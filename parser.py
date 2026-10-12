import re
import os
import logging

log = logging.getLogger("fable.parser")

def apply_patch(text: str) -> dict:
    """Parses LLM SEARCH/REPLACE blocks with forgiving regex for missing blank lines."""
    # 🚨 THE FIX: Removed the strict \n requirements between the blocks
    pattern = re.compile(
        r"FILE:\s*([^\n]+)\n<<<< SEARCH\n(.*?)==== REPLACE\n(.*?)>>>>",
        re.DOTALL
    )
    matches = pattern.findall(text)
    
    written_files = {}
    for file_path, search_block, replace_block in matches:
        file_path = file_path.strip()
        
        # Clean up the trailing newline captured by DOTALL right before the markers
        if search_block.endswith('\n'): search_block = search_block[:-1]
        if replace_block.endswith('\n'): replace_block = replace_block[:-1]
        
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        
        # Scenario A: New file creation
        if not os.path.exists(file_path) or not search_block.strip():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(replace_block)
            written_files[file_path] = replace_block
            log.info(f"✨ [Patcher] Created new file: {file_path}")
            continue
            
        # Scenario B: Surgical AST/Diff Patching
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if search_block in content:
            new_content = content.replace(search_block, replace_block, 1)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            written_files[file_path] = new_content
            log.info(f"✂️ [Patcher] Surgically patched: {file_path}")
        else:
            log.error(f"❌ [Patcher] SEARCH block not found in {file_path}. Hallucinated code.")
            raise ValueError("Patch failed: SEARCH block mismatch.")
            
    return written_files
