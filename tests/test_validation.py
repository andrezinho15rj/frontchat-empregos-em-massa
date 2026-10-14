"""Testes de validação de e-mail (sintaxe, classificação, MX)."""
from __future__ import annotations

import unittest

from jobhunter.constants import EmailStatus
from jobhunter.validation.email_validator import (
    classify_category, syntax_ok, validate_email,
)
from jobhunter.validation.dedup import mark_duplicates

from .base import DBTestCase, network_available


class EmailValidationTests(unittest.TestCase):
    def test_syntax(self):
        self.assertTrue(syntax_ok("rh@empresa.com.br"))
        self.assertTrue(syntax_ok("recrutamento@empresa.com"))
        self.assertFalse(syntax_ok("sem-arroba.com"))
        self.assertFalse(syntax_ok("a@b"))
        self.assertFalse(syntax_ok("@empresa.com"))

    def test_category(self):
        self.assertEqual(classify_category("rh@x.com"), "recruitment")
        self.assertEqual(classify_category("trabalheconosco@x.com"), "recruitment")
        self.assertEqual(classify_category("sac@x.com"), "inadequate")
        self.assertEqual(classify_category("financeiro@x.com"), "inadequate")

    def test_personal_domain_inadequate(self):
        res = validate_email("fulano@gmail.com", check_mx=False)
        self.assertEqual(res.status, EmailStatus.INADEQUATE)

    def test_no_mx_does_not_confirm(self):
        res = validate_email("rh@empresa.com.br", check_mx=False)
        # sem MX não afirmamos nada como confirmado
        self.assertNotEqual(res.status, EmailStatus.FOUND_CONFIRMED)

    @unittest.skipUnless(network_available(), "rede indisponível")
    def test_mx_real_domain(self):
        res = validate_email("rh@gmail.com", check_mx=True)
        # gmail tem MX; mas domínio pessoal continua inadequado
        self.assertTrue(res.mx_ok)
        self.assertEqual(res.status, EmailStatus.INADEQUATE)


class DedupTests(DBTestCase):
    def test_mark_duplicates(self):
        from jobhunter.db.repositories import company_repo, contact_repo
        cid = company_repo.get_or_create("Empresa", domain="emp.com")
        cid2 = company_repo.get_or_create("Empresa 2", domain="emp2.com")
        contact_repo.add(cid, email="rh@emp.com", domain="emp.com")
        contact_repo.add(cid, email="recrutamento@emp.com", domain="emp.com")
        # mesmo e-mail aparecendo em outra empresa (ex.: mesmo recrutador)
        contact_repo.add(cid2, email="rh@emp.com", domain="emp.com")
        marked = mark_duplicates()
        self.assertGreaterEqual(marked, 1)
        from jobhunter.db.database import database
        dup = database.query_one(
            "SELECT is_duplicate FROM contacts WHERE email='rh@emp.com' ORDER BY id DESC LIMIT 1")
        self.assertEqual(dup["is_duplicate"], 1)


if __name__ == "__main__":
    unittest.main()
