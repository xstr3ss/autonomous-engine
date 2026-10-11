from __future__ import annotations
import re

# --------------------------------------------------------------------------- #
# Response parsing
# --------------------------------------------------------------------------- #
BASH_BLOCK_RE = re.compile(r"<{3,}\s*BASH.*?>{3,}\s*EXECUTE", re.DOTALL | re.IGNORECASE)
FILE_RE = re.compile(
    r"^\s*(?:#+\s*|\*{1,2})?\s*FILE:\s*[`'\"]*(.+?)[`'\"]*\s*(?:\*{1,2})?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
FENCE_RE = re.compile(r"```[\w+-]*[ \t]*\n(.*?)```", re.DOTALL)

# Commands an LLM should never be allowed to run unattended.
BLOCKED_COMMANDS = re.compile(
    r"(\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\*|\.\.)"
    r"|\bsudo\b|\bmkfs\b|\bdd\s+if="
    r"|:\(\)\s*\{"
    r"|\b(curl|wget)\b[^|;]*\|\s*(ba|z)?sh\b"
    r"|>\s*/dev/sd|\bshutdown\b|\breboot\b|\bchmod\s+-R\s+777\s+/)",
    re.IGNORECASE,
)

def parse_file_blocks(response_text: str) -> list[tuple[str, str]]:
    """Return [(filename, body)] for every FILE: section (BASH blocks excluded)."""
    text = BASH_BLOCK_RE.sub("", response_text)
    matches = list(FILE_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        name = m.group(1).strip().strip("`'\"*#")
        if name:
            blocks.append((name, text[m.end():end]))
    return blocks

def extract_code(body: str) -> str:
    """Extract code cleanly from fences, stripping leading introductory text."""
    fences = FENCE_RE.findall(body)
    if fences:
        return fences[0].strip() + "\n"
    lines = body.splitlines()
    code_lines = []
    started = False
    for line in lines:
        if line.strip().startswith(("import ", "from ", "def ", "class ", "@", "if ", "#")):
            started = True
        if started:
            code_lines.append(line)
    return ("\n".join(code_lines) if code_lines else body).strip() + "\n"
