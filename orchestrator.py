import json
import os
import requests
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

load_dotenv()
console = Console()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class InstitutionalOrchestrator:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.model = model_name
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

    def generate_execution_plan(self, user_objective: str) -> List[Dict[str, Any]]:
        """Decomposes high-level instructions into concrete execution milestones."""
        prompt = f"""You are the Lead Quantitative Architect for an institutional trading engine.
Decompose this request into a structured execution plan (2 to 4 milestones max).

OBJECTIVE: "{user_objective}"

Return ONLY a valid JSON array of objects. Do not include markdown code fences or conversational text.
Format:
[
  {{"step": 1, "action": "RESEARCH", "target": "Identify required indicators and data requirements"}},
  {{"step": 2, "action": "MODIFY", "target": "strategy.py", "spec": "Implement indicator logic"}},
  {{"step": 3, "action": "VERIFY", "target": "test_strategy.py", "spec": "Validate syntax and performance"}}
]"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        try:
            res = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30).json()
            raw_text = res["choices"][0]["message"]["content"].strip()
            # Clean common markdown wrappers if returned
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            return json.loads(raw_text)
        except Exception:
            # Resilient fallback plan
            return [
                {"step": 1, "action": "MODIFY", "target": "strategy.py", "spec": user_objective},
                {"step": 2, "action": "VERIFY", "target": "test_strategy.py", "spec": "Run automated verification"}
            ]

    def display_plan(self, plan: List[Dict[str, Any]]) -> None:
        """Render institutional progress telemetry to the console."""
        plan_str = ""
        for item in plan:
            action = item.get('action', 'TASK')
            target = item.get('target', '')
            spec = item.get('spec', '')
            plan_str += f"[bold cyan]Step {item['step']}:[/] [{action}] [yellow]{target}[/] - [dim]{spec}[/]\n"
        
        console.print(Panel(plan_str.strip(), title="⚡ Autonomous Execution Plan", border_style="cyan"))
