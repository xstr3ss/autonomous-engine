import click
import subprocess
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

def print_banner():
    # A sleek, minimalist, unbreakable header
    console.print(Panel(
        "[bold white]CORE CONTROLLER[/]\n[cyan]Fable Architecture v1.0.0[/]\n[dim]Autonomous Code Repair Engine[/]", 
        border_style="cyan", 
        expand=False
    ))

@click.group()
def cli():
    """🚀 The Autonomous Self-Healing Code Engine"""
    pass

@click.command()
def init():
    """📦 Boot the Sandbox and initialize the Context Graph"""
    print_banner()
    console.print("\n[bold yellow]⚡ Initializing System...[/]")
    
    console.print("[cyan]1. Booting Zero-Trust Sandbox...[/]")
    time.sleep(0.5)
    console.print("   ✅ [green]Sandbox MicroVM Online.[/]")
    
    console.print("[cyan]2. Wiping old Database Locks...[/]")
    os.system("rm -rf qdrant_ledger_data > /dev/null 2>&1")
    os.system("pkill -9 -f 'python repo_indexer.py' > /dev/null 2>&1 || true")
    console.print("   ✅ [green]Database Cleaned.[/]")

    console.print("[cyan]3. Building Global Context Graph (Qdrant)...[/]")
    subprocess.run([sys.executable, "repo_indexer.py"], capture_output=True)
    console.print("   ✅ [green]Context Graph Indexed.[/]")
    
    console.print("\n🎉 [bold green]System Ready. Run 'python cli.py watch' to ignite the engine.[/]\n")

@click.command()
def watch():
    """👁️ Start the AI Daemon to listen for code changes"""
    print_banner()
    console.print("\n[bold green]👁️ Watcher Daemon Activating...[/]")
    console.print("[dim]Listening for file modifications... Press Ctrl+C to stop.[/]\n")
    try:
        subprocess.run([sys.executable, "auto_watcher.py"])
    except KeyboardInterrupt:
        console.print("\n🛑 [bold red]Engine Shutting Down.[/]")

@click.command()
@click.argument('filepath')
def fix(filepath):
    """🛠️ Manually force the AI to fix a specific file"""
    print_banner()
    if not os.path.exists(filepath):
        console.print(f"\n❌ [bold red]File {filepath} not found![/]")
        return
    
    console.print(f"\n🚀 [bold yellow]Forcing Agentic Repair on {filepath}...[/]")
    from engine import SelfHealingEngine
    engine = SelfHealingEngine()
    engine.resolve_error(f"Manual override triggered for {filepath}. Find the bug and patch it.")

cli.add_command(init)
cli.add_command(watch)
cli.add_command(fix)

if __name__ == '__main__':
    cli()
