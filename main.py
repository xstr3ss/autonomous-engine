from bug_resolution_store import BugResolutionStore

def run_agent():
    print("🤖 [Agent] Booting up memory modules...")
    memory = BugResolutionStore()

    try:
        # Simulate the agent encountering a broken piece of code
        current_error = "IndexError: list index out of range in auth_module.py"
        print(f"\n🚨 [Agent] Code execution failed! Error captured:")
        print(f"   -> {current_error}")
        
        print("\n🔍 [Agent] Querying vector database for past solutions...")
        
        # Search memory for the top 1 most similar error
        past_fixes = memory.search_similar_error(current_error, limit=1)
        
        # Check if we have a match and if the confidence is high enough (> 0.70)
        if past_fixes and past_fixes[0]['score'] > 0.70:
            best_fix = past_fixes[0]
            print(f"\n💡 [Agent] Found highly relevant past fix! (Confidence: {best_fix['score']:.4f})")
            print(f"   Original error it fixed: {best_fix['error_message']}")
            print(f"\n🔧 [Agent] Automatically applying patch...")
            print("-------------------------------------------------")
            print(best_fix['applied_patch'])
            print("-------------------------------------------------")
            print("✅ [Agent] Patch applied successfully.")
        else:
            print("\n🧠 [Agent] No high-confidence fix found in memory.")
            print("   (In Phase 4, the LLM will generate a new fix here and save it).")
            
    finally:
        memory.close()
        print("\n🛑 [Agent] Shutting down cleanly.")

if __name__ == "__main__":
    run_agent()
