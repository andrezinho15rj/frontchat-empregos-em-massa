"""Provedores de envio de e-mail (SMTP autenticado / OAuth2 XOAUTH2).

- Autenticacao por senha de app (Gmail, Outlook, Zoho, etc.) via SMTP.
- Autenticacao OAuth2 (XOAUTH2) usando access token obtido no fluxo de
  autorizacao (ver oauth.py).

Nao implementa qualquer mecanismo para burlar limites, filtros antispam ou
bloqueios. O envio respeita intervalos e limites configuraveis.
"""
from __future__ import annotations

import mimetypes
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

from ..logging_setup import get_logger

log = get_logger("campaigns.provider")


@dataclass
class SendResult:
    success: bool
    to_email: str
    message_id: str = ""
    error: str = ""
    smtp_code: int | None = None
    provider: str = ""


PRESETS = {
    "Gmail": {"host": "smtp.gmail.com", "port": 587, "security": "starttls",
              "auth": "app_password", "note": "Use uma Senha de App do Google."},
    "Outlook / Office 365": {"host": "smtp.office365.com", "port": 587,
                             "security": "starttls", "auth": "app_password",
                             "note": "Requer senha de app / SMTP AUTH habilitado."},
    "Outlook.com": {"host": "smtp-mail.outlook.com", "port": 587,
                    "security": "starttls", "auth": "app_password",
                    "note": "Requer senha de app."},
    "Yahoo": {"host": "smtp.mail.yahoo.com", "port": 587, "security": "starttls",
              "auth": "app_password", "note": "Requer senha de app."},
    "Zoho": {"host": "smtp.zoho.com", "port": 587, "security": "starttls",
             "auth": "app_password", "note": "Use senha de app do Zoho."},
    "Personalizado (SMTP)": {"host": "", "port": 587, "security": "starttls",
                             "auth": "app_password", "note": "Informe host/porta do seu provedor."},
}


class SmtpProvider:
    def __init__(self, host: str, port: int, username: str, password: str = "",
                 access_token: str = "", security: str = "starttls",
                 from_email: str = "", from_name: str = ""):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.access_token = access_token
        self.security = security  # 'starttls' | 'ssl' | 'none'
        self.from_email = from_email or username
        self.from_name = from_name

    def _connect(self) -> smtplib.SMTP:
        context = ssl.create_default_context()
        if self.security == "ssl":
            server: smtplib.SMTP = smtplib.SMTP_SSL(
                self.host, self.port, timeout=45, context=context)
        else:
            server = smtplib.SMTP(self.host, self.port, timeout=45)
            server.ehlo()
            if self.security == "starttls":
                server.starttls(context=context)
                server.ehlo()
        return server

    def _authenticate(self, server: smtplib.SMTP) -> None:
        if self.access_token:
            auth_str = f"user={self.username}\x01auth=Bearer {self.access_token}\x01\x01"
            server.auth("XOAUTH2", lambda x=None: auth_str.encode())
        elif self.password:
            server.login(self.username, self.password)
        else:
            raise RuntimeError("Sem credenciais: informe senha de app ou access token.")

    @staticmethod
    def _attach(msg: EmailMessage, path: Path) -> None:
        ctype, _ = mimetypes.guess_type(str(path))
        if ctype:
            maintype, subtype = ctype.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"
        with open(path, "rb") as fh:
            msg.add_attachment(fh.read(), maintype=maintype, subtype=subtype,
                               filename=path.name)

    def verify_login(self) -> tuple[bool, str]:
        try:
            server = self._connect()
            self._authenticate(server)
            server.noop()
            server.quit()
            return True, "Autenticação SMTP bem-sucedida."
        except Exception as exc:
            return False, f"Falha de autenticação SMTP: {exc}"

    def send(self, to_email: str, subject: str, body: str,
             attachments: list[str] | None = None,
             reply_to: str = "") -> SendResult:
        msg = EmailMessage()
        msg["From"] = formataddr((self.from_name or self.from_email, self.from_email))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Message-ID"] = make_msgid()
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(body)
        for att in (attachments or []):
            p = Path(att)
            if p.exists():
                self._attach(msg, p)
        try:
            server = self._connect()
            self._authenticate(server)
            server.send_message(msg)
            server.quit()
            return SendResult(True, to_email, msg["Message-ID"], provider="smtp")
        except smtplib.SMTPResponseException as exc:
            return SendResult(False, to_email, error=f"SMTP {exc.smtp_code}: {exc.smtp_error}",
                              smtp_code=exc.smtp_code, provider="smtp")
        except Exception as exc:
            return SendResult(False, to_email, error=str(exc), provider="smtp")
