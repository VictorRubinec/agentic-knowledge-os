#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/researcher.py — Pesquisa e Validação Técnica no GitHub e Web
"""

import re
import logging
import requests
from dataclasses import dataclass
from datetime import datetime, timezone

from concurrent.futures import ThreadPoolExecutor
from config import GITHUB_TOKEN
from analyzer import MultimodalReelAnalysis, IdentifiedTechnologyItem, MultimodalAnalysisResult

logger = logging.getLogger("repo_researcher")


@dataclass
class ValidatedTechnologyDossier:
    """Dossiê consolidado e auditado de uma tecnologia individual com métricas reais do GitHub."""
    tech_name: str
    summary: str
    audio_insights: str
    video_insights: str
    install_command: str
    repo_found: bool = False
    repo_name: str = ""
    repo_url: str = ""
    stars: int = 0
    stars_display: str = ""
    forks: int = 0
    language: str = ""
    license_name: str = ""
    last_update_str: str = ""
    is_archived: bool = False
    repo_description: str = ""
    official_website: str = ""
    verdict: str = ""


@dataclass
class ValidatedCollectionDossier:
    """Dossiê unificado do Reel contendo uma ou mais tecnologias auditadas (1:N)."""
    is_collection: bool
    collection_title: str
    collection_overview: str
    items: list[ValidatedTechnologyDossier]

    @property
    def tech_name(self) -> str:
        """Compatibilidade para componentes legados que acessam tech_name diretamente."""
        if self.items:
            return self.collection_title or self.items[0].tech_name
        return self.collection_title or "Tecnologia"


def formatar_stars(num: int) -> str:
    """Formata número de estrelas em formato legível (ex: 8.4k)."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(num)


def formatar_data_relativa(iso_date: str) -> str:
    """Calcula a proximidade da última atualização do commit."""
    if not iso_date:
        return "Desconhecido"
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        agora = datetime.now(timezone.utc)
        dias = (agora - dt).days
        if dias <= 0:
            return "Hoje"
        if dias == 1:
            return "Ontem"
        if dias < 30:
            return f"Há {dias} dias"
        if dias < 365:
            meses = dias // 30
            return f"Há {meses} mês(es)"
        anos = dias // 365
        return f"Há {anos} ano(s)"
    except Exception:
        return iso_date[:10]


