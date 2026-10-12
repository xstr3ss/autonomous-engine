from __future__ import annotations
import logging
import time
import os
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import Config

log = logging.getLogger("fable.llm")

class LLMClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._local_down_until = 0.0
        
        self.session = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"POST", "GET"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self._cached_cloud_model = None
        
        # 🚨 THE FIX: Advanced Diff Engine System Prompt
        self.system_prompt = (
            "You are Fable, an autonomous AI coding agent. "
            "You MUST output code modifications using surgical SEARCH/REPLACE blocks.\n"
            "Format exactly like this:\n"
            "FILE: filename.py\n"
            "<<<< SEARCH\n"
            "Exact lines to replace (leave blank if creating a new file)\n"
            "==== REPLACE\n"
            "New lines of code\n"
            ">>>>\n\n"
            "Never deviate from this format. No conversational text."
        )

    def _get_valid_groq_model(self, api_key: str) -> str:
        if self._cached_cloud_model:
            return self._cached_cloud_model
            
        log.info("🔍 [LLM] Auto-discovering available Groq models...")
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            res = self.session.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10).json()
            models = [m["id"] for m in res.get("data", [])]
            
            valid_models = [m for m in models if "guard" not in m.lower() and "whisper" not in m.lower() and "vision" not in m.lower()]
            
            for target in ["llama-3.1", "qwen", "llama3"]:
                for m in valid_models:
                    if target in m.lower():
                        self._cached_cloud_model = m
                        log.info(f"🎯 [LLM] Selected Groq model: {m}")
                        return m
                        
            self._cached_cloud_model = valid_models[0]
            return valid_models[0]
        except Exception as e:
            log.warning(f"⚠️ [LLM] Model discovery failed, falling back to llama-3.1-8b-instant. Error: {e}")
            return "llama-3.1-8b-instant"

    def get_local_response(self, prompt: str, timeout: Optional[int] = None) -> str:
        payload = {
            "model": self.cfg.local_model,
            "prompt": prompt,
            "system": self.system_prompt,
            "stream": False,
            "options": {"temperature": self.cfg.temperature},
        }
        res = self.session.post(self.cfg.local_url, json=payload, timeout=timeout or self.cfg.local_timeout)
        res.raise_for_status()
        return res.json().get("response", "")

    def get_cloud_response(self, prompt: str) -> str:
        api_key = os.getenv("GROQ_API_KEY", self.cfg.groq_api_key)
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        
        active_model = self._get_valid_groq_model(api_key)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": active_model,
            # 🚨 THE FIX: Injecting the system prompt into Groq
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }
        
        cloud_url = "https://api.groq.com/openai/v1/chat/completions"
        
        res = self.session.post(cloud_url, headers=headers, json=payload, timeout=120)
        
        if res.status_code != 200:
            log.error(f"❌ [Groq API Error] {res.text}")
            res.raise_for_status()
            
        return res.json()["choices"][0]["message"]["content"]

    def generate(self, prompt: str, force_cloud: bool = False, slow: bool = False) -> str:
        skip_local = self.cfg.prefer_cloud or (force_cloud and bool(os.getenv("GROQ_API_KEY", self.cfg.groq_api_key)))
        if not skip_local and time.monotonic() >= self._local_down_until:
            timeout = self.cfg.local_timeout * (3 if slow else 1)
            for attempt in range(1, self.cfg.local_retries + 1):
                log.info("🔄 [Agent Loop] Attempt %d/%d (Local SLM)...", attempt, self.cfg.local_retries)
                try:
                    text = self.get_local_response(prompt, timeout)
                    if text.strip():
                        return text
                    log.warning("⚠️ [Local API] Empty response")
                except (requests.ConnectionError, requests.Timeout) as e:
                    log.warning("⚠️ [Local API] Unreachable (is Ollama running?): %s", self.cfg.local_model, e)
                    break
                except requests.RequestException as e:
                    log.warning("⚠️ [Local API] Failed: %s", e)
                time.sleep(0.5 * attempt)
            self._local_down_until = time.monotonic() + self.cfg.local_cooldown

        log.info("🚀 [Tier 2] Escalating to Groq Cloud Engine...")
        return self.get_cloud_response(prompt)
