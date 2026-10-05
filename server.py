from fastapi import FastAPI
from pydantic import BaseModel
from engine import SelfHealingEngine
import uvicorn

app = FastAPI(title="Autonomous Engine Webhook Listener")
engine = SelfHealingEngine()

# This defines the exact shape of the data we expect from GitHub
class WebhookPayload(BaseModel):
    repository: str
    error_log: str
    pr_number: int

@app.post("/webhook")
async def github_webhook(payload: WebhookPayload):
    print(f"\n📡 [Server] Webhook received! PR #{payload.pr_number} on {payload.repository}")
    
    # 1. Feed the error from the webhook directly into our Self-Healing Engine
    success = engine.resolve_error(payload.error_log)
    
    # 2. Respond back to GitHub (In the future, this would post a PR comment)
    if success:
        print("✅ [Server] Responding to GitHub: Fix successful.")
        return {"status": "success", "message": "Engine generated and verified a patch."}
    else:
        print("❌ [Server] Responding to GitHub: Fix failed.")
        return {"status": "failed", "message": "Engine could not resolve the error."}

@app.on_event("shutdown")
def shutdown_event():
    engine.shutdown()
    print("🛑 [Server] Engine memory safely closed.")

if __name__ == "__main__":
    print("🚀 Starting GitHub Webhook Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
