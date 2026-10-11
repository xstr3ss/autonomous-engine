import re
import ast
from typing import List, Tuple, Optional, Any

class DiffEngine:
    DIFF_PATTERN = re.compile(
        r'<{5,9}\s*SEARCH\s*\n(.*?)\n={5,9}\s*\n(.*?)\n>{5,9}\s*REPLACE',
        re.DOTALL
    )
    
    # NEW: Regex to catch bash commands the AI wants to run
    BASH_PATTERN = re.compile(
        r'<{5,9}\s*BASH\s*\n(.*?)\n>{5,9}\s*EXECUTE',
        re.DOTALL
    )
    
    last_raw_response = ""

    @classmethod
    def parse_bash_blocks(cls, response_text: str) -> List[str]:
        """Extract terminal commands Fable wants to execute."""
        if not response_text: return []
        return [match.strip() for match in cls.BASH_PATTERN.findall(response_text)]

    @classmethod
    def parse_diff_blocks(cls, response_text: str) -> List[Tuple[str, str]]:
        if not response_text: return []
        cls.last_raw_response = response_text 
        
        matches = cls.DIFF_PATTERN.findall(response_text)
        blocks = [(search.strip(), replace.strip()) for search, replace in matches]
        
        if not blocks and cls.extract_ast_functions(response_text):
            return [("AST_SPLICE_TRIGGER", "AST_SPLICE_TRIGGER")]
            
        return blocks

    @classmethod
    def extract_ast_functions(cls, code_text: str) -> List[Tuple[str, str]]:
        cleaned = re.sub(r'```(?:python|PATCH|patch)?\n(.*?)```', r'\1', code_text, flags=re.DOTALL|re.IGNORECASE).strip()
        cleaned = re.sub(r'^PATCH\s*', '', cleaned).strip()
        try:
            tree = ast.parse(cleaned)
        except SyntaxError:
            return []
        
        functions = []
        lines = cleaned.splitlines()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno - 1
                end_line = node.end_lineno
                fn_source = "\n".join(lines[start_line:end_line])
                functions.append((node.name, fn_source))
        return functions

    @classmethod
    def apply_ast_splice(cls, target_file_content: str, fn_name: str, new_fn_code: str) -> Optional[str]:
        try:
            target_tree = ast.parse(target_file_content)
        except SyntaxError:
            return None
            
        target_lines = target_file_content.splitlines()
        for node in target_tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
                start_line = node.lineno - 1
                end_line = node.end_lineno
                updated_lines = target_lines[:start_line] + [new_fn_code] + target_lines[end_line:]
                return "\n".join(updated_lines) + "\n"
        return None

    @classmethod
    def apply_diff(cls, original_content: str, response_text: str) -> Tuple[bool, str]:
        blocks = cls.parse_diff_blocks(response_text)
        if blocks and blocks[0][0] != "AST_SPLICE_TRIGGER":
            modified = original_content
            for search_block, replace_block in blocks:
                if search_block not in modified:
                    return False, original_content
                modified = modified.replace(search_block, replace_block, 1)
            return True, modified

        extracted_functions = cls.extract_ast_functions(response_text)
        if extracted_functions:
            modified = original_content
            applied_any = False
            for fn_name, fn_code in extracted_functions:
                spliced = cls.apply_ast_splice(modified, fn_name, fn_code)
                if spliced:
                    modified = spliced
                    applied_any = True
            if applied_any:
                return True, modified

        return False, original_content

    @classmethod
    def patch_file(cls, filepath: str, blocks_or_text: Any = None) -> Tuple[bool, str]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original = f.read()
            
            raw_text = cls.last_raw_response if cls.last_raw_response else str(blocks_or_text)
            
            success, modified = cls.apply_diff(original, raw_text)
            if success:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified)
                return True, "File patched successfully."
            return False, "No valid syntax blocks found to patch."
        except Exception as e:
            return False, f"Exception: {e}"
