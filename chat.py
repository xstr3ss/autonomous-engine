import os
import requests
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
console = Console()
groq_api_key = os.getenv("GROQ_API_KEY")

URL_MODELS = "https://api.groq.com/openai/v1/models"
URL_CHAT = "https://api.groq.com/openai/v1/chat/completions"

def get_valid_model() -> str:
    if not groq_api_key:
        return "llama-3.3-70b-versatile"
    try:
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.get(URL_MODELS, headers=headers, timeout=10).json()
        models = [m["id"] for m in resp.get("data", [])]
        valid_models = [m for m in models if "guard" not in m.lower() and "whisper" not in m.lower() and "vision" not in m.lower()]

        # Safely fall back to guaranteed models
        for target in ["llama-3.3-70b", "llama-3.1-8b"]:
            for m in valid_models:
                if target in m.lower():
                    return m
        return valid_models[0] if valid_models else "llama-3.3-70b-versatile"
    except Exception:
        return "llama-3.3-70b-versatile"

class AgenticOrchestrator:
    def __init__(self, model_name):
        self.model = model_name
        self.memory = [
            {"role": "system", "content": "You are Fable, an institutional autonomous software engine. Keep conversational replies clear and concise."}
        ]

    def route_intent(self, user_input: str) -> str:
        prompt = f"""Analyze input: "{user_input}"
Determine if this requires file modifications, code execution, or project generation.
Respond with exactly one word: ACTION or CHAT."""

        headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
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
            "model": self.model,
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
    console.print("\n[bold yellow]⚡ Booting Fable OS...[/]")

    console.print("[cyan]1. Discovering Groq API Models...[/]")
    ACTIVE_MODEL = get_valid_model()
    os.environ["FABLE_CLOUD_MODEL"] = ACTIVE_MODEL

    console.print("[cyan]2. Loading Autonomous Worker Engine (Qdrant & AST)...[/]")
    from engine import SelfHealingEngine
    from orchestrator import InstitutionalOrchestrator

    engine = SelfHealingEngine()
    planner = InstitutionalOrchestrator(model_name=ACTIVE_MODEL)
    orchestrator = AgenticOrchestrator(model_name=ACTIVE_MODEL)

    console.print(Panel(
        f"[bold white]FABLE ENTERPRISE ORCHESTRATOR[/]\n"
        f"[cyan]Active Brain:[/] {ACTIVE_MODEL}\n"
        f"[dim]AST Splicing: Enabled | Hierarchical Planning: Active[/]",
        border_style="cyan"
    ))

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
                engine.run(user_input)
                orchestrator.memory.append({
                    "role": "system",
                    "content": f"System log: Executed task: '{user_input}'."
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
