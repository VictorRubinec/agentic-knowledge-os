#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projetos/analisador-instagram-telegram/processar_lote_videos.py
Processamento em lote de Reels do Instagram e YouTube Shorts para extração,
auditoria de repositórios no GitHub e consolidação do Catálogo Técnico no Knowledge OS.
"""

import sys
import os
import re
import json
import logging
import argparse
import subprocess
from pathlib import Path
from dataclasses import asdict

# Forçar encoding UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from config import validar_configuracoes, GEMINI_API_KEY
from downloader import baixar_reel_instagram, extrair_url_midia, InstagramPost
from analyzer import analisar_video_multimodal, MultimodalReelAnalysis
from researcher import (
    enriquecer_e_validar_analise,
    ValidatedCollectionDossier,
    ValidatedTechnologyDossier
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("processador_lote")

CACHE_LOTE_FILE = CURRENT_DIR / "cache_lote_videos.json"
CATALOGO_JSON_FILE = REPO_ROOT / "projetos" / "pesquisas" / "catalogo-itens-estudo.json"
CATALOGO_HTML_FILE = REPO_ROOT / "projetos" / "pesquisas" / "catalogo-itens-estudo.html"
NOVO_DOC_SCRIPT = REPO_ROOT / "scripts" / "novo_documento.py"
GERAR_PDF_SCRIPT = REPO_ROOT / "scripts" / "gerar_pdf.py"


def carregar_cache() -> dict:
    if CACHE_LOTE_FILE.exists():
        try:
            with open(CACHE_LOTE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar cache do lote: {e}")
    return {}


def salvar_cache(dados: dict):
    try:
        with open(CACHE_LOTE_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Erro ao salvar cache do lote: {e}")


def carregar_lista_links(arquivo_caminho: Path) -> list[str]:
    if not arquivo_caminho.exists():
        raise FileNotFoundError(f"Arquivo de links não encontrado: {arquivo_caminho}")
    links = []
    with open(arquivo_caminho, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                clean = extrair_url_midia(linha) or linha
                if clean not in links:
                    links.append(clean)
    return links


def formatar_tabela_markdown(itens: list[dict]) -> str:
    md = ["| Tecnologia | Repositório | Stars | Linguagem | Problema que Resolve | Comandos / Instalação |",
          "| :--- | :--- | :---: | :---: | :--- | :--- |"]
    for it in itens:
        repo_link = f"[{it.get('repo_name')}]({it.get('repo_url')})" if it.get("repo_found") and it.get("repo_url") else (it.get("official_website") or "N/D")
        stars = it.get("stars_display") or "-"
        lang = it.get("language") or "-"
        cmd = f"`{it.get('install_command')}`" if it.get("install_command") else "-"
        summary = (it.get("summary") or "").replace("|", "-")
        md.append(f"| **{it.get('tech_name')}** | {repo_link} | {stars} | {lang} | {summary} | {cmd} |")
    return "\n".join(md)


def gerar_conteudo_html_catalogo(todos_os_itens: list[dict], videos_processados: list[dict]) -> str:
    """Gera a estrutura técnica interna em HTML5 para injeção via scripts/novo_documento.py."""
    total_videos = len(videos_processados)
    total_itens = len(todos_os_itens)
    total_repos = sum(1 for it in todos_os_itens if it.get("repo_found"))
    
    # Montar linhas da tabela
    linhas_tabela = []
    for it in todos_os_itens:
        repo_html = f'<a href="{it.get("repo_url")}" target="_blank" class="font-medium text-sky-600 hover:underline">{it.get("repo_name")}</a>' if it.get("repo_found") else f'<span class="text-slate-400">{it.get("official_website") or "Proprietário / SaaS"}</span>'
        stars_badge = f'<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">⭐ {it.get("stars_display")}</span>' if it.get("stars") else '<span class="text-xs text-slate-400">-</span>'
        cmd_html = f'<code class="px-1.5 py-0.5 bg-slate-100 text-slate-800 rounded text-xs font-mono">{it.get("install_command")}</code>' if it.get("install_command") else '<span class="text-xs text-slate-400">-</span>'
        origem_html = f'<a href="{it.get("source_url")}" target="_blank" class="text-xs text-indigo-500 hover:underline">Vídeo Ref</a>' if it.get("source_url") else '-'
        
        linhas_tabela.append(f"""
        <tr class="hover:bg-slate-50 border-b border-slate-100 transition-colors">
          <td class="py-3 px-4 font-semibold text-slate-900">{it.get("tech_name")}</td>
          <td class="py-3 px-4">{repo_html}</td>
          <td class="py-3 px-4 text-center">{stars_badge}</td>
          <td class="py-3 px-4 text-xs font-medium text-slate-600">{it.get("language") or "Geral"}</td>
          <td class="py-3 px-4 text-sm text-slate-600 max-w-md">{it.get("summary")}</td>
          <td class="py-3 px-4">{cmd_html}</td>
          <td class="py-3 px-4 text-center">{origem_html}</td>
        </tr>
        """)
    tabela_corpo = "\n".join(linhas_tabela)

    # Montar cards detalhados
    cards_html = []
    for idx, it in enumerate(todos_os_itens, start=1):
        repo_info = f'<a href="{it.get("repo_url")}" target="_blank" class="text-sky-600 font-mono text-sm hover:underline">{it.get("repo_name")}</a> ({it.get("stars_display")} stars)' if it.get("repo_found") else "Repositório não indexado publicamente"
        cards_html.append(f"""
        <div class="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:border-sky-300 transition-colors">
          <div class="flex items-start justify-between gap-4 mb-3">
            <div>
              <span class="text-xs font-bold uppercase tracking-wider text-sky-600">Item #{idx:02d}</span>
              <h3 class="text-lg font-bold text-slate-900">{it.get("tech_name")}</h3>
              <p class="text-xs text-slate-500">{repo_info}</p>
            </div>
            <div class="text-right">
              <span class="inline-block px-2.5 py-1 text-xs font-medium rounded-full bg-slate-100 text-slate-700">{it.get("language") or "Framework / Tool"}</span>
            </div>
          </div>
          <p class="text-sm text-slate-700 mb-4">{it.get("summary")}</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs mb-3">
            <div class="bg-slate-50 p-3 rounded border border-slate-100">
              <span class="font-semibold text-slate-700 block mb-1">🎧 Destaques do Áudio / Fala:</span>
              <p class="text-slate-600">{it.get("audio_insights") or "Não detalhado na locução."}</p>
            </div>
            <div class="bg-slate-50 p-3 rounded border border-slate-100">
              <span class="font-semibold text-slate-700 block mb-1">📺 Destaques Visuais / Telas:</span>
              <p class="text-slate-600">{it.get("video_insights") or "Código ou interface exibida no vídeo."}</p>
            </div>
          </div>
          
          {f'<div class="mt-2 bg-slate-900 text-slate-100 p-2.5 rounded font-mono text-xs flex justify-between items-center"><span>{it.get("install_command")}</span><span class="text-slate-400 text-[10px]">EXEC / CLI</span></div>' if it.get("install_command") else ''}
          <div class="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500 flex justify-between items-center">
            <span><strong>Veredito:</strong> {it.get("verdict")}</span>
            {f'<a href="{it.get("source_url")}" target="_blank" class="text-indigo-600 font-medium hover:underline">Ver Vídeo Original &rarr;</a>' if it.get("source_url") else ''}
          </div>
        </div>
        """)
    cards_corpo = "\n".join(cards_html)

    html = f"""
    <!-- Seção 1: Resumo Executivo da Rodada -->
    <section class="mb-10">
      <h2 class="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">1. Resumo Executivo da Extração</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-sky-50 border border-sky-200 rounded-lg p-4">
          <span class="text-xs font-semibold text-sky-800 uppercase tracking-wider block">Vídeos Analisados</span>
          <span class="text-3xl font-extrabold text-sky-950 mt-1 block">{total_videos}</span>
          <span class="text-xs text-sky-700 mt-1 block">Instagram Reels & YouTube Shorts</span>
        </div>
        <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
          <span class="text-xs font-semibold text-emerald-800 uppercase tracking-wider block">Tecnologias Mapeadas</span>
          <span class="text-3xl font-extrabold text-emerald-950 mt-1 block">{total_itens}</span>
          <span class="text-xs text-emerald-700 mt-1 block">Itens catalogados para estudo e PoC</span>
        </div>
        <div class="bg-violet-50 border border-violet-200 rounded-lg p-4">
          <span class="text-xs font-semibold text-violet-800 uppercase tracking-wider block">Repositórios Auditados</span>
          <span class="text-3xl font-extrabold text-violet-950 mt-1 block">{total_repos}</span>
          <span class="text-xs text-violet-700 mt-1 block">Com métricas do GitHub e comandos CLI</span>
        </div>
      </div>
      <div class="p-4 bg-slate-50 border-l-4 border-sky-600 rounded-r text-sm text-slate-700">
        Este dossiê consolida a extração de inteligência multimodal executada pelo motor Knowledge OS. 
        Cada vídeo passou por transcrição de áudio, OCR de código em tela e busca automatizada na API do GitHub para validar se as ferramentas mencionadas são repositórios open-source ativos, bibliotecas ou produtos de mercado.
      </div>
    </section>

    <!-- Seção 2: Tabela Consolidada de Tecnologias -->
    <section class="mb-10">
      <h2 class="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">2. Catálogo Comparativo Geral</h2>
      <div class="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="bg-slate-100 text-slate-700 text-xs font-bold uppercase tracking-wider border-b border-slate-200">
              <th class="py-3 px-4">Tecnologia</th>
              <th class="py-3 px-4">Repositório GitHub</th>
              <th class="py-3 px-4 text-center">Stars</th>
              <th class="py-3 px-4">Linguagem</th>
              <th class="py-3 px-4">Problema que Resolve</th>
              <th class="py-3 px-4">Comando / Instalação</th>
              <th class="py-3 px-4 text-center">Origem</th>
            </tr>
          </thead>
          <tbody>
            {tabela_corpo}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Seção 3: Fichas Detalhadas das Tecnologias -->
    <section class="mb-10">
      <h2 class="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">3. Fichas Técnicas para Projetos e Estudos</h2>
      <div class="space-y-4">
        {cards_corpo}
      </div>
    </section>
    """
    return html


def main():
    parser = argparse.ArgumentParser(description="Processador em Lote de Reels/Shorts para Catálogo de Tecnologias")
    parser.add_argument("--arquivo", default=str(CURRENT_DIR / "links_estudo.txt"), help="Arquivo contendo a lista de links")
    parser.add_argument("--limite", type=int, default=0, help="Limite máximo de vídeos a processar (0 para todos)")
    parser.add_argument("--forcar", action="store_true", help="Ignorar cache e forçar reprocessamento de vídeos já analisados")
    args = parser.parse_args()

    ok, msg = validar_configuracoes(precisa_telegram=False)
    if not ok:
        print(f"❌ Erro de Configuração:\n{msg}")
        sys.exit(1)

    arquivo_links = Path(args.arquivo)
    links = carregar_lista_links(arquivo_links)
    if args.limite > 0:
        links = links[:args.limite]

    print(f"\n=======================================================")
    print(f"🚀 INICIANDO PROCESSAMENTO EM LOTE: {len(links)} VÍDEOS")
    print(f"=======================================================\n")

    cache = carregar_cache()
    videos_processados = []
    todos_os_itens = []

    for idx, url in enumerate(links, start=1):
        print(f"\n[{idx}/{len(links)}] Processando: {url}")
        
        # Verificar se já está em cache
        if not args.forcar and url in cache:
            print("   ⚡ Usando resultado em cache para esta URL.")
            video_data = cache[url]
            videos_processados.append(video_data)
            for it in video_data.get("items", []):
                it["source_url"] = url
                todos_os_itens.append(it)
            continue

        post = None
        try:
            print("   ⏳ 1/3 Baixando vídeo com yt-dlp...")
            post = baixar_reel_instagram(url)
            print(f"      ✔ Mídia: {post.video_path.name} ({post.video_path.stat().st_size / 1024 / 1024:.2f} MB)")
            
            print("   ⏳ 2/3 Analisando com Gemini Multimodal...")
            analise = analisar_video_multimodal(post)
            n_techs = len(analise.technologies) if analise.technologies else 1
            print(f"      ✔ Extraídas {n_techs} tecnologia(s) mencionadas.")

            print("   ⏳ 3/3 Auditando e localizando repositórios no GitHub...")
            dossier_col = enriquecer_e_validar_analise(analise, post.caption)

            # Converter para dicionário serializável
            itens_serializados = []
            for it in dossier_col.items:
                it_dict = asdict(it) if hasattr(it, "__dataclass_fields__") else it
                it_dict["source_url"] = url
                itens_serializados.append(it_dict)
                todos_os_itens.append(it_dict)
                print(f"         • {it.tech_name}: {it.repo_url or it.official_website or 'SaaS/Proprietário'} ({it.stars_display} stars)")

            video_record = {
                "url": url,
                "author": post.author,
                "caption": post.caption[:300],
                "is_collection": dossier_col.is_collection,
                "collection_title": dossier_col.collection_title,
                "collection_overview": dossier_col.collection_overview,
                "items": itens_serializados
            }

            videos_processados.append(video_record)
            cache[url] = video_record
            salvar_cache(cache)

        except Exception as e:
            logger.error(f"   ❌ Falha ao processar {url}: {e}")
            cache[url] = {
                "url": url,
                "erro": str(e),
                "items": []
            }
            salvar_cache(cache)
        finally:
            if post:
                post.cleanup()

    # Desduplicação inteligente de itens (por nome ou URL do repo)
    itens_unicos = []
    chaves_vistas = set()
    for it in todos_os_itens:
        chave = (it.get("repo_url") or it.get("tech_name") or "").strip().lower()
        if chave and chave not in chaves_vistas:
            chaves_vistas.add(chave)
            itens_unicos.append(it)

    print(f"\n=======================================================")
    print(f"🎉 PROCESSAMENTO CONCLUÍDO!")
    print(f"Total de Vídeos: {len(links)}")
    print(f"Total de Tecnologias Identificadas: {len(itens_unicos)}")
    print(f"=======================================================\n")

    # Salvar JSON estruturado consolidado
    CATALOGO_JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOGO_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "data_extracao": str(Path(__file__).stat().st_mtime),
            "total_videos": len(videos_processados),
            "total_tecnologias": len(itens_unicos),
            "itens": itens_unicos
        }, f, ensure_ascii=False, indent=2)
    print(f"✔ Arquivo JSON consolidado salvo em: {CATALOGO_JSON_FILE}")

    # Gerar Artefato HTML5 no Knowledge OS
    conteudo_html = gerar_conteudo_html_catalogo(itens_unicos, videos_processados)
    temp_conteudo = CURRENT_DIR / "temp_catalogo_conteudo.html"
    with open(temp_conteudo, "w", encoding="utf-8") as f:
        f.write(conteudo_html)

    cmd_novo_doc = [
        sys.executable,
        str(NOVO_DOC_SCRIPT),
        "--titulo", "Catálogo Técnico: Tecnologias e Repositórios Extraídos de Vídeos",
        "--arquivo", str(CATALOGO_HTML_FILE),
        "--preset", "pesquisa-tecnica",
        "--categoria", "Pesquisa e Engenharia",
        "--status", "CONCLUIDO",
        "--tags", "Engenharia,IA,Frontend,GitHub,Automação,Estudos",
        "--conteudo-arquivo", str(temp_conteudo),
        "--force"
    ]
    res_doc = subprocess.run(cmd_novo_doc, capture_output=True, text=True)
    if temp_conteudo.exists():
        temp_conteudo.unlink()

    if res_doc.returncode == 0:
        print(f"✔ Documento HTML5 gerado com sucesso em: {CATALOGO_HTML_FILE}")
        # Compilar PDF A4
        print("⏳ Compilando PDF A4 Corporativo via Playwright Chromium...")
        subprocess.run([sys.executable, str(GERAR_PDF_SCRIPT), str(CATALOGO_HTML_FILE)], capture_output=True, text=True)
        print("✔ PDF compilado com sucesso!")
    else:
        print(f"❌ Falha ao criar documento HTML5: {res_doc.stderr}")


if __name__ == "__main__":
    main()
