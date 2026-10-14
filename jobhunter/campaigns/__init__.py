from .templates import (
    default_templates, default_apresentacao, render, build_values,
    available_variables, VARIABLES,
)
from .providers import SmtpProvider, SendResult, PRESETS
from .engine import CampaignEngine, campaign_engine, PrepareReport, SendReport

__all__ = [
    "default_templates", "default_apresentacao", "render", "build_values",
    "available_variables", "VARIABLES", "SmtpProvider", "SendResult", "PRESETS",
    "CampaignEngine", "campaign_engine", "PrepareReport", "SendReport",
]
