"""Testes de extração de contatos a partir de HTML público (sem rede)."""
from __future__ import annotations

import unittest

from jobhunter.contacts.email_extractor import (
    _normalize_phone, extract_from_html,
)
from jobhunter.db.repositories import contact_repo, company_repo

from .base import DBTestCase


class ExtractorTests(unittest.TestCase):
    SAMPLE = """
    <html><body>
      <a href="mailto:rh@empresa.com.br?subject=vaga">Fale com o RH</a>
      <p>Contato: recrutamento@empresa.com.br</p>
      <p>Para candidaturas envie para selecao [at] empresa [dot] com [dot] br</p>
      <a href="/trabalhe-conosco">Trabalhe conosco</a>
      <a href="mailto:sac@empresa.com.br">SAC</a>
    </body></html>
    """

    def test_extract_emails_and_forms(self):
        result = extract_from_html(self.SAMPLE, "https://empresa.com.br/contato")
        emails = {e.email for e in result.emails}
        self.assertIn("rh@empresa.com.br", emails)
        self.assertIn("recrutamento@empresa.com.br", emails)
        self.assertIn("sac@empresa.com.br", emails)
        self.assertIn("selecao@empresa.com.br", emails)
        self.assertTrue(any("trabalhe-conosco" in f for f in result.form_urls))

    def test_cloudflare_decode(self):
        # "rh@empresa.com.br" codificado
        plain = "rh@empresa.com.br"
        key = 0x2A
        encoded = f"{key:02x}" + "".join(f"{ord(c) ^ key:02x}" for c in plain)
        html = f'<a href="/cdn-cgi/l/email-protection" data-cfemail="{encoded}">x</a>'
        result = extract_from_html(html, "https://empresa.com.br")
        self.assertIn("rh@empresa.com.br", {e.email for e in result.emails})


class PhoneExtractorTests(unittest.TestCase):
    def test_normalize_phone(self):
        self.assertEqual(_normalize_phone("(11) 91234-5678"), "+55 (11) 91234-5678")
        self.assertEqual(_normalize_phone("+55 21 98765-4321"), "+55 (21) 98765-4321")
        self.assertEqual(_normalize_phone("11 3456-7890"), "+55 (11) 3456-7890")
        self.assertEqual(_normalize_phone("2024"), "")
        self.assertEqual(_normalize_phone("R$ 5.000"), "")

    def test_extract_phones_from_html(self):
        html = """
        <html><body>
          <a href="tel:+5511987654321">Ligue agora</a>
          <p>RH: (11) 91234-5678</p>
          <p>SAC: 0800 123 4567</p>
          <p>Ano de 2024, valor R$ 5.000,00</p>
        </body></html>
        """
        result = extract_from_html(html, "https://empresa.com.br/contato")
        phones = {p.phone for p in result.phones}
        self.assertIn("+55 (11) 98765-4321", phones)
        self.assertIn("+55 (11) 91234-5678", phones)
        self.assertTrue(any("0800" in p for p in phones))
        self.assertFalse(any(p == "2024" for p in phones))


class PhoneStorageTests(DBTestCase):
    def test_phone_saved_and_listed(self):
        cid = company_repo.get_or_create("Empresa Tel", domain="empresa-tel.com.br")
        contact_repo.add(company_id=cid, phone="+55 (11) 91234-5678",
                         status="Telefone encontrado")
        rows = contact_repo.list()
        self.assertTrue(any(r["phone"] == "+55 (11) 91234-5678" for r in rows))
        found = contact_repo.list(search="91234")
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
