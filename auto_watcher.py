import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from engine import SelfHealingEngine

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.engine = SelfHealingEngine()
        self.is_healing = False
        self.last_trigger = 0 
        # Ignore our engine's own files so it doesn't trigger on itself
        self.system_files = {
            'engine.py', 'auto_watcher.py', 'bug_resolution_store.py', 
            'docker_sandbox.py', 'tier0_parser.py', 'diff_engine.py', 
            'repo_indexer.py', 'setup_rag_challenge.py', 'fix_indexer.py'
        }

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.py'):
            return
            
        if '__pycache__' in event.src_path or '.pytest_cache' in event.src_path:
            return
            
        filename = os.path.basename(event.src_path)
        
        # Smart blacklist instead of a hard whitelist
        if filename in self.system_files or filename.startswith('.'):
            return

        current_time = time.time()
        
        if self.is_healing or (current_time - self.last_trigger) < 3.0:
            return

        self.last_trigger = current_time
        self.is_healing = True
        
        try:
            print(f"\n📁 [Watcher] Detected modification in: {filename}")
            print("⚙️ [Watcher] Executing local CI/CD pipeline...")
            
            # Dynamically run pytest on the file that changed
            target = filename if filename.startswith("test_") else ""
            cmd = ["python", "-m", "pytest"]
            if target: cmd.append(target)
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print("🚨 [Watcher] Pipeline failed! Booting Self-Healing Engine...")
                self.engine.resolve_error(result.stdout)
            else:
                print("✅ [Watcher] Pipeline passed. Agent returning to sleep.")
        except Exception as e:
            print(f"⚠️ [Watcher Error] {e}")
        finally:
            self.is_healing = False

if __name__ == "__main__":
    print("👁️ [Watcher] Daemon online. Listening for live code changes...")
    event_handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 [Watcher] Shutting down daemon...")
        observer.stop()
        event_handler.engine.shutdown()
    observer.join()
