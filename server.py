import logging
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Request
from engine import SelfHealingEngine

logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
log = logging.getLogger("fable.server")

app = FastAPI(title="Fable Autonomous CI/CD Engine")
engine = SelfHealingEngine()

def dispatch_worker(prompt: str):
    """Runs the Fable TDD loop in the background."""
    log.info(f"🚀 [Webhook] Autonomous loop triggered with prompt:\n{prompt}")
    try:
        engine.run(prompt)
        log.info("✅ [Webhook] Fable worker completed execution.")
    except Exception as e:
        log.error(f"❌ [Webhook] Fable worker crashed: {e}")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Listens for GitHub/GitLab webhook payloads.
    Triggers the self-healing loop when a new issue is opened or a build fails.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON payload"}

    # --- Scenario A: A new GitHub Issue is opened ---
    if "issue" in payload and payload.get("action") == "opened":
        title = payload["issue"].get("title", "No Title")
        body = payload["issue"].get("body", "No Description")
        
        # Formulate the prompt for the engine
        prompt = f"Fix this GitHub Issue: {title}\nDetails: {body}"
        
        # Dispatch to background so GitHub doesn't timeout waiting for the AI
        background_tasks.add_task(dispatch_worker, prompt)
        return {"status": "accepted", "message": f"Fable dispatched for issue: {title}"}

    # --- Scenario B: A CI/CD pipeline pushes a failure (Mock logic) ---
    elif "commits" in payload:
        commit_msg = payload["commits"][0].get("message", "Unknown commit")
        prompt = f"Implement the requirements from this commit push: {commit_msg}"
        
        background_tasks.add_task(dispatch_worker, prompt)
        return {"status": "accepted", "message": "Fable dispatched for commit event."}

    return {"status": "ignored", "message": "Unhandled webhook event type."}

@app.get("/health")
def health_check():
    return {"status": "online", "agent": "Fable Core Controller"}

if __name__ == "__main__":
    log.info("🌐 Booting Fable Webhook Listener on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
