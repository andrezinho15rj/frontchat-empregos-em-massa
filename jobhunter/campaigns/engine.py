"""Motor de campanhas de candidatura.

Fluxo controlado e verificavel:
  1) PREPARAR: gera mensagens personalizadas e grava em `applications` (status
     'Preparada'). Nada e enviado nesta etapa.
  2) REVISAR: o usuario revisa/edita na interface.
  3) PROCESSAR: envia apenas os itens aprovados, registrando resultado real do
     provedor. Respeita pausa/cancelamento e intervalo entre envios.

Nunca marca uma candidatura como enviada sem confirmacao do provedor SMTP.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from ..constants import ApplicationStatus
from ..db.repositories import (
    application_repo, campaign_repo, company_repo, contact_repo, job_repo,
    resume_repo,
)
from ..logging_setup import get_logger
from .providers import SmtpProvider
from .templates import build_values, default_apresentacao, render

log = get_logger("campaigns.engine")


@dataclass
class PrepareReport:
    prepared: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    ai_used: bool = False
    ai_unavailable: bool = False


@dataclass
class SendReport:
    sent: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    aborted: bool = False


class CampaignEngine:
    """Preparacao e envio de candidaturas."""

    def prepare(self, campaign_id: int, contact_ids: list[int],
                use_ai: bool = False, ai_min_priority: str = "baixa",
                min_match_score: float | None = None,
                progress=None) -> PrepareReport:
        report = PrepareReport()
        campaign = campaign_repo.get(campaign_id)
        if not campaign:
            report.errors.append("Campanha inexistente.")
            return report
        resume = resume_repo.get(campaign["resume_id"]) if campaign["resume_id"] else \
            resume_repo.active()
        if not resume:
            report.errors.append("Nenhum currículo ativo para esta campanha.")
            return report
        resume_text = resume["content_text"] or ""

        analyzer = None
        if use_ai:
            from ..ai.analyzer import AIAnalyzer
            analyzer = AIAnalyzer()
            if not analyzer.is_available():
                report.ai_unavailable = True
                report.errors.append(
                    "IA solicitada, mas não está configurada. "
                    "A personalização usará apenas os modelos.")
                analyzer = None
            else:
                report.ai_used = True

        language = campaign["language"] or "pt"
        candidate = resume["name"] or "Candidato(a)"

        total = len(contact_ids)
        for idx, cid in enumerate(contact_ids):
            if progress:
                progress(idx + 1, total)
            contact = contact_repo.get(cid)
            if not contact:
                report.skipped += 1
                continue
            email = (contact["email"] or "").strip()
            if not email:
                report.skipped += 1
                continue
            company = company_repo.get(contact["company_id"]) if contact["company_id"] else None
            company_name = company["name"] if company else "sua empresa"
            job = job_repo.get(contact["job_id"]) if contact["job_id"] else None
            job_title = job["title"] if job else "a vaga anunciada"
            area = job["area"] if job else ""
            city = (job["city"] if job and job["city"] else (company["location"] if company else ""))

            if application_repo.already_applied(contact["company_id"] or 0,
                                                contact["job_id"], email):
                report.skipped += 1
                continue

            match_score = None
            match_reason = ""
            apresentacao = default_apresentacao(language)
            subject_tpl = campaign["subject_tpl"] or ""
            body_tpl = campaign["body_tpl"] or ""

            if analyzer and job:
                try:
                    m = analyzer.match(job["title"], job["description"] or "", resume_text)
                    match_score = m.get("score")
                    match_reason = m.get("reason", "")
                    if min_match_score is not None and match_score is not None \
                            and match_score < min_match_score:
                        report.skipped += 1
                        continue
                    if ai_min_priority in ("alta", "media") and m.get("priority"):
                        order = {"alta": 3, "media": 2, "baixa": 1}
                        if order.get(m["priority"], 0) < order.get(ai_min_priority, 0):
                            report.skipped += 1
                            continue
                    pers = analyzer.personalize(company_name, job_title,
                                                resume_text, language)
                    if pers.get("subject"):
                        subject_tpl = pers["subject"]
                    if pers.get("apresentacao"):
                        apresentacao = pers["apresentacao"]
                except Exception as exc:  # pragma: no cover - rede IA
                    report.errors.append(f"IA falhou para {company_name}: {exc}")

            values = build_values(
                company=company_name, title=job_title, candidate=candidate,
                area=area, city=city, apresentacao=apresentacao,
                sender=campaign["from_email"] or "",
            )
            subject = render(subject_tpl, values) if subject_tpl else \
                render("Candidatura para {cargo} — {candidato}", values)
            body = render(body_tpl, values) if body_tpl else ""

            aid = application_repo.add(
                campaign_id=campaign_id,
                company_id=contact["company_id"],
                job_id=contact["job_id"],
                contact_id=cid,
                to_email=email,
                subject=subject,
                body=body,
                resume_id=resume["id"],
                status=ApplicationStatus.PREPARED.value,
                match_score=match_score,
                match_reason=match_reason,
            )
            if aid:
                report.prepared += 1
            else:
                report.skipped += 1

        campaign_repo.update(campaign_id, status="Aguardando revisão")
        log.info("Campanha %s: %d preparadas, %d ignoradas",
                 campaign_id, report.prepared, report.skipped)
        return report

    def send_queue(self, campaign_id: int, provider: SmtpProvider,
                   delay_seconds: float = 5.0, only_application_ids: list[int] | None = None,
                   stop_event: threading.Event | None = None,
                   pause_event: threading.Event | None = None,
                   progress=None) -> SendReport:
        report = SendReport()
        apps = application_repo.list(campaign_id=campaign_id)
        candidates = []
        for a in apps:
            if a["status"] not in (ApplicationStatus.PREPARED.value,
                                   ApplicationStatus.QUEUED.value):
                continue
            if only_application_ids and a["id"] not in only_application_ids:
                continue
            candidates.append(a)

        campaign = campaign_repo.get(campaign_id)
        resume = resume_repo.get(campaign["resume_id"]) if campaign and campaign["resume_id"] else None
        attachments = [resume["file_path"]] if resume and resume["file_path"] else []
        campaign_repo.update(campaign_id, status="Em execução")

        total = len(candidates)
        for idx, app in enumerate(candidates):
            if stop_event and stop_event.is_set():
                report.aborted = True
                break
            while pause_event and pause_event.is_set():
                time.sleep(0.5)
                if stop_event and stop_event.is_set():
                    report.aborted = True
                    break
            if report.aborted:
                break
            if progress:
                progress(idx + 1, total, app["to_email"])

            result = provider.send(
                to_email=app["to_email"],
                subject=app["subject"] or "",
                body=app["body"] or "",
                attachments=attachments,
            )
            if result.success:
                application_repo.update(
                    app["id"], status=ApplicationStatus.SENT.value,
                    sent_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error=None)
                report.sent += 1
            else:
                application_repo.update(
                    app["id"], status=ApplicationStatus.FAILED.value, error=result.error)
                report.failed += 1
                report.errors.append(f"{app['to_email']}: {result.error}")

            if idx < total - 1 and not report.aborted:
                slept = 0.0
                while slept < delay_seconds:
                    if stop_event and stop_event.is_set():
                        report.aborted = True
                        break
                    time.sleep(0.5)
                    slept += 0.5
                if report.aborted:
                    break

        new_status = "Cancelada" if report.aborted else "Concluída"
        campaign_repo.update(campaign_id, status=new_status)
        log.info("Campanha %s finalizada: %d enviadas, %d falhas",
                 campaign_id, report.sent, report.failed)
        return report


campaign_engine = CampaignEngine()
