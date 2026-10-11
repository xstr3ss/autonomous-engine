import os
import requests
from rich.console import Console
from rich.panel import Panel
from engine import SelfHealingEngine
from orchestrator import InstitutionalOrchestrator
from dotenv import load_dotenv

load_dotenv()
console = Console()
engine = SelfHealingEngine()
groq_api_key = os.getenv("GROQ_API_KEY")

# Strict constants to prevent URL string corruption
URL_MODELS = "https://api.groq.com/openai/v1/models"
URL_CHAT = "https://api.groq.com/openai/v1/chat/completions"

def get_valid_model() -> str:
    if not groq_api_key:
        return "openai/gpt-oss-20b"
    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.get(URL_MODELS, headers=headers, timeout=10).json()
        models = [m["id"] for m in resp.get("data", [])]
        valid_models = [m for m in models if "guard" not in m.lower() and "whisper" not in m.lower() and "vision" not in m.lower() and "canopylabs" not in m.lower()]
        for target in ["gpt-oss-20b", "qwen3.8", "gpt-oss"]:
            for m in valid_models:
                if target in m.lower():
                    return m
        return valid_models[0] if valid_models else "openai/gpt-oss-20b"
    except Exception:
        return "openai/gpt-oss-20b"

ACTIVE_MODEL = get_valid_model()
planner = InstitutionalOrchestrator(model_name=ACTIVE_MODEL)

class AgenticOrchestrator:
    def __init__(self):
        self.memory = [
            {"role": "system", "content": "You are Fable, an institutional autonomous software and quantitative intelligence engine. Keep conversational replies clear and concise."}
        ]

    def route_intent(self, user_input: str) -> str:
        prompt = f"""Analyze input: "{user_input}"
Determine if this requires file modifications, code execution, or quantitative research.
Respond with exactly one word: ACTION or CHAT."""
        
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": ACTIVE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        try:
            resp = requests.post(URL_CHAT, headers=headers, json=payload, timeout=15).json()
            intent = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
            return "ACTION" if "ACTION" in intent else "CHAT"
        except Exception:
            return "CHAT"

    def conversational_reply(self, user_input: str) -> str:
        self.memory.append({"role": "user", "content": user_input})
        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": ACTIVE_MODEL,
            "messages": self.memory
        }
        try:
            resp = requests.post(URL_CHAT, headers=headers, json=payload, timeout=30).json()
            if "error" in resp:
                self.memory.pop()
                return f"API Error: {resp['error'].get('message', resp['error'])}"
            reply = resp["choices"][0]["message"]["content"]
            self.memory.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            self.memory.pop()
            return f"Error: {e}"

def run_chat():
    console.print(Panel(
        f"[bold white]FABLE ENTERPRISE ORCHESTRATOR[/]\n"
        f"[cyan]Active Brain:[/] {ACTIVE_MODEL}\n"
        f"[dim]AST Splicing: Enabled | Hierarchical Planning: Active[/]",
        border_style="cyan"
    ))

    orchestrator = AgenticOrchestrator()

    while True:
        try:
            user_input = console.input("\n[bold green]Shyam > [/]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break

            intent = orchestrator.route_intent(user_input)

            if intent == "ACTION":
                console.print("\n📋 [bold yellow]Decomposing objective into execution plan...[/]")
                plan = planner.generate_execution_plan(user_input)
                planner.display_plan(plan)

                console.print("\n⚙️ [bold yellow]Dispatching Worker Engine...[/]")
                engine.resolve_error(user_input)
                orchestrator.memory.append({
                    "role": "system",
                    "content": f"System log: Executed plan for task: '{user_input}'. Verification and Git commits recorded."
                })
            else:
                response = orchestrator.conversational_reply(user_input)
                console.print(f"\n🤖 [bold cyan]Fable >[/] {response}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Session terminated.[/]")
            break
        except Exception as e:
            console.print(f"\n❌ [bold red]Runtime Error: {e}[/]")

if __name__ == "__main__":
    run_chat()
