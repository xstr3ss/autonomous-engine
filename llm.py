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
            allowed_methods=frozenset({"POST"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_local_response(self, prompt: str, timeout: Optional[int] = None) -> str:
        payload = {
            "model": self.cfg.local_model,
            "prompt": prompt,
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
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # FORCE synchronization with chat.py, bypassing the config cache
        active_model = os.getenv("FABLE_CLOUD_MODEL", "llama-3.3-70b-versatile")
        
        payload = {
            "model": active_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        
        # HARDCODE exact URL string to prevent any hidden \r character bugs
        cloud_url = "https://api.groq.com/openai/v1/chat/completions"
        
        res = self.session.post(cloud_url, headers=headers, json=payload, timeout=120)
        
        # Print the ACTUAL JSON error from Groq instead of failing silently
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
