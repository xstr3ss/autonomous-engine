import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from bug_resolution_store import BugResolutionStore
from docker_sandbox import CodeSandbox

# Load the secret API key from the .env file
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class SelfHealingEngine:
    def __init__(self):
        self.memory = BugResolutionStore()
        self.confidence_threshold = 0.85
        self.sandbox = CodeSandbox()
        
        # Initialize the Gemini model
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_real_patch(self, error_message: str) -> str:
        print("🧠 [LLM] Calling Gemini API to analyze error and write patch...")
        
        prompt = f"""
        You are an autonomous CI/CD debugging agent. 
        A Python test failed with the following error:
        {error_message}
        
        Write a Python function named `authenticate(user)` that fixes this.
        RULES:
        1. Return ONLY the raw Python code.
        2. Do NOT wrap the code in markdown formatting (no ```python).
        3. Do NOT include explanations.
        """
        
        response = self.model.generate_content(prompt)
        patch = response.text.strip()
        
        # Fallback: Strip markdown backticks just in case the LLM disobeys Rule 2
        patch = re.sub(r"^```python\n", "", patch)
        patch = re.sub(r"^```\n", "", patch)
        patch = re.sub(r"\n```$", "", patch)
        
        return patch.strip()

    def run_sandbox_tests(self, patch: str):
        print("🧪 [CI/CD] Forwarding patch to Docker Sandbox...")
        success, output = self.sandbox.test_patch(patch)
        
        if success:
            print(f"✅ [CI/CD] Container execution successful!\n   -> {output}")
            return True, 1.0
        else:
            print(f"❌ [CI/CD] Container execution failed!\n   -> {output}")
            return False, 0.0

    def resolve_error(self, error_message: str):
        print(f"\n🚨 [Engine] Detected pipeline failure: {error_message}")
        
        print("🔍 [Engine] Searching Qdrant memory for known fixes...")
        past_fixes = self.memory.search_similar_error(error_message, limit=1)
        
        if past_fixes and past_fixes[0]['score'] > self.confidence_threshold:
            best = past_fixes[0]
            print(f"💡 [Engine] Found matching fix in memory! (Confidence: {best['score']:.4f})")
            print("🔧 [Engine] Applying patch instantly.")
            return True

        if past_fixes:
            print(f"⚠️️ [Engine] No confident match found (Highest score: {past_fixes[0]['score']:.4f}).")
        
        # Calling the REAL LLM now
        new_patch = self.generate_real_patch(error_message)
        print(f"✍️  [Engine] Proposed Patch from Gemini:\n------------------\n{new_patch}\n------------------")
        
        success, score = self.run_sandbox_tests(new_patch)
        
        if success:
            print("💾 [Engine] Patch verified securely. Committing to vector memory...")
            self.memory.store_fix(error_message, new_patch, score)
            return True
        else:
            print("♻️ [Engine] Patch failed tests. Rolling back changes...")
            return False
            
    def shutdown(self):
        self.memory.close()

if __name__ == "__main__":
    engine = SelfHealingEngine()
    try:
        # We give it a brand new, unseen error about a completely different logic bug
        engine.resolve_error("AssertionError: authenticate('admin') should return True, but logic failed.")
    finally:
        engine.shutdown()
        print("\n🛑 [Engine] Offline.")
