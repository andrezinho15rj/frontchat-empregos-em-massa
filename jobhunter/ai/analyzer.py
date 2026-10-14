"""Modulo de IA: analise de compatibilidade e personalizacao.

Regra absoluta: a IA NUNCA deve inventar experiencias, diplomas, certificados ou
competencias que nao estejam no curriculo. O system prompt reforca isso e o
resultado e sinalizado como sugestao sujeita a revisao humana.
"""
from __future__ import annotations

from ..logging_setup import get_logger
from .client import AIClient, AIUnavailableError

log = get_logger("ai.analyzer")

MATCH_SYSTEM = (
    "Você é um assistente de recrutamento. Compare a vaga com o CURRÍCULO fornecido. "
    "NUNCA invente experiências, diplomas, certificados ou competências que não estejam "
    "explicitamente no currículo. Responda SOMENTE com JSON válido no formato: "
    '{"score": <0-100>, "skills_relevantes": [..], "lacunas": [..], '
    '"prioridade": "alta|media|baixa", "justificativa": "..."}. '
    "O score deve ser calculado apenas com base no que está no currículo e na descrição da vaga."
)

PERSONALIZE_SYSTEM_PT = (
    "Você redige e-mails de candidatura profissionais em português do Brasil. "
    "Use APENAS informações presentes no currículo. NUNCA invente qualificações. "
    "Responda SOMENTE com JSON: {\"assunto\": \"...\", \"apresentacao\": \"...\"}. "
    "O campo 'apresentacao' é um parágrafo curto de apresentação (2 a 3 frases)."
)

PERSONALIZE_SYSTEM_EN = (
    "You write professional job application emails in English. "
    "Use ONLY information found in the resume. NEVER invent qualifications. "
    "Reply ONLY with JSON: {\"assunto\": \"...\", \"apresentacao\": \"...\"}. "
    "'apresentacao' is a short 2-3 sentence introduction paragraph."
)


class AIAnalyzer:
    def __init__(self, client: AIClient | None = None):
        self.client = client or AIClient()

    def is_available(self) -> bool:
        return self.client.is_available()

    def match(self, job_title: str, job_description: str,
              resume_text: str) -> dict:
        user = (
            f"VAGA: {job_title}\n\nDESCRIÇÃO DA VAGA:\n{(job_description or '')[:6000]}\n\n"
            f"CURRÍCULO DO CANDIDATO:\n{(resume_text or '')[:8000]}"
        )
        try:
            data = self.client.complete_json(MATCH_SYSTEM, user)
        except AIUnavailableError as exc:
            log.info("IA indisponível para análise: %s", exc)
            raise
        score = data.get("score")
        try:
            score = float(score)
        except Exception:
            score = None
        return {
            "score": score,
            "skills": data.get("skills_relevantes", []) or [],
            "gaps": data.get("lacunas", []) or [],
            "priority": (data.get("prioridade", "") or "").lower(),
            "reason": data.get("justificativa", "") or "",
        }

    def personalize(self, company: str, job_title: str, resume_text: str,
                    language: str = "pt") -> dict:
        system = PERSONALIZE_SYSTEM_EN if language == "en" else PERSONALIZE_SYSTEM_PT
        if language == "en":
            user = (f"Company: {company}\nPosition: {job_title}\n\n"
                    f"RESUME:\n{(resume_text or '')[:8000]}")
        else:
            user = (f"Empresa: {company}\nCargo: {job_title}\n\n"
                    f"CURRÍCULO:\n{(resume_text or '')[:8000]}")
        data = self.client.complete_json(system, user)
        return {
            "subject": data.get("assunto", "") or "",
            "apresentacao": data.get("apresentacao", "") or "",
        }
