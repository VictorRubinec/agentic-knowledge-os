#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/curador_temas_scraper.py
=============================================================================
CURADOR E SCRAPER AUTÔNOMO DE TEMAS DE TECNOLOGIA E IA (Knowledge OS)
Monitora continuamente fontes técnicas globais (Hacker News, GitHub Trending,
Blogs de Engenharia) para identificar arquiteturas emergentes, bibliotecas e
padrões de software de alto valor, alimentando automaticamente a fila do Hermes.

Pilares de Triagem (Knowledge OS & UNIPDS):
  1. Engenharia de Software com IA & Multi-Agente (FastMCP, Roteamento, LLMOps)
  2. Bancos de Dados, RAG & Vetores (Neon Lakebase, pgvector, HNSW, DBX)
  3. DevSecOps, Kubernetes & Resiliência (Aikido, K8s, Gatekeepers, CI/CD)
  4. SaaS B2B & Ferramentas para Desenvolvedores (TokenGuard AI, Gateways, Proxies)

Comandos CLI:
  python scripts/curador_temas_scraper.py --scan
  python scripts/curador_temas_scraper.py --scan --auto-enqueue --limit 3
  python scripts/curador_temas_scraper.py --daemon --interval 3600
=============================================================================
"""

import sys
import os
import re
import json
import time
import argparse
import datetime
import urllib.request
import urllib.parse
from pathlib import Path

# Suporte UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
META_DIR = ROOT_DIR / "00-meta"
QUEUE_FILE = META_DIR / "hermes_tasks.json"
CACHE_FILE = META_DIR / ".curador_cache.json"
CRONOGRAMA_FILE = META_DIR / "cronograma_pesquisas.json"


def carregar_cronograma() -> dict:
    if not CRONOGRAMA_FILE.exists():
        return {}
    try:
        with open(CRONOGRAMA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# Mapeamento oficial dos 6 eixos temáticos por dia da semana
DIAS_MAPA = {
    0: "monday",     # Segunda
    1: "tuesday",    # Terça
    2: "wednesday",  # Quarta
    3: "thursday",   # Quinta
    4: "friday",     # Sexta
    5: "saturday",   # Sábado
    6: "sunday"      # Domingo
}

DIA_NOME_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

# Palavras-chave positivas com pesos de relevância
PILARES_PESOS = {
    "agent": 25,
    "multi-agent": 35,
    "mcp": 30,
    "model context protocol": 35,
    "rag": 25,
    "pgvector": 30,
    "neon": 30,
    "lakebase": 30,
    "vector": 20,
    "hnsw": 25,
    "embeddings": 20,
    "kubernetes": 25,
    "k8s": 25,
    "devsecops": 30,
    "security": 20,
    "sast": 25,
    "sca": 25,
    "rate limiting": 25,
    "proxy": 20,
    "token": 15,
    "fastapi": 20,
    "playwright": 20,
    "postgresql": 20,
    "postgres": 20,
    "saas": 25,
    "b2b": 25,
    "devtools": 25,
    "systems design": 30,
    "concurrency": 25,
    "rpg": 30,
    "ordem paranormal": 35
}

# Filtro Anti-Slop / Blacklist
TERMOS_IGNORADOS = [
    "crypto", "bitcoin", "nft", "airdrop", "giveaway", "elon musk",
    "meme", "drama", "unpopular opinion", "clickbait", "hire me",
    "funding round", "valuation", "seed round", "layoffs"
]


def carregar_cache():
    if not CACHE_FILE.exists():
        return {"processed_urls": [], "processed_titles": []}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"processed_urls": [], "processed_titles": []}


def salvar_cache(cache):
    META_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def request_json(url: str, timeout: int = 10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KnowledgeOS-TechScout/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return None


def fetch_hacker_news_trends():
    """Rastreia discussões técnicas qualificadas via Algolia API do Hacker News."""
    print("   [1/3] Varrendo Hacker News (discussões técnicas em alta)...")
    queries = ["AI agent", "MCP protocol", "Postgres vector", "DevSecOps", "Kubernetes"]
    descobertas = []

    for q in queries:
        url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(q)}&tags=story&hitsPerPage=6"
        data = request_json(url)
        if not data:
            continue
        for hit in data.get("hits", []):
            titulo = hit.get("title") or ""
            link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            pontos = hit.get("points") or 0
            comentarios = hit.get("num_comments") or 0
            if titulo and pontos >= 5:
                descobertas.append({
                    "origem": "Hacker News",
                    "titulo": titulo,
                    "url": link,
                    "engajamento": f"{pontos} pts, {comentarios} comments",
                    "raw_text": f"{titulo} {hit.get('story_text', '')}"
                })
        time.sleep(0.2)
    return descobertas


def fetch_github_trending():
    """Rastreia repositórios emergentes com foco em ferramentas de IA e infraestrutura."""
    print("   [2/3] Varrendo GitHub Trending (repositórios de alta tração)...")
    topics = ["mcp", "ai-agents", "pgvector", "devsecops"]
    descobertas = []

    for t in topics:
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(t)}+stars:>50&sort=updated&order=desc&per_page=5"
        data = request_json(url)
        if not data:
            continue
        for repo in data.get("items", []):
            nome = repo.get("full_name") or ""
            desc = repo.get("description") or ""
            stars = repo.get("stargazers_count") or 0
            html_url = repo.get("html_url") or ""
            if nome:
                descobertas.append({
                    "origem": "GitHub Trending",
                    "titulo": f"{nome}: {desc[:80]}",
                    "url": html_url,
                    "engajamento": f"⭐ {stars} stars",
                    "raw_text": f"{nome} {desc} {' '.join(repo.get('topics', []))}"
                })
        time.sleep(0.3)
    return descobertas


def avaliar_relevancia(item: dict) -> int:
    """Calcula pontuação de relevância e aplica filtros anti-slop."""
    texto = (item["titulo"] + " " + item.get("raw_text", "")).lower()

    # Filtro anti-slop estrito
    for banido in TERMOS_IGNORADOS:
        if banido in texto:
            return 0

    score = 0
    for termo, peso in PILARES_PESOS.items():
        if re.search(r"\b" + re.escape(termo) + r"\b", texto):
            score += peso

    # Bônus por engajamento
    if "stars" in item.get("engajamento", ""):
        score += 15
    elif "pts" in item.get("engajamento", ""):
        score += 10

    return min(score, 100)


def classificar_tema(item: dict, cronograma: dict) -> tuple[str, str, str]:
    """
    Classifica o item em um dos 6 temas editoriais do cronograma.
    Retorna: (tema_id, dia_nome, dia_chave)
    """
    texto = (item.get("titulo", "") + " " + item.get("raw_text", "")).lower()

    # 1. Sábado: RPG & Ordem Paranormal
    if any(k in texto for k in ["rpg", "ttrpg", "ordem paranormal", "game design", "ficha", "tormenta"]):
        return "rpg", "Sábado", "saturday"

    # 2. Terça: Automações & Pipelines
    if any(k in texto for k in ["automation", "pipeline", "workflow", "n8n", "crawler", "scraper", "webhook", "orchestrat"]):
        return "automacoes", "Terça-feira", "tuesday"

    # 3. Sexta: Tendências de Mercado & Negócios
    if any(k in texto for k in ["saas", "b2b", "pricing", "monetiz", "business", "startup", "revenue"]):
        return "tendencias_negocios", "Sexta-feira", "friday"

    # 4. Quinta: Evolução de Conhecimento & Engenharia
    if any(k in texto for k in ["architecture", "systems design", "internals", "concurrency", "algorithm", "data structure", "database internal", "pos-ia"]):
        return "evolucao_conhecimento", "Quinta-feira", "thursday"

    # 5. Quarta: Repositórios Famosos / Trending
    if "stars" in item.get("engajamento", "") or "github" in item.get("origem", "").lower():
        return "repositorios_famosos", "Quarta-feira", "wednesday"

    # 6. Segunda: Notícias Tech & Lançamentos da Indústria (Default)
    return "noticias_tech", "Segunda-feira", "monday"


def calcular_proximo_slot(dia_chave: str, cronograma: dict, fila_tasks: list) -> str:
    """
    Calcula a data e hora ISO do próximo slot vago (08:30 ou 19:30)
    correspondente ao dia da semana alvo, garantindo no máximo 2 tarefas por dia.
    """
    target_weekday = DIA_NOME_TO_WEEKDAY.get(dia_chave, 0)
    slots = cronograma.get("slots_horario", ["08:30", "19:30"]) if cronograma else ["08:30", "19:30"]

    agora = datetime.datetime.now()
    dias_para_frente = (target_weekday - agora.weekday()) % 7

    data_base = (agora + datetime.timedelta(days=dias_para_frente)).date()

    # Coleta todos os slots já ocupados na fila
    slots_ocupados = set()
    for t in fila_tasks:
        sched = t.get("scheduled_for")
        if sched and t.get("status") in ["pending", "running"]:
            slots_ocupados.add(sched[:16])  # formato "YYYY-MM-DDTHH:MM"

    # Varre as próximas 4 semanas para encontrar o primeiro slot livre
    for semana in range(4):
        dia_alvo = data_base + datetime.timedelta(days=semana * 7)
        for slot_hora in slots:
            hora, minuto = map(int, slot_hora.split(":"))
            dt_slot = datetime.datetime(dia_alvo.year, dia_alvo.month, dia_alvo.day, hora, minuto, 0)

            # Se for hoje e o horário já passou, não aloca
            if dt_slot <= agora:
                continue

            iso_key = dt_slot.strftime("%Y-%m-%dT%H:%M")
            if iso_key not in slots_ocupados:
                return dt_slot.isoformat()

    # Fallback se lotado: aloca 4 semanas à frente
    dia_fb = data_base + datetime.timedelta(days=28)
    return datetime.datetime(dia_fb.year, dia_fb.month, dia_fb.day, 8, 30, 0).isoformat()


def formular_especificacao_hermes(item: dict, cronograma: dict, fila_tasks: list) -> dict:
    """Transforma uma descoberta em especificação executiva do Hermes com agendamento editorial."""
    titulo_raw = item["titulo"]
    url = item["url"]

    # Limpar título e classificar
    titulo_limpo = re.sub(r"^(Show HN:|Ask HN:|GitHub - )", "", titulo_raw).strip()
    tema_id, dia_nome, dia_chave = classificar_tema(item, cronograma)
    scheduled_for = calcular_proximo_slot(dia_chave, cronograma, fila_tasks)

    prompt_pesquisa = (
        f"Investigação aprofundada baseada na descoberta: '{titulo_limpo}' (Fonte: {url}). "
        f"Eixo Temático: {dia_nome} — {tema_id}. "
        f"Mapear a arquitetura técnica de referência, comparar benchmarks quantitativos de latência e custo, "
        f"apresentar implementação mínima viável executável, identificar edge cases e falhas ocultas em produção, "
        f"e estruturar plano prático de aplicação no ecossistema Knowledge OS."
    )

    prioridade = "alta" if item["score"] >= 65 else "media"

    return {
        "titulo": f"Análise Técnica: {titulo_limpo[:70]}",
        "prompt": prompt_pesquisa,
        "tipo": "pesquisa",
        "prioridade": prioridade,
        "tema_id": tema_id,
        "dia_nome": dia_nome,
        "scheduled_for": scheduled_for,
        "score": item["score"],
        "url_origem": url,
        "engajamento": item.get("engajamento", "")
    }


def ja_pesquisado_ou_enfileirado(titulo: str) -> bool:
    slug = slugify(titulo)
    # 1. Checar fila atual
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                fila = json.load(f)
                for t in fila.get("tasks", []):
                    if slugify(t.get("titulo", "")) == slug:
                        return True
        except Exception:
            pass

    # 2. Checar arquivos já gerados em projetos/hermes/
    hermes_dir = ROOT_DIR / "projetos" / "hermes"
    if hermes_dir.exists():
        for f in hermes_dir.glob("*.html"):
            if slug in f.stem:
                return True

    return False


def executar_varredura(auto_enqueue: bool = False, limit: int = 3):
    print("\n" + "=" * 80)
    print("🌐 INICIALIZANDO CURADOR E SCRAPER DE ASSUNTOS (Knowledge OS)")
    print("=" * 80)

    cache = carregar_cache()
    candidatos = []

    # 1. Scraping Hacker News
    hn_items = fetch_hacker_news_trends()
    # 2. Scraping GitHub Trending
    gh_items = fetch_github_trending()

    todos = hn_items + gh_items
    print(f"   [3/3] Triando e pontuando {len(todos)} itens brutos coletados...")

    for item in todos:
        if item["url"] in cache.get("processed_urls", []):
            continue
        score = avaliar_relevancia(item)
        if score >= 35:
            item["score"] = score
            candidatos.append(item)

    # Ordenar por score de relevância decrescente
    candidatos.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "=" * 80)
    print(f"{'SCORE':<8} | {'ORIGEM':<15} | {'ENGAJAMENTO':<18} | {'TÍTULO'}")
    print("-" * 80)

    selecionados = []
    urls_vistas_nesta_execucao = set()
    for c in candidatos:
        if c["url"] in urls_vistas_nesta_execucao or ja_pesquisado_ou_enfileirado(c["titulo"]):
            continue
        urls_vistas_nesta_execucao.add(c["url"])
        selecionados.append(c)
        print(f"{c['score']:<8} | {c['origem']:<15} | {c['engajamento'][:16]:<18} | {c['titulo'][:36]}")
        if len(selecionados) >= limit:
            break

    print("=" * 80 + "\n")

    if not selecionados:
        print("ℹ️ Nenhum novo tema com relevância superior ao corte encontrado no momento.")
        return []

    if auto_enqueue:
        print(f"🚀 Enfileirando temas com agendamento editorial no Hermes:")
        from hermes_agent import enfileirar_tarefa, carregar_fila
        cronograma = carregar_cronograma()

        for sel in selecionados:
            fila_atual = carregar_fila().get("tasks", [])
            spec = formular_especificacao_hermes(sel, cronograma, fila_atual)
            enfileirar_tarefa(
                titulo=spec["titulo"],
                prompt=spec["prompt"],
                tipo=spec["tipo"],
                prioridade=spec["prioridade"],
                scheduled_for=spec["scheduled_for"],
                tema_id=spec["tema_id"],
                dia_nome=spec["dia_nome"]
            )
            cache.setdefault("processed_urls", []).append(sel["url"])
            cache.setdefault("processed_titles", []).append(sel["titulo"])

        salvar_cache(cache)
        print("\n✨ Tarefas agendadas com sucesso no calendário editorial do Hermes!")
        print("Execute 'python scripts/hermes_agent.py --list' para auditar a grade semanal.\n")

    return selecionados


def run_daemon_loop(interval: int = 3600, limit_per_run: int = 2):
    print(f"[Curador Daemon] Ativado. Intervalo de checagem: {interval}s ({interval//60} min). Pressione Ctrl+C para parar.")
    try:
        while True:
            executar_varredura(auto_enqueue=True, limit=limit_per_run)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[Curador Daemon] Encerrado com segurança.")


def main():
    parser = argparse.ArgumentParser(description="Curador e Scraper Autônomo de Temas de Tecnologia (Knowledge OS)")
    parser.add_argument("--scan", action="store_true", help="Executar varredura e triagem de temas técnicos")
    parser.add_argument("--auto-enqueue", action="store_true", help="Enfileirar automaticamente os melhores temas no Hermes")
    parser.add_argument("--limit", type=int, default=3, help="Número máximo de temas a selecionar (default: 3)")
    parser.add_argument("--daemon", action="store_true", help="Executar em loop contínuo de vigilância técnica")
    parser.add_argument("--interval", type=int, default=3600, help="Intervalo em segundos para o modo daemon")

    args = parser.parse_args()

    if args.daemon:
        run_daemon_loop(interval=args.interval, limit_per_run=args.limit)
    elif args.scan or len(sys.argv) == 1:
        executar_varredura(auto_enqueue=args.auto_enqueue, limit=args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
