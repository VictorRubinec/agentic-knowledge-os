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
    "trabalho/join4/produto/consultas-portal": "Auditoria técnica, arquitetura BFF e visão de produto do ConsultasPortal.",
    "trabalho/join4/produto": "Ferramentas internas e produtos SaaS desenvolvidos pela área de Produto da Join4.",
    "trabalho/join4/clientes/atlantica/automacoes": "Documentações técnicas, arquitetura e dossiês de robôs RPA da Atlântica.",
    "trabalho/join4/clientes/atlantica/erros": "Relatórios técnicos, incidentes e controle de erros da Atlântica.",
    "trabalho/join4/clientes/atlantica": "Suporte, incidentes, automações e reuniões da Atlântica Hotels.",
    "trabalho/join4": "Demandas, tarefas, decisões técnicas e reuniões da Join4.",
    "trabalho/triade/comercial": "Instrumentos jurídicos, formulários de descoberta e protocolos de entrega da Triade.",
    "trabalho/triade/plataforma-interna": "Plataforma unificada de gestão de sprints, documentação MDX e contexto de IA da Triade.",
    "trabalho/triade/projetos/somos1-tattoo-studio": "Plataforma oficial Somos1: Agendamento, CRM, Indicações e Mensageria WhatsApp.",
    "trabalho/triade/projetos/exemplo-projeto-tatuagem": "Projeto de referência Triade: Blackthorn Tattoo Studio.",
    "trabalho/triade/projetos": "Soluções comerciais entregues a clientes externos sob a governança da Triade.",
    "trabalho/triade": "Consultoria, posicionamento, estratégia, governança e metodologia da Triade.",
    "trabalho/sites/relatorios": "Relatórios técnicos de Design System e auditoria de CSS (designsys).",
    "trabalho/sites/pessoal": "Websites pessoais, landing pages e portfólios próprios.",
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
    "studio-kustom": "Projetos, estratégias, marcas e ideias da Studio Kustom.",
    "projetos/automacao-emails": "Engenharia e desenvolvimento da engine RubiMail Serverless.",
    "projetos/automacao-fontes": "Motor FontScout para pesquisa e download de fontes em Python.",
    "projetos/monitor-uptime/conhecimentos": "Guias técnicos de SSL socket, Telegram API, worker e status page.",
    "projetos/monitor-uptime": "Prompt mestre e arquitetura do Monitor de Uptime e Status Page.",
    "projetos/gerador-fichas-ordem-2/conhecimentos": "Bases de conhecimento, anatomia A4, design system e schemas do Gerador de Fichas Ordem 2.",
    "projetos/gerador-fichas-ordem-2": "Planejamento e especificação técnica do Gerador Web de Fichas Ordem 2 (300 DPI A4).",
    "projetos/pesquisas": "Pesquisas técnicas aprofundadas, benchmarks e instrumentos para tomada de decisão.",
    "projetos": "Projetos pessoais, estudos e ideias gerais fora do trabalho.",
    "pos-ia/00-visao-geral": "Ementa, cronograma acadêmico e matriz de competências da pós-graduação.",
    "pos-ia/disciplinas/00-ambientacao": "Ambientação, diretrizes institucionais (UNIPDS) e setup de desenvolvimento.",
    "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores": "Fundamentos de IA, Transformers, tokens, amostragem e saídas estruturadas.",
    "pos-ia/disciplinas": "Anotações e cadernos vivos dos módulos da pós-graduação em IA Aplicada.",
    "pos-ia/projetos": "Catálogo de projetos práticos, laboratórios e projeto final (Capstone) da pós-graduação.",
    "pos-ia/blueprints-e-padroes": "Biblioteca de padrões de arquitetura de IA, snippets e templates de integração.",
    "pos-ia": "Pós-graduação em Engenharia de Software com IA Aplicada (UNIPDS).",
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
    docs = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".mdx"):
                file_path = Path(root) / file
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
        order_prefixes = ["trabalho/join4", "trabalho/triade", "trabalho/sites", "trabalho", "pos-ia", "rpg/sistemas", "rpg/mesas", "rpg", "studio-kustom", "projetos", "00-meta"]
        for idx, prefix in enumerate(order_prefixes):
            if cat.startswith(prefix):
                return (idx, cat)
        return (99, cat)

    sorted_categories = sorted(categories.keys(), key=category_sort_key)

    lines = [
        "| Categoria / Pasta | Escopo Principal | Documentos Existentes (.mdx) | Resumo do Assunto |",
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
        content = re.sub(pattern, new_matrix_block, content, flags=re.DOTALL)
    else:
        # Procura a seção ## Matriz de Categorias e Resumo de Documentos
        matrix_header = "## Matriz de Categorias e Resumo de Documentos"
        if matrix_header in content:
            # Encontra até o próximo header de nível 2 ou fim
            pattern = re.escape(matrix_header) + r"\n\n.*?(?=\n---\n|\n## |\Z)"
            replacement = f"{matrix_header}\n\n{new_matrix_block}"
            content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

    # 2. Substituição ou inserção do Índice
    if MARKER_INDEX_START in content and MARKER_INDEX_END in content:
        pattern = re.escape(MARKER_INDEX_START) + r".*?" + re.escape(MARKER_INDEX_END)
        content = re.sub(pattern, new_index_block, content, flags=re.DOTALL)
    else:
        index_header = "## Índice de Palavras-Chave e Links Rápidos"
        if index_header in content:
            pattern = re.escape(index_header) + r"\n\n.*?\Z"
            replacement = f"{index_header}\n\n{new_index_block}\n"
            content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

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
