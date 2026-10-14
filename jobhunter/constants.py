"""Enumeracoes e constantes de dominio compartilhadas."""
from __future__ import annotations

from enum import Enum


class WorkMode(str, Enum):
    PRESENCIAL = "Presencial"
    HIBRIDO = "Híbrido"
    REMOTO = "Remoto"
    DESCONHECIDO = "Não informado"


class ContractType(str, Enum):
    CLT = "CLT"
    ESTAGIO = "Estágio"
    APRENDIZ = "Jovem Aprendiz"
    TEMPORARIO = "Temporário"
    FREELANCER = "Freelancer"
    PJ = "PJ"
    OUTRO = "Outro"


class EmailStatus(str, Enum):
    """Estados de validacao/qualidade de contato.

    Nunca marcamos um endereco como existente apenas porque o dominio possui MX.
    """
    FOUND_CONFIRMED = "Encontrado e origem confirmada"
    DOMAIN_VALID = "Domínio válido, entrega não confirmada"
    INVALID = "E-mail inválido"
    DUPLICATE = "E-mail duplicado"
    INADEQUATE = "Contato inadequado para candidatura"
    FORM_AVAILABLE = "Formulário de candidatura disponível"
    UNCHECKED = "Não verificado"


class ApplicationStatus(str, Enum):
    PREPARED = "Preparada"
    QUEUED = "Na fila"
    SENT = "Enviada"
    FAILED = "Falha no envio"
    CANCELLED = "Cancelada"
    REPLY = "Resposta recebida"
    INTERVIEW = "Entrevista"


class CampaignStatus(str, Enum):
    DRAFT = "Rascunho"
    REVIEW = "Aguardando revisão"
    RUNNING = "Em execução"
    PAUSED = "Pausada"
    DONE = "Concluída"
    CANCELLED = "Cancelada"


AREA_OPTIONS = [
    "Administrativo",
    "Comercial / Vendas",
    "Tecnologia",
    "Atendimento / SAC",
    "Logística",
    "Financeiro",
    "Marketing",
    "Recursos Humanos",
    "Engenharia",
    "Saúde",
    "Educação",
    "Jurídico",
    "Outras",
]

PUBLICATION_PERIODS = {
    "Últimas 24 horas": 1,
    "Últimos 7 dias": 7,
    "Últimos 15 dias": 15,
    "Últimos 30 dias": 30,
    "Personalizado": None,
}

EMAIL_CATEGORY_KEYWORDS = {
    "recruitment": [
        "rh", "recrutamento", "selecao", "seleção", "talentos", "carreiras",
        "trabalheconosco", "trabalhe-conosco", "vagas", "curriculo", "currículo",
        "gente", "people", "recruiting", "careers", "jobs", "hr", "humanresources",
    ],
    "inadequate": [
        "sac", "atendimento", "suporte", "financeiro", "cobranca", "cobrança",
        "fiscal", "compras", "marketing", "imprensa", "comercial", "vendas",
        "juridico", "jurídico", "lgpd", "dpo", "privacidade",
    ],
}
