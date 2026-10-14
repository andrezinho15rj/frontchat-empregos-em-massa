"""Testes de extração de contatos a partir de HTML público (sem rede)."""
from __future__ import annotations

import unittest

from jobhunter.contacts.email_extractor import extract_from_html


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


if __name__ == "__main__":
    unittest.main()
