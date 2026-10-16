#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para regenerar as seções 'Matriz de Categorias e Resumo de Documentos'
e 'Índice de Palavras-Chave e Links Rápidos' do ORGANIZATION.md a partir
do frontmatter e estrutura dos arquivos .mdx.

Utiliza marcadores AUTO-GENERATED para preservar o conteúdo manual do arquivo.
Exibe diff de preview antes de aplicar alterações.
"""

import argparse
import difflib
import os
import re
import sys
from pathlib import Path

# Garante suporte a UTF-8 no terminal Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".agents",
    ".gemini",
    "scratch",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "tests",
    "templates",
    "starter-kit",
    "scripts",
}

MARKER_MATRIX_START = "<!-- AUTO-GENERATED:MATRIX:START -->"
MARKER_MATRIX_END = "<!-- AUTO-GENERATED:MATRIX:END -->"
MARKER_INDEX_START = "<!-- AUTO-GENERATED:INDEX:START -->"
MARKER_INDEX_END = "<!-- AUTO-GENERATED:INDEX:END -->"
# Mantém a saída gerada byte a byte estável frente ao `prettier --write`
PRETTIER_IGNORE_START = "<!-- prettier-ignore-start -->"
PRETTIER_IGNORE_END = "<!-- prettier-ignore-end -->"

CATEGORY_DESCRIPTIONS = {
    "trabalho/join4/produto/tarefas": "Painel de controle, acompanhamento de execução, escopo e histórico vivo de tarefas de Produto.",
    "trabalho/join4/produto/tarefas/anexos/task-005-kpis-gold": "Anexos e consultas SQL de KPIs do Data Lakehouse (TASK-005).",
    "trabalho/join4/produto/consultas-portal": "Auditoria técnica, arquitetura BFF e visão de produto do ConsultasPortal.",
    "trabalho/join4/produto/relatorios": "Relatórios técnicos de engenharia, arquitetura e alinhamento de Produto Join4.",
    "trabalho/join4/produto": "Ferramentas internas e produtos SaaS desenvolvidos pela área de Produto da Join4.",
    "trabalho/join4/clientes/atlantica/automacoes": "Documentações técnicas, arquitetura e dossiês de robôs RPA da Atlântica.",
    "trabalho/join4/clientes/atlantica/erros": "Relatórios técnicos, incidentes e controle de erros da Atlântica.",
    "trabalho/join4/clientes/atlantica": "Suporte, incidentes, automações e reuniões da Atlântica Hotels.",
    "trabalho/join4": "Demandas, tarefas, decisões técnicas e reuniões da Join4.",
    "trabalho/triade/comercial": "Instrumentos jurídicos, formulários de descoberta e protocolos de entrega da Triade.",
    "trabalho/triade/plataforma-interna": "Plataforma unificada de gestão de sprints, documentação MDX e contexto de IA da Triade.",
    "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/apresentacao-slides": "Roteiros de slides e pitch decks comerciais do Somos1 Tattoo Studio.",
    "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio": "Especificações de escopo, propostas comerciais e atas de PO do Somos1.",
    "trabalho/triade/projetos/somos1-tattoo-studio/03-arquitetura-e-tech": "Relatórios de auditoria baseline e engenharia reversa do Somos1.",
    "trabalho/triade/projetos/somos1-tattoo-studio/04-prototipos": "Dossiês visuais de UI/UX e wireframes do Somos1.",
    "trabalho/triade/projetos/somos1-tattoo-studio": "Plataforma oficial Somos1: Agendamento, CRM, Indicações e Mensageria WhatsApp.",
    "trabalho/triade/projetos/exemplo-projeto-tatuagem": "Projeto de referência Triade: Blackthorn Tattoo Studio.",
    "trabalho/triade/projetos": "Soluções comerciais entregues a clientes externos sob a governança da Triade.",
    "trabalho/triade": "Consultoria, posicionamento, estratégia, governança e metodologia da Triade.",
    "trabalho/sites/relatorios": "Relatórios técnicos de Design System e auditoria de CSS (designsys).",
    "trabalho/sites/pessoal/cha-casa-nova/conhecimentos": "Bases de conhecimento técnico, regras, design system e PIX do Chá de Casa Nova.",
    "trabalho/sites/pessoal/cha-casa-nova": "Documento mestre e especificações do Convite Interativo Chá de Casa Nova.",
    "trabalho/sites/pessoal/site-portfolio-pessoal": "Website pessoal destinado a portfólio profissional e canais de contato.",
    "trabalho/sites/pessoal": "Websites pessoais, landing pages e portfólios próprios.",
    "trabalho/sites/trabalhos/amg/pacote-assets-ia/documentos-originais": "Documentos e atas de alinhamento originais do cliente AMG Consulting.",
    "trabalho/sites/trabalhos/amg/prototipos": "Protótipos visuais e wireframes do website AMG.",
    "trabalho/sites/trabalhos/amg": "Site institucional e guia de desenvolvimento por agentes de IA da AMG.",
    "trabalho/sites/trabalhos/site-institucional-cliente": "Website institucional comercial para cliente corporativo.",
    "trabalho/sites/trabalhos": "Websites corporativos e comerciais para clientes externos.",
    "trabalho/sites": "Metodologia mestre, diretrizes, topologia e checklists de websites.",
    "rpg/sistemas/ordem-paranormal/criacao-personagem": "Regras de criação de personagem, classes, trilhas e origens de Ordem Paranormal.",
    "rpg/sistemas/ordem-paranormal/regras": "Mecânicas centrais, combate, perícias, sanidade e interlúdio de Ordem Paranormal v1.3.",
    "rpg/sistemas/ordem-paranormal/habilidades": "Poderes de classe, poderes paranormais e rituais de Ordem Paranormal v1.3.",
    "rpg/sistemas/ordem-paranormal/itens-e-equipamentos": "Patentes, armas, modificações, proteções e itens amaldiçoados de Ordem Paranormal.",
    "rpg/sistemas/ordem-paranormal": "Mapeamento completo do sistema Ordem Paranormal v1.3 e suplementos.",
    "rpg/sistemas/ordem-2/criacao-personagem": "Guia de criação, perfis psicológicos, ocupações e progressão Níveis 1 a 10 de Ordem 2.",
    "rpg/sistemas/ordem-2/regras": "Mecânicas centrais, atributos, perícias, cenas de ação e desafios de acesso de Ordem 2.",
    "rpg/sistemas/ordem-2/itens-e-equipamentos": "Equipamentos forenses, Compêndio C.R.I.S. e armas de Ordem 2.",
    "rpg/sistemas/ordem-2/documentos": "Especificações técnicas e design systems do sistema Ordem 2.",
    "rpg/sistemas/ordem-2/exemplos": "Exemplos práticos e templates de Pontos de Interesse (PDI) para Ordem 2.",
    "rpg/sistemas/ordem-2": "Mapeamento completo do sistema Ordem 2 (Playtest Alpha v1.1 e Homebrews).",
    "rpg/mesas/ordem-2-playtest/ato-1": "Primeira Missão oficial do Playtest de Ordem 2 (A Maldição do Ídolo de Pedra - Ato I).",
    "rpg/mesas/ordem-2-playtest/ato-2": "Segunda Missão oficial do Playtest de Ordem 2 (A Maldição do Ídolo de Pedra - Ato II).",
    "rpg/mesas/ordem-2-playtest": "Campanhas e Atos oficiais de Playtest do Ordem Paranormal 2.",
    "rpg/mesas/estacao-monte-calvario/personagens": "Fichas de personagens e cartas secretas da campanha Estação Monte Calvário.",
    "rpg/mesas/estacao-monte-calvario": "Campanha One-Shot de Terror Analógico para 8 Jogadores (Sinal 104.7 - Estação Monte Calvário).",
    "rpg/mesas": "Campanhas ativas e arquivadas, sessões, lore e NPCs de RPG.",
    "rpg/personagens": "Fichas de personagens próprios e conceitos de jogo.",
    "studio-kustom/01-negocio-e-operacao": "Operação física, maquinário, pesquisa e catálogo da Studio Kustom.",
    "studio-kustom/02-engine-e-arquitetura": "Arquitetura técnica, motores gráficos e infraestrutura do Studio Kustom Engine.",
    "studio-kustom/03-agente-ia-e-governanca": "Operação autônoma por IA, contratos zero-code e governança visual.",
    "studio-kustom": "Projetos, estratégias, marcas e ideias da Studio Kustom.",
    "projetos/automacao-emails": "Engenharia e desenvolvimento da engine RubiMail Serverless.",
    "projetos/automacao-fontes/conhecimentos": "Guias técnicos de APIs de fontes, fontTools, scraping e pipelines.",
    "projetos/automacao-fontes": "Motor FontScout para pesquisa e download de fontes em Python.",
    "projetos/monitor-uptime/conhecimentos": "Guias técnicos de SSL socket, Telegram API, worker e status page.",
    "projetos/monitor-uptime": "Prompt mestre e arquitetura do Monitor de Uptime e Status Page.",
    "projetos/gerador-fichas-ordem-2/conhecimentos": "Bases de conhecimento, anatomia A4, design system e schemas do Gerador de Fichas Ordem 2.",
    "projetos/gerador-fichas-ordem-2": "Planejamento e especificação técnica do Gerador Web de Fichas Ordem 2 (300 DPI A4).",
    "projetos/darkcraft-engine/conhecimentos": "Guias técnicos de automação de vídeo e engines criativas do DarkCraft.",
    "projetos/darkcraft-engine": "Engine e pipelines de produção de vídeos dark e monetização por IA.",
    "projetos/knowledge-os-v2": "Arquitetura, roadmap e especificações da modernização do Knowledge OS v2.0.",
    "projetos/knowledge-studio": "Plataforma de visualização e orquestração de artefatos de conhecimento.",
    "projetos/curriculos": "Dossiês e modelos de currículos profissionais de tecnologia compilados em PDF.",
    "projetos/pesquisas": "Pesquisas técnicas aprofundadas, benchmarks e instrumentos para tomada de decisão.",
    "projetos/pesquisas-noturnas": "Dossiês e relatórios de pesquisa autônoma noturna com IA.",
    "projetos": "Projetos pessoais, estudos e ideias gerais fora do trabalho.",
    "pos-ia/00-visao-geral": "Ementa, cronograma acadêmico e matriz de competências da pós-graduação.",
    "pos-ia/disciplinas/00-ambientacao": "Ambientação, diretrizes institucionais (UNIPDS) e setup de desenvolvimento.",
    "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores": "Fundamentos de IA, Transformers, tokens, amostragem e saídas estruturadas.",
    "pos-ia/disciplinas": "Anotações e cadernos vivos dos módulos da pós-graduação em IA Aplicada.",
    "pos-ia/projetos": "Catálogo de projetos práticos, laboratórios e projeto final (Capstone) da pós-graduação.",
    "pos-ia/blueprints-e-padroes": "Biblioteca de padrões de arquitetura de IA, snippets e templates de integração.",
    "pos-ia": "Pós-graduação em Engenharia de Software com IA Aplicada (UNIPDS).",
    "scripts/hyperframes": "Templates e rotinas de geração de vídeo programático via HyperFrames.",
    "exemplos": "Exemplos de atas, tarefas e documentos padronizados do repositório.",
    "00-meta": "Templates de notas, modelos de websites e diretrizes de governança do repositório.",
}


def parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}
    yaml_str = match.group(1)
    fields = {}
    lines = yaml_str.splitlines()
    current_key = None
    list_items = []

    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue

        if raw.startswith("- ") and current_key:
            list_items.append(raw[2:].strip().strip("\"'"))
            fields[current_key] = list_items
            continue

        kv_match = re.match(r"^([a-zA-Z0-9_-]+)\s*:\s*(.*)$", raw)
        if kv_match:
            key, val = kv_match.groups()
            current_key = key.strip()
            val = val.strip()
            if " #" in val:
                val = val.split(" #")[0].strip()
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                fields[current_key] = items
            elif val == "" or val == "[]":
                list_items = []
                fields[current_key] = []
            else:
                fields[current_key] = val.strip("\"'")
        else:
            current_key = None

    return fields


def parse_html_document(file_path: Path, root_dir: Path) -> dict:
    """Extrai metadados completos de um documento HTML5 compilado."""
    import html as html_lib
    content = file_path.read_text(encoding="utf-8")

    # 1. Título
    m_h1 = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', content)
    if m_h1:
        title = html_lib.unescape(re.sub(r'<[^>]+>', '', m_h1.group(1)).strip())
    else:
        m_title = re.search(r'<title>([\s\S]*?)</title>', content)
        if m_title:
            raw_title = re.sub(r' — (?:Documentação Técnica|Livro de Regras).*', '', m_title.group(1))
            title = html_lib.unescape(re.sub(r'<[^>]+>', '', raw_title).strip())
        else:
            title = file_path.stem.replace('-', ' ').title()

    # 2. Categoria e diretório
    dir_rel = file_path.parent.relative_to(root_dir).as_posix()

    # 3. Status
    m_status = re.search(r'<header[^>]*>[\s\S]*?<span class="px-2\.5 py-0\.5 rounded-full text-xs font-medium[^"]*">\s*([A-Za-zÀ-ÿ0-9_-]+)\s*</span>', content)
    status = m_status.group(1).lower() if m_status else "ativo"

    # 4. Tags
    tags = []
    m_badges = re.search(r'<div class="flex flex-wrap gap-2 my-3">([\s\S]*?)</div>', content)
    if m_badges:
        tags = [html_lib.unescape(x.strip()) for x in re.findall(r'<span[^>]*>([^<]+)</span>', m_badges.group(1))]

    # 5. Resumo
    summary = ""
    m_vg = re.search(r'<h2[^>]*>.*?(?:Visão Geral|Resumo|Objetivo).*?</h2>[\s\S]{0,500}?<p[^>]*>([\s\S]*?)</p>', content, re.IGNORECASE)
    if m_vg:
        summary = m_vg.group(1)
    else:
        m_call = re.search(r'<div class="callout[^"]*">[\s\S]{0,300}?<p[^>]*>([\s\S]*?)</p>', content)
        if m_call:
            summary = m_call.group(1)
        else:
            m_main = re.search(r'<p[^>]*>([\s\S]*?)</p>', content)
            if m_main:
                summary = m_main.group(1)

    summary = html_lib.unescape(re.sub(r'<[^>]+>', '', summary).strip())
    summary = re.sub(r'\s+', ' ', summary)
    if len(summary) > 160:
        summary = summary[:157] + '...'
    if not summary:
        summary = "Documento técnico e diretrizes de projeto."

    return {
        "path": file_path.relative_to(root_dir).as_posix(),
        "filename": file_path.name,
        "title": title,
        "category": dir_rel,
        "tags": tags,
        "status": status,
        "summary": summary,
        "dir": dir_rel,
    }


def extract_summary(content: str) -> str:
    """Extrai uma breve descrição do documento a partir da seção de Visão Geral."""
    # Remove frontmatter
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
    
    # Procura seção de visão geral ou primeiro parágrafo relevante
    vg_match = re.search(r"^##\s+.*(?:Visão Geral|Resumo|Objetivo).*?\n\n?(.*?)(?:\n\n|\n##|\Z)", body, re.MULTILINE | re.IGNORECASE | re.DOTALL)
    if vg_match:
        text = vg_match.group(1).strip()
        # Remove tags JSX, Markdown links e formatações pesadas
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        first_line = text.split("\n")[0].strip()
        if len(first_line) > 160:
            first_line = first_line[:157] + "..."
        if first_line:
            return first_line

    # Fallback: primeira linha de texto significativa
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "import ", "<", "-", "*", ">", "```", "|")):
            if len(line) > 160:
                line = line[:157] + "..."
            return line

    return "Documento técnico e diretrizes de projeto."


def collect_mdx_metadata(root_dir: Path):
    """Coleta metadados de documentos do repositório (priorizando .html, com fallback a .mdx)."""
    docs = []
    seen_bases = set()

    # Passagem 1: Documentos HTML
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".html"):
                file_path = Path(root) / file
                base_key = (file_path.parent.relative_to(root_dir).as_posix(), file_path.stem)
                try:
                    doc_data = parse_html_document(file_path, root_dir)
                    docs.append(doc_data)
                    seen_bases.add(base_key)
                except Exception as e:
                    print(f"⚠️ Aviso: falha ao processar {file_path}: {e}")
                    continue

    # Passagem 2: Documentos .mdx residuais sem versão HTML
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".mdx"):
                file_path = Path(root) / file
                base_key = (file_path.parent.relative_to(root_dir).as_posix(), file_path.stem)
                if base_key in seen_bases:
                    continue
                rel_path = file_path.relative_to(root_dir).as_posix()
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception:
                    continue

                fm = parse_frontmatter(content)
                title = fm.get("title") or file.replace(".mdx", "").replace("-", " ").title()
                category = fm.get("category") or file_path.parent.relative_to(root_dir).as_posix()
                tags = fm.get("tags") or []
                status = fm.get("status") or "ativo"
                summary = extract_summary(content)

                docs.append({
                    "path": rel_path,
                    "filename": file,
                    "title": title,
                    "category": category,
                    "tags": tags,
                    "status": status,
                    "summary": summary,
                    "dir": file_path.parent.relative_to(root_dir).as_posix(),
                })
    return docs


def generate_matrix_section(docs):
    """Gera a tabela da Matriz de Categorias e Resumo de Documentos."""
    # Agrupa documentos por diretório / categoria
    categories = {}
    for doc in docs:
        cat_key = doc["dir"]
        if cat_key not in categories:
            categories[cat_key] = []
        categories[cat_key].append(doc)

    # Ordena categorias com prioridade lógica: trabalho -> rpg -> studio-kustom -> projetos -> meta
    def category_sort_key(cat):
        order_prefixes = ["trabalho/join4", "trabalho/triade", "trabalho/sites", "trabalho", "pos-ia", "rpg/sistemas", "rpg/mesas", "rpg", "studio-kustom", "projetos", "scripts", "exemplos", "00-meta"]
        for idx, prefix in enumerate(order_prefixes):
            if cat.startswith(prefix):
                return (idx, cat)
        return (99, cat)

    sorted_categories = sorted(categories.keys(), key=category_sort_key)

    lines = [
        "| Categoria / Pasta | Escopo Principal | Documentos Existentes (.html) | Resumo do Assunto |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for cat in sorted_categories:
        cat_docs = sorted(categories[cat], key=lambda d: d["title"])
        scope = CATEGORY_DESCRIPTIONS.get(cat, f"Anotações e documentação de {cat}.")

        docs_links = ", ".join([f"[`{d['filename']}`]({d['path']})" for d in cat_docs])
        
        # Resume os assuntos
        if len(cat_docs) == 1:
            resumo = f"**{cat_docs[0]['title']}**: {cat_docs[0]['summary']}"
        else:
            titles_preview = ", ".join([d['title'] for d in cat_docs[:3]])
            if len(cat_docs) > 3:
                titles_preview += f" e outros {len(cat_docs) - 3} documentos"
            resumo = f"Consolidação de {len(cat_docs)} documentos ({titles_preview})."

        # Escapa barras verticais para tabela markdown
        scope = scope.replace("|", "\\|")
        resumo = resumo.replace("|", "\\|")
        docs_links = docs_links.replace("|", "\\|")

        lines.append(f"| **`{cat}`** | {scope} | {docs_links} | {resumo} |")

    return "\n".join(lines)


def generate_index_section(docs):
    """Gera a lista de índice alfabético de palavras-chave e links rápidos."""
    index_entries = []

    for doc in docs:
        # 1. Entrada pelo título principal
        entry_label = f"{doc['title']}"
        index_entries.append((entry_label, doc['path']))

        # 2. Entradas adicionais por tags significativas
        for tag in doc['tags']:
            if tag and tag not in {"status", "ativo", "mdx", "docs", "projeto", "trabalho", "rpg"}:
                tag_label = f"{doc['title']} ({tag.upper()})"
                index_entries.append((tag_label, doc['path']))

    # Remove duplicados preservando ordem e ordena alfabeticamente
    unique_entries = {}
    for label, path in index_entries:
        if label not in unique_entries:
            unique_entries[label] = path

    sorted_labels = sorted(unique_entries.keys(), key=lambda s: s.lower())

    lines = []
    for label in sorted_labels:
        path = unique_entries[label]
        lines.append(f"- `{label}` -> [`{path}`]({path})")

    return "\n".join(lines)


def update_organization_content(current_content: str, matrix_text: str, index_text: str) -> str:
    """Atualiza o conteúdo de ORGANIZATION.md injetando ou atualizando os marcadores AUTO-GENERATED."""
    new_matrix_block = f"{MARKER_MATRIX_START}\n{PRETTIER_IGNORE_START}\n{matrix_text}\n{PRETTIER_IGNORE_END}\n{MARKER_MATRIX_END}"
    new_index_block = f"{MARKER_INDEX_START}\n{PRETTIER_IGNORE_START}\n{index_text}\n{PRETTIER_IGNORE_END}\n{MARKER_INDEX_END}"

    content = current_content

    # 1. Substituição ou inserção da Matriz
    if MARKER_MATRIX_START in content and MARKER_MATRIX_END in content:
        pattern = re.escape(MARKER_MATRIX_START) + r".*?" + re.escape(MARKER_MATRIX_END)
        content = re.sub(pattern, lambda _: new_matrix_block, content, flags=re.DOTALL)
    else:
        # Procura a seção ## Matriz de Categorias e Resumo de Documentos
        matrix_header = "## Matriz de Categorias e Resumo de Documentos"
        if matrix_header in content:
            # Encontra até o próximo header de nível 2 ou fim
            pattern = re.escape(matrix_header) + r"\n\n.*?(?=\n---\n|\n## |\Z)"
            replacement = f"{matrix_header}\n\n{new_matrix_block}"
            content = re.sub(pattern, lambda _: replacement, content, count=1, flags=re.DOTALL)

    # 2. Substituição ou inserção do Índice
    if MARKER_INDEX_START in content and MARKER_INDEX_END in content:
        pattern = re.escape(MARKER_INDEX_START) + r".*?" + re.escape(MARKER_INDEX_END)
        content = re.sub(pattern, lambda _: new_index_block, content, flags=re.DOTALL)
    else:
        index_header = "## Índice de Palavras-Chave e Links Rápidos"
        if index_header in content:
            pattern = re.escape(index_header) + r"\n\n.*?\Z"
            replacement = f"{index_header}\n\n{new_index_block}\n"
            content = re.sub(pattern, lambda _: replacement, content, count=1, flags=re.DOTALL)

    return content


def main():
    parser = argparse.ArgumentParser(description="Regenera seções dinâmicas de ORGANIZATION.md com preview de diff.")
    parser.add_argument("--write", action="store_true", help="Aplica as alterações no arquivo ORGANIZATION.md.")
    parser.add_argument("--check", action="store_true", help="Valida se ORGANIZATION.md está em sincronia com os .mdx (exit 1 se divergir).")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    org_file = root_dir / "ORGANIZATION.md"

    if not org_file.exists():
        print(f"❌ Erro: Arquivo {org_file} não encontrado.")
        sys.exit(1)

    current_content = org_file.read_text(encoding="utf-8")
    docs = collect_mdx_metadata(root_dir)

    matrix_text = generate_matrix_section(docs)
    index_text = generate_index_section(docs)

    new_content = update_organization_content(current_content, matrix_text, index_text)

    # Gera o diff unificado
    diff = list(difflib.unified_diff(
        current_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile="ORGANIZATION.md (atual)",
        tofile="ORGANIZATION.md (regenerado)",
    ))

    print("=" * 70)
    print(f"📄 Gerador de ORGANIZATION.md - Repositório: {root_dir.name}")
    print(f"📁 Documentos .mdx indexados: {len(docs)}")
    print("=" * 70)

    if not diff:
        print("\n✅ Sucesso: ORGANIZATION.md já está 100% atualizado e em sincronia com todos os .mdx!")
        print("=" * 70)
        sys.exit(0)

    print("\n🔍 DIFF DETECTADO ENTRE O ARQUIVO ATUAL E O REGENERADO:\n")
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"\033[92m{line.rstrip()}\033[0m" if sys.stdout.isatty() else line.rstrip())
        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[91m{line.rstrip()}\033[0m" if sys.stdout.isatty() else line.rstrip())
        elif line.startswith("@"):
            print(f"\033[94m{line.rstrip()}\033[0m" if sys.stdout.isatty() else line.rstrip())
        else:
            print(line.rstrip())

    print("\n" + "=" * 70)

    if args.write:
        org_file.write_text(new_content, encoding="utf-8")
        print("💾 Sucesso: ORGANIZATION.md atualizado com marcadores AUTO-GENERATED!")
        print("=" * 70)
        sys.exit(0)
    elif args.check:
        print("❌ Falha: ORGANIZATION.md está desatualizado em relação aos arquivos .mdx.")
        print("💡 Para sincronizar o arquivo, execute: python scripts/gerar_organization.py --write")
        print("=" * 70)
        sys.exit(1)
    else:
        print("ℹ️ Modo Preview: Nenhuma alteração foi gravada em disco.")
        print("💡 Para aplicar as alterações, execute: python scripts/gerar_organization.py --write")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
