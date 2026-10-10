import os
import ast
import logging
from typing import Dict, List, Optional, Union
from tree_sitter import Language, Parser, Node
import tree_sitter_python as tspython

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("Tier0-Parser")

class Tier0Parser:
    """
    Tier 0 Deterministic AST Parser using Tree-Sitter and Python AST.
    Generates token-starved repo skeletons and extracts target function bytes.
    """
    def __init__(self, root_dir: str = ".") -> None:
        self.root_dir = root_dir
        self.language: Language = Language(tspython.language())
        self.parser: Parser = Parser(self.language)

    def _read_file_bytes(self, filepath: str) -> bytes:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        with open(filepath, "rb") as f:
            return f.read()

    def generate_skeletal_map(self, filepath: str) -> str:
        """
        Parses a file and emits only class/function signatures, stripping bodies.
        """
        source_bytes = self._read_file_bytes(filepath)
        tree = self.parser.parse(source_bytes)
        skeleton_lines: List[str] = []

        def traverse(node: Node, indent_level: int = 0) -> None:
            indent = "    " * indent_level
            if node.type == "class_definition":
                block_node = self._get_child_by_type(node, "block")
                if block_node:
                    sig = source_bytes[node.start_byte:block_node.start_byte].decode("utf-8").strip()
                    skeleton_lines.append(f"{indent}{sig} ...")
                    for child in block_node.children:
                        traverse(child, indent_level + 1)
                else:
                    name = self._get_node_identifier(node)
                    skeleton_lines.append(f"{indent}class {name}: ...")
            elif node.type == "function_definition":
                block_node = self._get_child_by_type(node, "block")
                if block_node:
                    sig = source_bytes[node.start_byte:block_node.start_byte].decode("utf-8").strip()
                    skeleton_lines.append(f"{indent}{sig} ...")
                else:
                    name = self._get_node_identifier(node)
                    skeleton_lines.append(f"{indent}def {name}(...): ...")
            else:
                if node.type not in ["function_definition", "class_definition"]:
                    for child in node.children:
                        traverse(child, indent_level)

        traverse(tree.root_node)
        return "\n".join(skeleton_lines)

    def extract_function(self, filepath: str, function_name: str) -> Dict[str, Union[str, int]]:
        """
        Extracts exact source code and byte indices of a specific function.
        """
        source_bytes = self._read_file_bytes(filepath)
        tree = self.parser.parse(source_bytes)
        target_node: Optional[Node] = None

        def search(node: Node) -> None:
            nonlocal target_node
            if target_node:
                return
            if node.type == "function_definition":
                if self._get_node_identifier(node) == function_name:
                    target_node = node
                    return
            for child in node.children:
                search(child)

        search(tree.root_node)
        if not target_node:
            raise ValueError(f"Function '{function_name}' not found in {filepath}")

        return {
            "name": function_name,
            "content": source_bytes[target_node.start_byte:target_node.end_byte].decode("utf-8"),
            "start_byte": target_node.start_byte,
            "end_byte": target_node.end_byte
        }

    def find_local_dependencies(self, filepath: str) -> List[str]:
        """
        Uses native AST to deterministically trace imports one level deep.
        """
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except Exception:
            return []
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                cand = os.path.join(self.root_dir, f"{node.module}.py")
                if os.path.exists(cand):
                    deps.add(f"{node.module}.py")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    cand = os.path.join(self.root_dir, f"{alias.name}.py")
                    if os.path.exists(cand):
                        deps.add(f"{alias.name}.py")
        return list(deps)

    def _get_child_by_type(self, node: Node, child_type: str) -> Optional[Node]:
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_node_identifier(self, node: Node) -> str:
        ident = self._get_child_by_type(node, "identifier")
        if ident and ident.text:
            return ident.text.decode("utf-8")
        return "unknown"
