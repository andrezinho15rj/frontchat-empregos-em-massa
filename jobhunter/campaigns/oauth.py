"""Infraestrutura OAuth 2.0 para Gmail e Outlook (Office 365).

Implementa:
- Renovacao de access token a partir de refresh token (ambos os provedores).
- Fluxo Google "installed app" (loopback) usando client_id/client_secret proprios.
- Fluxo Microsoft "device code" (nao requer servidor de redirecionamento).

O usuario deve criar seu proprio cliente OAuth no Google Cloud Console / Azure AD.
Nenhum token e gravado em texto puro: use o keyring (jobhunter.security).
"""
from __future__ import annotations

import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from ..logging_setup import get_logger

log = get_logger("campaigns.oauth")

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPE = "https://mail.google.com/ https://www.googleapis.com/auth/userinfo.email"

MS_TENANT = "common"
MS_DEVICE = f"https://login.microsoftonline.com/{MS_TENANT}/oauth2/v2.0/devicecode"
MS_TOKEN = f"https://login.microsoftonline.com/{MS_TENANT}/oauth2/v2.0/token"
MS_SCOPE = "https://outlook.office.com/SMTP.Send offline_access openid email"


def google_auth_url(client_id: str, redirect_uri: str = "http://localhost:8765/") -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH}?{urllib.parse.urlencode(params)}"


def google_exchange_code(client_id: str, client_secret: str, code: str,
                         redirect_uri: str = "http://localhost:8765/") -> dict:
    resp = requests.post(GOOGLE_TOKEN, data={
        "client_id": client_id, "client_secret": client_secret,
        "code": code, "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def google_loopback_flow(client_id: str, client_secret: str,
                         timeout: int = 180) -> dict:
    """Abre o navegador e captura o codigo no loopback local. Retorna tokens."""
    result: dict = {}
    ready = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            result["code"] = (params.get("code") or [""])[0]
            result["error"] = (params.get("error") or [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Autorização concluída. Você pode fechar esta aba.".encode())
            ready.set()

        def log_message(self, *args):
            pass

    server = HTTPServer(("localhost", 8765), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    webbrowser.open(google_auth_url(client_id))
    ready.wait(timeout=timeout)
    server.shutdown()
    if not result.get("code"):
        raise RuntimeError(f"Autorização Google falhou: {result.get('error') or 'timeout'}")
    return google_exchange_code(client_id, client_secret, result["code"])


def microsoft_device_flow(client_id: str, timeout: int = 300) -> dict:
    """Fluxo device code do Microsoft. Retorna tokens (access + refresh)."""
    resp = requests.post(MS_DEVICE, data={"client_id": client_id, "scope": MS_SCOPE},
                         timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print(f"\nAcesse {data['verification_uri']} e informe o código: {data['user_code']}\n")
    try:
        webbrowser.open(data.get("verification_uri", ""))
    except Exception:
        pass
    interval = int(data.get("interval", 5))
    deadline = time.time() + min(timeout, int(data.get("expires_in", 900)))
    while time.time() < deadline:
        time.sleep(interval)
        token_resp = requests.post(MS_TOKEN, data={
            "client_id": client_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": data["device_code"],
        }, timeout=30)
        payload = token_resp.json()
        if "access_token" in payload:
            return payload
        if payload.get("error") not in ("authorization_pending", "slow_down"):
            raise RuntimeError(f"Device flow falhou: {payload.get('error_description', payload)}")
    raise RuntimeError("Device flow expirou.")


def refresh_google(client_id: str, client_secret: str, refresh_token: str) -> str:
    resp = requests.post(GOOGLE_TOKEN, data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def refresh_microsoft(client_id: str, refresh_token: str,
                      client_secret: str = "") -> str:
    data = {
        "client_id": client_id, "refresh_token": refresh_token,
        "grant_type": "refresh_token", "scope": MS_SCOPE,
    }
    if client_secret:
        data["client_secret"] = client_secret
    resp = requests.post(MS_TOKEN, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]
