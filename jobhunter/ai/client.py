"""Cliente de IA generativa via API compativel com OpenAI (Chat Completions).

Configuravel: base_url, api_key (via keyring), model. Funciona com OpenAI,
Groq, OpenRouter, Ollama (openai-compat) etc. Se nao configurado, o modulo
fica explicitamente indisponivel (nunca simula respostas).
"""
from __future__ import annotations

import json

import requests

from ..db.repositories import settings_repo
from ..logging_setup import get_logger
from ..security.credentials import get_secret

log = get_logger("ai.client")


class AIUnavailableError(Exception):
    pass


class AIClient:
    def __init__(self):
        self.base_url = (settings_repo.get("ai_base_url", "") or
                         "https://api.openai.com/v1").rstrip("/")
        self.model = settings_repo.get("ai_model", "") or "gpt-4o-mini"
        self.api_key = get_secret("ai_api_key")

    def is_available(self) -> bool:
        # Ollama local não exige chave; demais provedores exigem.
        base = self.base_url.lower()
        if "localhost" in base or "127.0.0.1" in base:
            return bool(self.model)
        return bool(self.api_key)

    def _chat(self, messages: list[dict], temperature: float = 0.2,
              max_tokens: int = 900) -> str:
        if not self.is_available():
            raise AIUnavailableError(
                "IA não configurada. Informe base URL, modelo e chave na tela de IA.")
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        if resp.status_code >= 400:
            raise AIUnavailableError(f"IA retornou erro {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # pragma: no cover
            raise AIUnavailableError(f"Resposta de IA inesperada: {exc}") from exc

    def complete_json(self, system: str, user: str) -> dict:
        """Pede uma resposta JSON e faz parse tolerante."""
        raw = self._chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.1,
        )
        return _parse_json(raw)

    def complete_text(self, system: str, user: str, max_tokens: int = 700) -> str:
        return self._chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3, max_tokens=max_tokens,
        )


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except Exception as exc:
        raise AIUnavailableError(f"Não foi possível interpretar JSON da IA: {exc}") from exc
