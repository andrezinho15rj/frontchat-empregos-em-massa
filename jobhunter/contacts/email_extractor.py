"""Extração de e-mails corporativos e formulários publicados em páginas publicas.

Regras:
- Somente páginas publicas (home, contato, carreiras, trabalhe conosco, vagas).
- Nao contorna login, CAPTCHA ou restricao de acesso.
- Nao inventa enderecos; somente o que estiver publicado na pagina.
- Decodifica ofuscacao simples (ex.: Cloudflare data-cfemail), que faz parte do
  conteudo publico.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..logging_setup import get_logger

log = get_logger("contacts.extractor")

EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
)
OBFUSCATED_RE = re.compile(
    r"([A-Za-z0-9._%+\-]+)\s*(?:\[at\]|\(at\)|\sat\s|&#64;|\s@\s)\s*"
    r"([A-Za-z0-9.\-]+\s*(?:\[dot\]|\(dot\)|\sdot\s|\.)\s*[A-Za-z]{2,})",
    re.IGNORECASE,
)


def _deobfuscate(text: str) -> str:
    """Converte 'nome [at] dominio [dot] com' em 'nome@dominio.com' (conteudo publico)."""
    text = re.sub(r"\s*\[\s*at\s*\]\s*|\s*\(\s*at\s*\)\s*", "@", text, flags=re.I)
    text = re.sub(r"\s*\[\s*dot\s*\]\s*|\s*\(\s*dot\s*\)\s*", ".", text, flags=re.I)
    text = re.sub(r"\s+arroba\s+", "@", text, flags=re.I)
    text = re.sub(r"\s+ponto\s+", ".", text, flags=re.I)
    return text

FORM_KEYWORDS = [
    "formul", "candidat", "apply", "inscri", "trabalhe", "vaga", "carreira",
    "career", "job", "recrutamento", "processo seletivo", "curriculo",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36 FrontchatEmpregosEmMassa/1.0"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# Paginas publicas tipicas de contato/recrutamento (caminhos relativos)
CANDIDATE_PATHS = [
    "", "/contato", "/fale-conosco", "/contact", "/carreiras", "/careers",
    "/trabalhe-conosco", "/trabalheconosco", "/trabalhe_conosco", "/vagas",
    "/jobs", "/recrutamento", "/quem-somos", "/sobre",
]


@dataclass
class ExtractedContact:
    email: str
    source_url: str
    context: str = ""


@dataclass
class ExtractResult:
    emails: list[ExtractedContact] = field(default_factory=list)
    form_urls: list[str] = field(default_factory=list)
    pages_fetched: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _decode_cloudflare(encoded: str) -> str:
    try:
        r = int(encoded[:2], 16)
        return "".join(
            chr(int(encoded[i:i + 2], 16) ^ r) for i in range(2, len(encoded), 2)
        )
    except Exception:
        return ""


def _clean(email: str) -> str:
    email = email.strip().strip(".,;:()<>[]{}\"'").lower()
    # remove sufixos comuns erroneamente capturados (ex.: .png)
    email = re.sub(r"\.(png|jpg|jpeg|gif|webp|svg|css|js|woff2?)$", "", email)
    return email


def extract_from_html(html: str, base_url: str) -> ExtractResult:
    result = ExtractResult()
    if not html:
        return result

    soup = BeautifulSoup(html, "lxml")

    # 1) Cloudflare-protected emails
    for node in soup.select("[data-cfemail]"):
        decoded = _decode_cloudflare(node.get("data-cfemail", ""))
        if decoded and "@" in decoded:
            result.emails.append(ExtractedContact(_clean(decoded), base_url,
                                                  "data-cfemail ofuscado"))

    # 2) mailto:
    for a in soup.select("a[href^=mailto]"):
        href = a.get("href", "")
        addr = href[7:].split("?")[0]
        if addr and "@" in addr:
            result.emails.append(ExtractedContact(
                _clean(addr), base_url, (a.get_text(" ", strip=True) or "")[:120]))

    # 3) texto visivel + atributos
    text = soup.get_text(" ", strip=True)
    for m in EMAIL_RE.finditer(text):
        result.emails.append(ExtractedContact(_clean(m.group(0)), base_url, "texto da página"))

    # 4) ofuscacao simples (nome [at] dominio [dot] com) — desofusca e extrai
    deobfuscated = _deobfuscate(text)
    for m in EMAIL_RE.finditer(deobfuscated):
        result.emails.append(ExtractedContact(_clean(m.group(0)), base_url,
                                               "e-mail ofuscado (at/dot)"))

    # 5) formularios de candidatura
    for a in soup.find_all("a", href=True):
        href = a["href"]
        label = (a.get_text(" ", strip=True) + " " + href).lower()
        if any(k in label for k in FORM_KEYWORDS):
            full = urljoin(base_url, href)
            if full.startswith("http") and full not in result.form_urls:
                result.form_urls.append(full)

    return result


class ContactExtractor:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def _fetch(self, url: str) -> str | None:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout,
                                allow_redirects=True)
            ctype = resp.headers.get("Content-Type", "")
            if resp.status_code == 200 and "text" in ctype.lower():
                return resp.text
            if resp.status_code == 200 and "html" in ctype.lower():
                return resp.text
        except Exception as exc:  # pragma: no cover
            log.debug("Falha ao buscar %s: %s", url, exc)
        return None

    def scan_site(self, website: str, max_pages: int = 6) -> ExtractResult:
        """Varre paginas publicas de um site e coleta e-mails/formularios."""
        result = ExtractResult()
        if not website:
            return result
        if not website.startswith("http"):
            website = "https://" + website
        parsed = urlparse(website)
        root = f"{parsed.scheme}://{parsed.netloc}"

        for path in CANDIDATE_PATHS:
            if len(result.pages_fetched) >= max_pages:
                break
            url = urljoin(root + "/", path.lstrip("/")) if path else root
            if url in result.pages_fetched:
                continue
            html = self._fetch(url)
            if not html:
                continue
            result.pages_fetched.append(url)
            page = extract_from_html(html, url)
            result.emails.extend(page.emails)
            for f in page.form_urls:
                if f not in result.form_urls:
                    result.form_urls.append(f)
        return result

    def scan_page(self, url: str) -> ExtractResult:
        result = ExtractResult()
        html = self._fetch(url)
        if html:
            result.pages_fetched.append(url)
            page = extract_from_html(html, url)
            result.emails = page.emails
            result.form_urls = page.form_urls
        return result
