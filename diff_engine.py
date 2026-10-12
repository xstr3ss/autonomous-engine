"""Fable DiffEngine: safe, structure-aware patching of source files from LLM output.

Understands three kinds of content in a model response:
  * BASH blocks            <<<<<<< BASH ... >>>>>>> EXECUTE
  * SEARCH/REPLACE blocks  <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE
  * Plain Python code      whole functions / classes (optionally in ``` fences),
                           spliced into the target file by AST position

Public API is unchanged: parse_bash_blocks, parse_diff_blocks, extract_ast_functions,
apply_ast_splice, apply_diff, patch_file, last_raw_response.
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import tempfile
import textwrap
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

_FENCE_RE = re.compile(r"```[\w+-]*[ \t]*\n(.*?)```", re.DOTALL)
_CODE_START_RE = re.compile(r"^(?:@|def |async def |class |import |from )", re.MULTILINE)
_FUNC = (ast.FunctionDef, ast.AsyncFunctionDef)
_IMPORT = (ast.Import, ast.ImportFrom)
_TRIGGER = "AST_SPLICE_TRIGGER"
_NO_BLOCKS = "No valid syntax blocks found to patch."


@dataclass(frozen=True)
class _Unit:
    kind: str                     # "func" | "class" | "method"
    name: str                     # "foo", "Cls" or "Cls.method"
    source: str                   # dedented source, decorators included
    owner: Optional[str] = None   # class name, for methods


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _node_span(node: ast.AST) -> Tuple[int, int]:
    """0-based [start, end) line span of a node, decorators included."""
    decorators = getattr(node, "decorator_list", [])
    start = min([node.lineno] + [d.lineno for d in decorators])
    return start - 1, node.end_lineno


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _reindent(src: str, indent: str) -> List[str]:
    return [(indent + line) if line.strip() else "" for line in textwrap.dedent(src).split("\n")]


def _node_source(lines: List[str], node: ast.AST) -> str:
    """Source of a node with its own indentation (col_offset) removed."""
    start, end = _node_span(node)
    col = node.col_offset
    chunk = lines[start:end]
    return "\n".join(l[col:] if not l[:col].strip() else l for l in chunk)


class DiffEngine:
    DIFF_PATTERN = re.compile(
        r"<{5,9}\s*SEARCH\s*\n(.*?)\n={5,9}\s*\n(.*?)\n>{5,9}\s*REPLACE",
        re.DOTALL,
    )

    # Regex to catch bash commands the AI wants to run
    BASH_PATTERN = re.compile(
        r"<{5,9}\s*BASH\s*\n(.*?)\n>{5,9}\s*EXECUTE",
        re.DOTALL,
    )

    # Kept for backward compatibility. Patching never depends on it any more
    # (it used to override the text passed to patch_file, which broke multi-file runs).
    last_raw_response = ""

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #
    @classmethod
    def parse_bash_blocks(cls, response_text: str) -> List[str]:
        """Extract terminal commands Fable wants to execute."""
        if not response_text:
            return []
        text = response_text.replace("\r\n", "\n")
        return [m.strip() for m in cls.BASH_PATTERN.findall(text) if m.strip()]

    @classmethod
    def _raw_blocks(cls, text: str) -> List[Tuple[str, str]]:
        """SEARCH/REPLACE pairs with indentation intact."""
        if not text:
            return []
        return cls.DIFF_PATTERN.findall(text.replace("\r\n", "\n"))

    @classmethod
    def parse_diff_blocks(cls, response_text: str) -> List[Tuple[str, str]]:
        if not response_text:
            return []
        cls.last_raw_response = response_text

        blocks = [(s.strip(), r.strip()) for s, r in cls._raw_blocks(response_text)]
        if not blocks and cls.extract_ast_functions(response_text):
            return [(_TRIGGER, _TRIGGER)]
        return blocks

    @classmethod
    def _snippets(cls, text: str) -> List[str]:
        """Candidate code snippets: every fenced block, or the whole text if unfenced."""
        text = (text or "").replace("\r\n", "\n")
        blocks = [b for b in _FENCE_RE.findall(text) if b.strip()] or [text]
        out = []
        for block in blocks:
            block = re.sub(r"\A\s*PATCH[ \t]*\n", "", block)
            out.append(textwrap.dedent(block).strip("\n"))
        return out

    @staticmethod
    def _parse_code(code: str) -> Optional[Tuple[ast.Module, List[str]]]:
        try:
            return ast.parse(code), code.split("\n")
        except SyntaxError:
            pass
        # Unfenced reply with prose in front ("Here is the fix:\ndef ..."): start at the first code line.
        m = _CODE_START_RE.search(code)
        if m and m.start() > 0:
            code = code[m.start():]
            try:
                return ast.parse(code), code.split("\n")
            except SyntaxError:
                return None
        return None

    @classmethod
    def _extract(cls, text: str) -> Tuple[List[Tuple[str, str]], List[_Unit]]:
        """Return (imports, units) found in the code of a response.

        imports: [(ast_key, source)]; units: functions, classes and class methods.
        """
        imports: List[Tuple[str, str]] = []
        units: List[_Unit] = []
        for code in cls._snippets(text):
            parsed = cls._parse_code(code)
            if not parsed:
                continue
            tree, lines = parsed
            for node in tree.body:
                if isinstance(node, _IMPORT):
                    imports.append((ast.dump(node), _node_source(lines, node)))
                elif isinstance(node, _FUNC):
                    units.append(_Unit("func", node.name, _node_source(lines, node)))
                elif isinstance(node, ast.ClassDef):
                    units.append(_Unit("class", node.name, _node_source(lines, node)))
                    for sub in node.body:
                        if isinstance(sub, _FUNC):
                            units.append(_Unit("method", f"{node.name}.{sub.name}",
                                               _node_source(lines, sub), owner=node.name))
        return imports, units

    @classmethod
    def extract_ast_functions(cls, code_text: str) -> List[Tuple[str, str]]:
        """[(name, source)] for each function; class methods are named 'Class.method'."""
        _, units = cls._extract(code_text)
        return [(u.name, u.source) for u in units if u.kind in ("func", "method")]

    # ------------------------------------------------------------------ #
    # AST splicing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parses(src: str) -> bool:
        try:
            ast.parse(src)
            return True
        except (SyntaxError, ValueError):
            return False

    @staticmethod
    def _insert_top_level(lines: List[str], tree: ast.Module, new_lines: List[str]) -> List[str]:
        """Add code at the end of the module, but above a trailing `if __name__ == ...` guard."""
        main = next(
            (n for n in tree.body
             if isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
             and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"),
            None,
        )
        at = _node_span(main)[0] if main else len(lines)
        head, tail = lines[:at], lines[at:]
        while head and not head[-1].strip():
            head.pop()
        out = head + (["", ""] if head else []) + new_lines
        if main:
            out += ["", ""] + tail
        return out

    @classmethod
    def apply_ast_splice(cls, target_file_content: str, fn_name: str, new_fn_code: str) -> Optional[str]:
        """Replace function `fn_name` ('name' or 'Class.name') in the target, or add it if missing.

        Returns the new file content, or None if it cannot be done safely
        (target not valid Python, class not found, or the result would not parse).
        """
        content = target_file_content.replace("\r\n", "\n")
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return None

        lines = content.split("\n")  # not splitlines(): it breaks on chars ast does not count
        owner, _, leaf = fn_name.rpartition(".")
        class_node = None
        scope = tree.body
        if owner:
            class_node = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == owner), None)
            if class_node is None:
                return None
            scope = class_node.body

        node = next((n for n in scope if isinstance(n, _FUNC) and n.name == leaf), None)
        if node is not None:
            start, end = _node_span(node)
            lines[start:end] = _reindent(new_fn_code, _indent_of(lines[start]))
        elif class_node is not None:
            indent = _indent_of(lines[class_node.body[0].lineno - 1])
            lines[class_node.end_lineno:class_node.end_lineno] = [""] + _reindent(new_fn_code, indent)
        else:
            lines = cls._insert_top_level(lines, tree, _reindent(new_fn_code, ""))

        result = "\n".join(lines)
        if not result.endswith("\n"):
            result += "\n"
        return result if cls._parses(result) else None

    @classmethod
    def _add_imports(cls, content: str, imports: List[Tuple[str, str]]) -> str:
        """Add imports the new code needs that the file does not already have."""
        if not imports:
            return content
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return content

        seen = {ast.dump(n) for n in tree.body if isinstance(n, _IMPORT)}
        missing = []
        for key, src in imports:
            if key not in seen:
                seen.add(key)
                missing.append(src)
        if not missing:
            return content

        last_import = max((n.end_lineno for n in tree.body if isinstance(n, _IMPORT)), default=None)
        new_lines = [line for src in missing for line in src.split("\n")]
        if last_import is not None:
            at = last_import
        else:
            first = tree.body[0] if tree.body else None
            is_docstring = (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                            and isinstance(first.value.value, str))
            at = first.end_lineno if is_docstring else 0
            new_lines = ([""] if at else []) + new_lines + [""]

        lines = content.split("\n")
        lines[at:at] = new_lines
        result = "\n".join(lines)
        return result if cls._parses(result) else content

    # ------------------------------------------------------------------ #
    # SEARCH/REPLACE
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fuzzy_replace(content: str, search: str, replace: str) -> Optional[str]:
        """Whitespace-tolerant match (ignores indentation); must match exactly one place."""
        s_lines = search.split("\n")
        while s_lines and not s_lines[0].strip():
            s_lines.pop(0)
        while s_lines and not s_lines[-1].strip():
            s_lines.pop()
        if not s_lines:
            return None

        c_lines = content.split("\n")
        c_strip = [l.strip() for l in c_lines]
        key = [l.strip() for l in s_lines]
        n = len(key)
        hits = [i for i in range(len(c_lines) - n + 1) if c_strip[i:i + n] == key]
        if len(hits) != 1:
            return None

        i = hits[0]
        old_indent, new_indent = _indent_of(c_lines[i]), _indent_of(s_lines[0])
        out = []
        for line in (replace.split("\n") if replace.strip() else []):
            if line.strip() and line.startswith(new_indent):
                out.append(old_indent + line[len(new_indent):])
            else:
                out.append(line)
        c_lines[i:i + n] = out
        return "\n".join(c_lines)

    @classmethod
    def _replace_block(cls, content: str, search: str, replace: str) -> Optional[str]:
        if not search.strip():
            return None
        if search in content:                                           # 1. exact
            return content.replace(search, replace, 1)
        s, r = search.strip(), replace.strip()
        if s in content:                                                # 2. ignoring outer whitespace
            return content.replace(s, r, 1)
        return cls._fuzzy_replace(content, search, replace)     # 3. ignoring indentation

    # ------------------------------------------------------------------ #
    # Applying
    # ------------------------------------------------------------------ #
    @classmethod
    def _apply(cls, original: str, payload: Any) -> Tuple[bool, str, str]:
        """Core: returns (ok, new_content, reason). `payload` is response text or a list of blocks."""
        if isinstance(payload, (list, tuple)):
            real = [b for b in payload if b and b[0] != _TRIGGER]
            if real:
                blocks, text = [(s, r) for s, r in real], ""
            else:  # only the AST trigger was passed: fall back to the last parsed response
                blocks, text = [], cls.last_raw_response
        else:
            text = payload or ""
            blocks = cls._raw_blocks(text)

        if blocks:
            modified = original
            for i, (search, replace) in enumerate(blocks, 1):
                new = cls._replace_block(modified, search, replace)
                if new is None:
                    return False, original, f"SEARCH block {i} was not found in the file."
                modified = new
            return True, modified, "ok"

        imports, units = cls._extract(text)
        if not units:
            return False, original, _NO_BLOCKS

        modified, applied, added_classes = original, False, set()
        for u in units:
            if u.kind == "class":
                has_class = any(isinstance(n, ast.ClassDef) and n.name == u.name
                                for n in cls._safe_body(modified))
                if has_class:
                    continue
                try:
                    tree = ast.parse(modified)
                except SyntaxError:
                    continue
                lines = cls._insert_top_level(modified.split("\n"), tree, _reindent(u.source, ""))
                candidate = "\n".join(lines)
                candidate += "" if candidate.endswith("\n") else "\n"
                if cls._parses(candidate):
                    modified, applied = candidate, True
                    added_classes.add(u.name)
            elif u.kind == "method" and u.owner in added_classes:
                continue  # came with the whole class
            else:
                new = cls.apply_ast_splice(modified, u.name, u.source)
                if new is not None:
                    modified, applied = new, True

        if not applied:
            return False, original, "Could not splice any function into the file."
        return True, cls._add_imports(modified, imports), "ok"

    @staticmethod
    def _safe_body(src: str) -> List[ast.stmt]:
        try:
            return ast.parse(src).body
        except SyntaxError:
            return []

    @classmethod
    def apply_diff(cls, original_content: str, response_text: str) -> Tuple[bool, str]:
        ok, modified, _ = cls._apply(original_content.replace("\r\n", "\n"), response_text)
        return (True, modified) if ok else (False, original_content)

    # ------------------------------------------------------------------ #
    # File I/O
    # ------------------------------------------------------------------ #
    @staticmethod
    def _atomic_write(path: str, content: str) -> None:
        path = os.path.realpath(path)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".diff-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            shutil.copymode(path, tmp)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    @classmethod
    def patch_file(cls, filepath: str, blocks_or_text: Any = None) -> Tuple[bool, str]:
        """Patch `filepath` using the response text (or parsed blocks) passed in.

        With no argument, falls back to the last response seen by parse_diff_blocks.
        The write is atomic, preserves line endings and file mode, and a patch that would
        turn valid Python into invalid Python is rejected.
        """
        try:
            with open(filepath, "r", encoding="utf-8", newline="") as f:
                raw = f.read()
            crlf = "\r\n" in raw
            original = raw.replace("\r\n", "\n")

            if blocks_or_text is None:
                payload: Any = cls.last_raw_response
            elif isinstance(blocks_or_text, (list, tuple)):
                payload = list(blocks_or_text)
            else:
                payload = str(blocks_or_text)

            ok, modified, reason = cls._apply(original, payload)
            if not ok:
                return False, reason
            if modified == original:
                return True, "File already up to date."
            if filepath.endswith(".py") and cls._parses(original) and not cls._parses(modified):
                return False, "Patch rejected: it would leave the file with a syntax error."

            cls._atomic_write(filepath, modified.replace("\n", "\r\n") if crlf else modified)
            return True, "File patched successfully."
        except Exception as e:
            return False, f"Exception: {e}"
