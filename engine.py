from bug_resolution_store import BugResolutionStore

class SelfHealingEngine:
    def __init__(self):
        self.memory = BugResolutionStore()
        self.confidence_threshold = 0.70

    def mock_llm_generate_patch(self, error_message):
        print("🧠 [LLM] Analyzing error semantics and generating new code patch...")
        # In Phase 6, this will call a real LLM model
        if "auth_module.py" in error_message:
            return "def authenticate(user):\n    if not user:\n        return False\n    return True"
        return "pass # Fallback patch"

    def mock_run_tests(self, patch):
        print("🧪 [CI/CD] Running test suite against the new patch in sandbox...")
        # Simulate tests passing 100%
        print("✅ [CI/CD] All tests passed! Score: 1.0")
        return True, 1.0

    def resolve_error(self, error_message):
        print(f"\n🚨 [Engine] Detected pipeline failure: {error_message}")
        
        # 1. Check Vector Memory
        print("🔍 [Engine] Searching Qdrant memory for known fixes...")
        past_fixes = self.memory.search_similar_error(error_message, limit=1)
        
        if past_fixes and past_fixes[0]['score'] > self.confidence_threshold:
            best = past_fixes[0]
            print(f"💡 [Engine] Found matching fix in memory! (Confidence: {best['score']:.4f})")
            print(f"🔧 [Engine] Applying patch:\n{best['applied_patch']}")
            return True

        if past_fixes:
            print(f"⚠️ [Engine] No confident match found (Highest score: {past_fixes[0]['score']:.4f}).")
        
        # 2. Generate New Fix via LLM
        new_patch = self.mock_llm_generate_patch(error_message)
        print(f"✍️  [Engine] Proposed Patch:\n{new_patch}")
        
        # 3. Test & Verify
        success, score = self.mock_run_tests(new_patch)
        
        # 4. Save to Memory if Successful
        if success:
            print("💾 [Engine] Patch verified. Committing to vector memory for future use...")
            self.memory.store_fix(error_message, new_patch, score)
            return True
        else:
            print("❌ [Engine] Patch failed tests. Initiating rollback...")
            return False
            
    def shutdown(self):
        self.memory.close()

if __name__ == "__main__":
    engine = SelfHealingEngine()
    try:
        # First run: It won't find it in memory, will use LLM, and save it.
        print("\n--- FIRST PIPELINE RUN ---")
        engine.resolve_error("IndexError: list index out of range in auth_module.py")
        
        # Second run: It SHOULD find it in memory now!
        print("\n--- SECOND PIPELINE RUN (Simulating identical future failure) ---")
        engine.resolve_error("IndexError: list index out of range in auth_module.py")
    finally:
        engine.shutdown()
        print("\n🛑 [Engine] Offline.")
