import os
import uuid
from github import Github
from github.GithubException import GithubException
from dotenv import load_dotenv

load_dotenv()

class GitHubManager:
    def __init__(self, repo_name: str):
        token = os.getenv("GITHUB_PAT")
        if not token:
            raise ValueError("❌ [GitHub] ERROR: GITHUB_PAT missing from .env")
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)

    def create_pull_request(self, updated_files: dict, commit_message: str):
        print(f"🌿 [GitHub] Preparing to branch code for {len(updated_files)} files...")
        
        branch_name = f"fix/auto-patch-{uuid.uuid4().hex[:8]}"
        main_branch = self.repo.get_branch(self.repo.default_branch)
        self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
        
        for file_path, new_content in updated_files.items():
            print(f"📝 [GitHub] Committing changes to {file_path}...")
            try:
                file = self.repo.get_contents(file_path, ref=branch_name)
                self.repo.update_file(
                    path=file.path,
                    message=f"Update {file_path}",
                    content=new_content,
                    sha=file.sha,
                    branch=branch_name
                )
            except GithubException:
                self.repo.create_file(
                    path=file_path,
                    message=f"Create {file_path}",
                    content=new_content,
                    branch=branch_name
                )
        
        try:
            pr = self.repo.create_pull(
                title=f"🤖 Auto-Fix: {commit_message}",
                body="### 🛠️ Autonomous Self-Healing Engine\n\nThis PR modifies multiple files to resolve a CI/CD failure.\n\n- **Status:** ✅ Verified locally.\n- **Action:** Ready for human review.",
                head=branch_name,
                base=self.repo.default_branch
            )
            print(f"🚀 [GitHub] Multi-file PR successfully opened!\n   -> URL: {pr.html_url}")
            return pr.html_url
        except GithubException as e:
            print(f"⚠️ [GitHub] Branch pushed, but PR rejected (Likely no diff from main): {e.data.get('message', str(e))}")
            return f"https://github.com/{self.repo.full_name}/tree/{branch_name}"
