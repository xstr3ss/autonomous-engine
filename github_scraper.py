import requests
import json
import os
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

load_dotenv()
CHECKPOINT_FILE = "scraper_checkpoint.json"

DEFAULT_REPOS = [
    "psf/requests",
    "pallets/flask",
    "urllib3/urllib3",
    "pallets/click",
    "bottlepy/bottle"
]

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {
        "repos": DEFAULT_REPOS,
        "current_repo_idx": 0,
        "current_page": 1
    }

def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)

def scrape_and_store():
    state = load_checkpoint()
    q_client = QdrantClient(path="./qdrant_data")
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.getenv('GITHUB_TOKEN')}"
        
    repos = state.get("repos", DEFAULT_REPOS)
    
    print("🚀 [Scraper] Continuous extraction initialized. Trusting merged PRs...")
    
    while state["current_repo_idx"] < len(repos):
        repo = repos[state["current_repo_idx"]]
        page = state["current_page"]
        
        print(f"\n📡 [Scraper] Fetching {repo} (Page {page})...")
        url = f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page=50&page={page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code in [403, 429]:
            print("⚠️ [Scraper] Rate limit hit. Checkpoint saved. Run again later to resume.")
            break
            
        if response.status_code != 200:
            state["current_repo_idx"] += 1
            state["current_page"] = 1
            save_checkpoint(state)
            continue
            
        prs = response.json()
        if not prs:
            print(f"✅ [Scraper] Reached end of PRs for {repo}.")
            state["current_repo_idx"] += 1
            state["current_page"] = 1
            save_checkpoint(state)
            continue
            
        for pr in prs:
            # Only process successfully merged pull requests
            if not pr.get("body") or not pr.get("merged_at"):
                continue
            
            error_sig = f"{pr.get('title', '')}\n{pr.get('body', '')[:300]}"
            patch_resp = requests.get(pr["patch_url"], headers=headers)
            
            if patch_resp.status_code == 200:
                patch_text = patch_resp.text[:1500]
                
                print(f"✅ [Memory] PR #{pr['number']} verified by origin repo. Injecting into Qdrant...")
                q_client.upsert(
                    collection_name="bug_fixes",
                    points=[
                        PointStruct(
                            id=uuid.uuid4().hex,
                            vector=[0.0] * 384,
                            payload={
                                "error_signature": error_sig,
                                "patch": patch_text
                            }
                        )
                    ]
                )

        state["current_page"] += 1
        save_checkpoint(state)

    q_client.close()
    print("\n🛑 [Scraper] Run complete or paused. Checkpoint updated.")

if __name__ == "__main__":
    scrape_and_store()
