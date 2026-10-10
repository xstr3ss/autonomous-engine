import re
from typing import Tuple, List, Dict

class DiffEngine:
    DIFF_PATTERN = re.compile(
        r'<<<<<<< SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>> REPLACE',
        re.DOTALL
    )

    @classmethod
    def parse_diff_blocks(cls, response_text: str) -> List[Dict[str, str]]:
        matches = cls.DIFF_PATTERN.findall(response_text)
        if not matches:
            print("\n⚠️ [Diff Debug] NO VALID BLOCKS FOUND. RAW AI OUTPUT:\n" + response_text + "\n")
        blocks = []
        for search_block, replace_block in matches:
            blocks.append({
                "search": search_block,
                "replace": replace_block
            })
        return blocks

    @classmethod
    def apply_diff_to_content(cls, original_content: str, search_block: str, replace_block: str) -> Tuple[bool, str]:
        # 1. Exact match attempt
        if search_block in original_content:
            return True, original_content.replace(search_block, replace_block, 1)

        # 2. Normalized newline match attempt
        norm_orig = original_content.replace("\r\n", "\n")
        norm_search = search_block.replace("\r\n", "\n")
        norm_replace = replace_block.replace("\r\n", "\n")

        if norm_search in norm_orig:
            return True, norm_orig.replace(norm_search, norm_replace, 1)

        # 3. Strip leading/trailing empty lines match attempt
        stripped_search = norm_search.strip()
        if stripped_search and stripped_search in norm_orig:
            return True, norm_orig.replace(stripped_search, norm_replace.strip(), 1)
            
        # If all matches fail, print exactly what the AI tried to match
        print("\n⚠️ [Diff Debug] MISMATCH DETECTED.")
        print("--- AI SEARCH BLOCK ---")
        print(search_block)
        print("--- ACTUAL FILE CONTENT ---")
        print(original_content)
        print("-----------------------\n")

        return False, "Target SEARCH block not found in source file."

    @classmethod
    def patch_file(cls, filepath: str, diff_blocks: List[Dict[str, str]]) -> Tuple[bool, str]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return False, f"Failed to read {filepath}: {e}"

        current_content = content
        for idx, block in enumerate(diff_blocks):
            success, result = cls.apply_diff_to_content(
                current_content, 
                block["search"], 
                block["replace"]
            )
            if not success:
                return False, f"Block {idx + 1} failed: Target SEARCH block not found."
            current_content = result

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(current_content)
            return True, f"Successfully applied diff."
        except Exception as e:
            return False, f"Failed to write to {filepath}: {e}"
