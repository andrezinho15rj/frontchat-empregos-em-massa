"""Modelos de mensagem e renderizacao de variaveis (sem IA)."""
from __future__ import annotations

import re
from string import Formatter

DEFAULT_SUBJECT_PT = "Candidatura para {cargo} — {candidato}"

DEFAULT_BODY_PT = """Olá, equipe de recrutamento da {empresa}!

Identifiquei a oportunidade para {cargo} e gostaria de apresentar minha candidatura.

{apresentacao}

Encaminho meu currículo em anexo para avaliação.

Agradeço pela atenção e fico à disposição para uma entrevista.

Atenciosamente,
{candidato}"""

DEFAULT_APRESENTACAO = (
    "Tenho experiência em atividades relacionadas à área e acredito que meu perfil "
    "poderá contribuir para a equipe."
)

DEFAULT_SUBJECT_EN = "Application for {cargo} — {candidato}"

DEFAULT_BODY_EN = """Hello {empresa} recruiting team,

I noticed the opening for {cargo} and would like to submit my application.

{apresentacao}

Please find my resume attached for your consideration.

Thank you for your time; I am available for an interview.

Best regards,
{candidato}"""

DEFAULT_APRESENTACAO_EN = (
    "I have experience in the field and believe my profile can contribute to the team."
)

# Variaveis suportadas
VARIABLES = [
    "empresa", "cargo", "candidato", "area", "cidade", "estado",
    "remetente", "apresentacao",
]


def default_templates(language: str = "pt") -> tuple[str, str]:
    if language == "en":
        return DEFAULT_SUBJECT_EN, DEFAULT_BODY_EN
    return DEFAULT_SUBJECT_PT, DEFAULT_BODY_PT


def default_apresentacao(language: str = "pt") -> str:
    return DEFAULT_APRESENTACAO_EN if language == "en" else DEFAULT_APRESENTACAO


def available_variables(template: str) -> list[str]:
    try:
        return [f for _, f, _, _ in Formatter().parse(template) if f]
    except Exception:
        return []


def render(template: str, values: dict[str, str]) -> str:
    """Substitui {variaveis} com valores seguros. Variaveis ausentes viram string vazia."""
    if not template:
        return ""

    class _Safe(dict):
        def __missing__(self, key):
            return ""

    try:
        return Formatter().vformat(template, (), _Safe(values))
    except Exception:
        # fallback: substituicao manual
        out = template
        for k, v in values.items():
            out = out.replace("{" + k + "}", str(v or ""))
        return re.sub(r"\{[a-z_]+\}", "", out)


def build_values(company: str, title: str, candidate: str, area: str = "",
                 city: str = "", state: str = "", sender: str = "",
                 apresentacao: str = "") -> dict[str, str]:
    return {
        "empresa": company or "sua empresa",
        "cargo": title or "a vaga anunciada",
        "candidato": candidate or "Candidato(a)",
        "area": area or "",
        "cidade": city or "",
        "estado": state or "",
        "remetente": sender or candidate or "",
        "apresentacao": apresentacao,
    }