def pesquisar_github(candidate: str, fallback_tech: str) -> dict | None:
    """
    Busca o repositório na GitHub API com estratégia resiliente de múltiplas etapas:
    1. Tentativa direta com owner/repo exato.
    2. Se falhar (ex: erro de OCR em 1 letra do autor como kaomai vs kaomei),
       extrai o nome do repositório (ex: 'stickman-video-director') e busca no GitHub por 'repo in:name'.
    3. Busca pelo nome da tecnologia limpo (ex: 'Stickman Video Director' -> 'stickman video director in:name').
    4. Reranking inteligente selecionando correspondência exata de slug e maior contagem de estrelas.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Instagram-Tech-Analyzer-Bot"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Limpeza preliminar: remover protocolo e domínio
    raw_clean = candidate.strip()
    raw_clean = re.sub(r'^https?://github\.com/', '', raw_clean, flags=re.IGNORECASE)
    raw_clean = raw_clean.rstrip('/')

    extracted_owner = ""
    extracted_repo_name = ""

    # 1. Tentativa Direta: se candidato possui formato 'owner/repo'
    match_direct = re.search(r'([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)', raw_clean)
    if match_direct:
        extracted_owner = match_direct.group(1)
        extracted_repo_name = match_direct.group(2)
        url = f"https://api.github.com/repos/{extracted_owner}/{extracted_repo_name}"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                logger.info(f"Repositório encontrado por URL direta: {extracted_owner}/{extracted_repo_name}")
                return resp.json()
            elif resp.status_code == 404:
                logger.info(f"URL direta {extracted_owner}/{extracted_repo_name} retornou 404. Iniciando busca resiliente por slug...")
        except Exception as e:
            logger.warning(f"Erro na requisição direta: {e}")
    else:
        # Se veio apenas o nome do repositório
        extracted_repo_name = raw_clean.strip()

    # Estratégias de consultas de busca ordenadas por precisão
    queries_to_try = []

    # 2. Busca pelo slug do repositório (ignora o autor com erro de OCR)
    if extracted_repo_name:
        clean_repo_slug = re.sub(r'[^A-Za-z0-9_-]', '', extracted_repo_name).lower()
        if clean_repo_slug:
            queries_to_try.append(f"{clean_repo_slug} in:name")

    # 3. Busca pelo nome da tecnologia formatado como slug ou termos
    tech_slug = re.sub(r'[^A-Za-z0-9_-]', ' ', fallback_tech).strip()
    tech_hyphen = re.sub(r'\s+', '-', tech_slug).lower()
    if tech_hyphen and tech_hyphen != extracted_repo_name.lower():
        queries_to_try.append(f"{tech_hyphen} in:name")
    if tech_slug:
        queries_to_try.append(f"{tech_slug} in:name,description")

    # Executa as buscas e avalia o melhor candidato
    for q in queries_to_try:
        search_url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=10"
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    # Reranking inteligente:
                    # 1º prioridade: nome do repositório bate exatamente com o slug esperado
                    target_slug = (extracted_repo_name or tech_hyphen).lower().replace("_", "-")
                    for item in items:
                        item_slug = item.get("name", "").lower().replace("_", "-")
                        if item_slug == target_slug:
                            logger.info(
                                f"Match exato de slug encontrado: {item.get('full_name')} "
                                f"({item.get('stargazers_count')} stars) corrigindo possível erro de OCR do autor ({extracted_owner})."
                            )
                            return item

                    # 2º prioridade: item com mais estrelas que contenha o termo
                    best_item = items[0]
                    logger.info(
                        f"Melhor repositório por relevância: {best_item.get('full_name')} "
                        f"({best_item.get('stargazers_count')} stars)"
                    )
                    return best_item
        except Exception as e:
            logger.warning(f"Erro ao buscar no GitHub com query '{q}': {e}")

    return None


def auditar_tecnologia_item(item: IdentifiedTechnologyItem) -> ValidatedTechnologyDossier:
    """
    Cruza uma tecnologia individual identificada com dados reais da GitHub REST API.
    Aplica autocorreção inteligente em comandos de instalação caso o OCR tenha divergido do autor real.
    """
    candidato = item.github_candidate or item.tech_name
    gh_data = pesquisar_github(candidato, item.tech_name)

    dossier = ValidatedTechnologyDossier(
        tech_name=item.tech_name,
        summary=item.summary,
        audio_insights=item.audio_highlights,
        video_insights=item.video_highlights,
        install_command=item.install_commands,
        official_website=item.official_url_candidate
    )

    if gh_data:
        dossier.repo_found = True
        official_repo_url = gh_data.get("html_url", "")
        dossier.repo_name = gh_data.get("full_name", "")
        dossier.repo_url = official_repo_url
        dossier.stars = gh_data.get("stargazers_count", 0)
        dossier.stars_display = formatar_stars(dossier.stars)
        dossier.forks = gh_data.get("forks_count", 0)
        dossier.language = gh_data.get("language") or "Geral"
        
        lic = gh_data.get("license")
        dossier.license_name = lic.get("name") or lic.get("spdx_id") if lic else "Não especificada"
        
        pushed_at = gh_data.get("pushed_at") or gh_data.get("updated_at")
        dossier.last_update_str = formatar_data_relativa(pushed_at)
        dossier.is_archived = gh_data.get("archived", False)
        dossier.repo_description = gh_data.get("description") or ""

        # Site oficial ou documentação: se vazio ou se apontava para URL errada, assume o repo oficial
        if not dossier.official_website or "github.com" in dossier.official_website:
            dossier.official_website = gh_data.get("homepage") or official_repo_url

        # Autocorreção do comando de instalação (caso o OCR tenha errado 1 letra do autor)
        if dossier.install_command and candidato and official_repo_url:
            clean_cand = re.sub(r'^https?://github\.com/', '', candidato, flags=re.IGNORECASE).strip('/')
            clean_official = re.sub(r'^https?://github\.com/', '', official_repo_url, flags=re.IGNORECASE).strip('/')
            if clean_cand and clean_official and clean_cand.lower() != clean_official.lower():
                dossier.install_command = re.sub(
                    re.escape(clean_cand),
                    clean_official,
                    dossier.install_command,
                    flags=re.IGNORECASE
                )
                logger.info(f"Comando de instalação autocorrigido de '{clean_cand}' para '{clean_official}'.")

        # Geração do Veredito Técnico
        veredito_partes = []
        if dossier.is_archived:
            veredito_partes.append("⚠️ ATENÇÃO: Repositório arquivado/abandonado pelo mantenedor.")
        elif dossier.stars > 5000:
            veredito_partes.append(f"Projeto de alta maturidade ({dossier.stars_display} stars). Comunidade ativa e adoção ampla.")
        elif dossier.stars > 500:
            veredito_partes.append("Projeto com tração sólida e em crescimento contínuo.")
        else:
            veredito_partes.append("Projeto recente ou de nicho. Recomendado validar estabilidade antes de adotar em produção crítica.")

        if "Ontem" in dossier.last_update_str or "Hoje" in dossier.last_update_str or "dias" in dossier.last_update_str:
            veredito_partes.append("Manutenção muito frequente com commits recentes.")

        dossier.verdict = " ".join(veredito_partes)

    else:
        dossier.verdict = "Repositório GitHub direto não localizado na busca pública. Pode se tratar de uma plataforma SaaS, extensão proprietária ou biblioteca sob outro nome."

    return dossier


def enriquecer_e_validar_analise(analysis: MultimodalReelAnalysis, post_caption: str = "") -> ValidatedCollectionDossier:
    """
    Executa a auditoria concorrente no GitHub para todas as tecnologias identificadas no Reel (1:N).
    Retorna o ValidatedCollectionDossier contendo todos os dossiês auditados.
    """
    itens_analise = analysis.technologies or []
    if not itens_analise and hasattr(analysis, "tech_name"):
        # Fallback de segurança para análise unitária legada
        itens_analise = [
            IdentifiedTechnologyItem(
                tech_name=getattr(analysis, "tech_name", "Tecnologia"),
                github_candidate=getattr(analysis, "github_candidate", ""),
                official_url_candidate=getattr(analysis, "official_url_candidate", ""),
                summary=getattr(analysis, "summary", ""),
                audio_highlights=getattr(analysis, "audio_highlights", ""),
                video_highlights=getattr(analysis, "video_highlights", ""),
                install_commands=getattr(analysis, "install_commands", "")
            )
        ]

    logger.info(f"Iniciando auditoria concorrente no GitHub para {len(itens_analise)} tecnologia(s)...")
    dossiers_auditados = []

    # Auditoria em paralelo com ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(5, len(itens_analise) or 1)) as pool:
        dossiers_auditados = list(pool.map(auditar_tecnologia_item, itens_analise))

    logger.info(f"Auditoria GitHub concluída com sucesso para todas as {len(dossiers_auditados)} tecnologia(s).")

    is_col = analysis.is_collection if hasattr(analysis, "is_collection") else (len(dossiers_auditados) > 1)
    col_title = getattr(analysis, "collection_title", "")
    if not col_title and dossiers_auditados:
        col_title = dossiers_auditados[0].tech_name

    col_overview = getattr(analysis, "collection_overview", "")
    if not col_overview and dossiers_auditados:
        col_overview = dossiers_auditados[0].summary

    return ValidatedCollectionDossier(
        is_collection=is_col,
        collection_title=col_title,
        collection_overview=col_overview,
        items=dossiers_auditados
    )


def enriquecer_e_validar_tecnologia(analysis: MultimodalReelAnalysis | MultimodalAnalysisResult, post_caption: str = ""):
    """
    Adapter retrocompatível: retorna ValidatedCollectionDossier quando há coleção
    ou ValidatedTechnologyDossier para uso unitário legado.
    """
    col = enriquecer_e_validar_analise(analysis, post_caption)
    if not col.is_collection and len(col.items) == 1:
        return col.items[0]
    return col
