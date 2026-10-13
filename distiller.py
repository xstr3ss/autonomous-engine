import json
import os
import logging
import subprocess

log = logging.getLogger("fable.distiller")

class DistillationEngine:
    def __init__(self, dataset_path="distillation_dataset.jsonl", batch_size=50):
        self.dataset_path = dataset_path
        self.batch_size = batch_size  # Trigger weight updates every 50 successful fixes

    def save_golden_record(self, instruction: str, successful_code: str):
        """Captures a perfectly verified interaction for local weight distillation."""
        
        # Format for standard LoRA fine-tuning (ShareGPT / ChatML format)
        record = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are Fable, an autonomous AI coding agent. You MUST output code modifications using surgical SEARCH/REPLACE blocks."
                },
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": successful_code}
            ]
        }
        
        with open(self.dataset_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            
        log.info("💧 [Distiller] Golden record captured for weight distillation.")
        self._check_threshold()

    def _check_threshold(self):
        """Checks if we have enough new data to trigger a background weight update."""
        if not os.path.exists(self.dataset_path):
            return
            
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        count = len(lines)
        if count > 0 and count % self.batch_size == 0:
            log.warning(f"🧠 [Distiller] Dataset reached {count} records! Triggering background LoRA fine-tune...")
            self._trigger_weight_evolution()

    def _trigger_weight_evolution(self):
        """
        In a production environment, this triggers a background PyTorch/Unsloth 
        script to update the local SLM's weights and reload it into Ollama.
        """
        log.info("⚙️ [Distiller] Compiling dataset and preparing local GPU for weight update...")
        # Placeholder for actual GPU training execution
        # subprocess.Popen(["python", "train_lora.py", "--dataset", self.dataset_path])
