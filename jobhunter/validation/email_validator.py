"""Validacao de e-mails: sintaxe, dominio, MX e classificacao de adequacao.

IMPORTANTE: nunca afirmamos que uma caixa postal existe apenas porque o dominio
possui MX. Os estados distinguem 'origem confirmada' de 'entrega nao confirmada'.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..constants import EMAIL_CATEGORY_KEYWORDS, EmailStatus
from ..logging_setup import get_logger
from .mx import has_mx

log = get_logger("validation.email")

# Regex pragmatico de sintaxe (evita falsos positivos obvios)
EMAIL_RE = re.compile(
    r"^(?=.{6,254}$)(?=.{1,64}@)[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)

DISPOSABLE_HINTS = ["mailinator", "tempmail", "10minutemail", "guerrillamail"]
# Dominios obvios de contato pessoal/generico para excluir
PERSONAL_DOMAINS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.com.br",
    "live.com", "bol.com.br", "uol.com.br", "terra.com.br", "icloud.com",
}


@dataclass
class ValidationResult:
    email: str
    syntax_ok: bool
    domain: str
    mx_ok: bool
    is_personal: bool
    is_disposable: bool
    category: str
    status: EmailStatus
    reason: str


def split_email(email: str) -> tuple[str, str]:
    email = (email or "").strip().lower()
    if "@" not in email:
        return email, ""
    local, _, domain = email.partition("@")
    return local, domain


def syntax_ok(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))


def classify_category(email: str) -> str:
    local, _ = split_email(email)
    local_norm = re.sub(r"[^a-z]", "", local)
    for kw in EMAIL_CATEGORY_KEYWORDS["recruitment"]:
        if re.sub(r"[^a-z]", "", kw) in local_norm:
            return "recruitment"
    for kw in EMAIL_CATEGORY_KEYWORDS["inadequate"]:
        if re.sub(r"[^a-z]", "", kw) in local_norm:
            return "inadequate"
    return "unknown"


def validate_email(email: str, check_mx: bool = True,
                   origin_confirmed: bool = False) -> ValidationResult:
    email = (email or "").strip().lower()
    local, domain = split_email(email)
    s_ok = syntax_ok(email)

    if not s_ok:
        return ValidationResult(email, False, domain, False, False, False,
                                "unknown", EmailStatus.INVALID,
                                "Sintaxe de e-mail inválida.")

    is_personal = domain in PERSONAL_DOMAINS
    is_disposable = any(h in domain for h in DISPOSABLE_HINTS)
    mx_ok = has_mx(domain) if check_mx else False
    category = classify_category(email)

    if is_personal:
        status = EmailStatus.INADEQUATE
        reason = "Domínio de e-mail pessoal/gratuito — inadequado para candidatura corporativa."
    elif is_disposable:
        status = EmailStatus.INVALID
        reason = "Domínio descartável/temporário."
    elif category == "inadequate":
        status = EmailStatus.INADEQUATE
        reason = "Endereço aparenta ser de setor não relacionado a recrutamento."
    elif origin_confirmed and mx_ok:
        status = EmailStatus.FOUND_CONFIRMED
        reason = "Endereço publicado em fonte verificável; domínio possui registros MX."
    elif mx_ok:
        status = EmailStatus.DOMAIN_VALID
        reason = ("Domínio possui MX, mas a existência da caixa não foi confirmada "
                  "(sem verificação SMTP).")
    else:
        status = EmailStatus.DOMAIN_VALID if category == "recruitment" else EmailStatus.INVALID
        reason = "Não foi possível confirmar registros MX do domínio."

    return ValidationResult(email, s_ok, domain, mx_ok, is_personal, is_disposable,
                            category, status, reason)
