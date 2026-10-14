"""Orquestrador de descoberta de contatos de recrutamento por empresa/jovaga."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import EmailStatus
from ..db.repositories import company_repo, contact_repo, job_repo
from ..logging_setup import get_logger
from ..validation.dedup import mark_duplicates
from ..validation.email_validator import validate_email
from .email_extractor import ContactExtractor
from .website_finder import domain_from_url, find_company_website

log = get_logger("contacts.finder")


@dataclass
class ContactDiscoveryReport:
    companies_processed: int = 0
    emails_found: int = 0
    emails_saved: int = 0
    forms_found: int = 0
    phones_saved: int = 0
    errors: list[str] = field(default_factory=list)


class ContactDiscovery:
    def __init__(self, check_mx: bool = True):
        self.check_mx = check_mx
        self.extractor = ContactExtractor()

    def process_company(self, company_id: int, job_url: str | None = None,
                        report: ContactDiscoveryReport | None = None) -> ContactDiscoveryReport:
        report = report or ContactDiscoveryReport()
        company = company_repo.get(company_id)
        if not company:
            return report
        report.companies_processed += 1

        website = company["website"]
        if not website:
            website = find_company_website(
                company["name"], company["domain"], job_url)
            if website:
                company_repo.update(company_id, website=website)
                existing_domain = company["domain"] or domain_from_url(website)
                if existing_domain:
                    company_repo.update(company_id, domain=existing_domain)

        if not website and not job_url:
            report.errors.append(f"{company['name']}: site não identificado.")
            return report

        # 1) varre site oficial
        site_result = self.extractor.scan_site(website) if website else None
        emails = list(site_result.emails) if site_result else []
        forms = list(site_result.form_urls) if site_result else []
        phones = list(site_result.phones) if site_result else []

        # 2) varre a pagina da vaga (se disponivel) procurando contato
        if job_url:
            page = self.extractor.scan_page(job_url)
            emails.extend(page.emails)
            phones.extend(page.phones)
            forms.extend([f for f in page.form_urls if f not in forms])

        domain = domain_from_url(website) if website else (company["domain"] or "")
        seen: set[str] = set()
        for ec in emails:
            email = ec.email
            if not email or email in seen:
                continue
            seen.add(email)
            # ignora emails de terceiros/agregadores e imagens
            if any(x in email for x in ["sentry", "wixpress", "example.com", "domain.com",
                                        "email.com", "@2x", "png", "jpg", "gstatic",
                                        "googlemail", "cloudflare"]):
                continue
            report.emails_found += 1
            res = validate_email(email, check_mx=self.check_mx, origin_confirmed=True)
            from datetime import datetime
            cid = contact_repo.add(
                company_id=company_id,
                email=email,
                domain=res.domain or domain,
                source_url=ec.source_url,
                category=res.category,
                status=res.status.value,
            )
            if cid:
                contact_repo.update(
                    cid,
                    mx_ok=1 if res.mx_ok else 0,
                    syntax_ok=1 if res.syntax_ok else 0,
                    checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                report.emails_saved += 1

        for form in forms[:5]:
            contact_repo.add(company_id=company_id, form_url=form,
                             source_url=form, category="recruitment",
                             status=EmailStatus.FORM_AVAILABLE.value)
            report.forms_found += 1

        seen_phones: set[str] = set()
        for pc in phones:
            if not pc.phone or pc.phone in seen_phones:
                continue
            seen_phones.add(pc.phone)
            cid = contact_repo.add(
                company_id=company_id,
                phone=pc.phone,
                domain=domain,
                source_url=pc.source_url,
                category="recruitment",
                status=EmailStatus.PHONE_FOUND.value,
            )
            if cid:
                report.phones_saved += 1

        mark_duplicates()
        return report

    def find_for_job(self, job_id: int) -> ContactDiscoveryReport:
        job = job_repo.get(job_id)
        report = ContactDiscoveryReport()
        if not job:
            return report
        company_id = job["company_id"]
        if not company_id:
            # cria empresa a partir do dominio da vaga (sem inventar dados)
            from .website_finder import domain_from_url as _dfu
            dom = _dfu(job["url"])
            name = job["company_name"] if "company_name" in job.keys() else None
            if not name:
                name = dom or "Empresa não identificada"
            company_id = company_repo.get_or_create(name, domain=dom or None)
            job_repo.link_company(job_id, company_id)
        return self.process_company(company_id, job_url=job["url"], report=report)


contact_discovery = ContactDiscovery()
