#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação de Frontmatter e seções obrigatórias em arquivos .mdx.
Exige:
- Frontmatter YAML delimitado por --- contendo:
    * title
    * category
    * tags
    * updatedAt
    * status
- Seção de Markdown: "Linha do Tempo" (ex: ## Linha do Tempo, ## 7. Linha do Tempo...)
- Seção de Markdown: "Assuntos Relacionados" (ex: ## Assuntos Relacionados, ## 8. Assuntos Relacionados...)
"""

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

# Diretórios a ignorar
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

REQUIRED_FRONTMATTER_FIELDS = ["title", "category", "tags", "updatedAt", "status"]

RE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RE_TIMELINE_SECTION = re.compile(r"^#+\s+.*Linha do Tempo.*$", re.MULTILINE | re.IGNORECASE)
RE_RELATED_SECTION = re.compile(r"^#+\s+.*Assuntos Relacionados.*$", re.MULTILINE | re.IGNORECASE)


def find_mdx_files(root_dir: Path):
    mdx_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".mdx"):
                mdx_files.append(Path(root) / file)
    return mdx_files


def parse_yaml_frontmatter_simple(yaml_str: str) -> dict:
    """Extrai campos simples e listas de frontmatter YAML sem depender de bibliotecas externas."""
    fields = {}
    lines = yaml_str.splitlines()
    current_key = None
    list_items = []

    for line in lines:
        raw_line = line.strip()
        if not raw_line or raw_line.startswith("#"):
            continue

        # Item de lista YAML: - valor
        if raw_line.startswith("- ") and current_key:
            item_val = raw_line[2:].strip().strip("\"'")
            list_items.append(item_val)
            fields[current_key] = list_items
            continue

        # Chave: valor
        match = re.match(r"^([a-zA-Z0-9_-]+)\s*:\s*(.*)$", raw_line)
        if match:
            key, val = match.groups()
            current_key = key.strip()
            val = val.strip()
            # Remove comentários inline
            if " #" in val:
                val = val.split(" #")[0].strip()

            if val.startswith("[") and val.endswith("]"):
                # Lista inline: ["a", "b"]
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


def validate_file_frontmatter(file_path: Path):
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Erro ao ler arquivo: {e}"]

    parsed_fields = {}
    # 1. Validação de Frontmatter
    match = RE_FRONTMATTER.match(content)
    if not match:
        violations.append("Frontmatter YAML ausente ou mal formatado no topo do arquivo (delimitado por '---')")
        body_content = content
    else:
        yaml_content = match.group(1)
        body_content = content[match.end():]
        parsed_fields = parse_yaml_frontmatter_simple(yaml_content)

        for req_field in REQUIRED_FRONTMATTER_FIELDS:
            if req_field not in parsed_fields:
                violations.append(f"Campo obrigatório do frontmatter ausente: '{req_field}'")
            elif parsed_fields[req_field] is None or parsed_fields[req_field] == "":
                violations.append(f"Campo obrigatório do frontmatter está vazio: '{req_field}'")

    # 2. Validação das seções "Linha do Tempo" e "Assuntos Relacionados"
    # Documentos comerciais destinados ao cliente externo (propostas/contratos) são dispensados de seções internas de notas
    is_client_doc = (
        parsed_fields.get("doc_type") in ("proposta", "contrato")
        or parsed_fields.get("type") in ("proposta", "contrato")
    )

    if not is_client_doc:
        if not RE_TIMELINE_SECTION.search(body_content):
            violations.append("Seção obrigatória ausente: 'Linha do Tempo'")

        if not RE_RELATED_SECTION.search(body_content):
            violations.append("Seção obrigatória ausente: 'Assuntos Relacionados'")

    return violations


def main():
    root_dir = Path(__file__).resolve().parent.parent
    mdx_files = find_mdx_files(root_dir)

    total_files = len(mdx_files)
    total_violations = 0
    files_with_violations = 0

    print("=" * 70)
    print(f"📋 Validador de Frontmatter e Seções MDX - Repositório: {root_dir.name}")
    print(f"📁 Arquivos .mdx encontrados para validação: {total_files}")
    print(f"🔑 Campos exigidos: {', '.join(REQUIRED_FRONTMATTER_FIELDS)}")
    print(f"📌 Seções exigidas: 'Linha do Tempo' e 'Assuntos Relacionados'")
    print("=" * 70)

    for file_path in sorted(mdx_files):
        rel_path = file_path.relative_to(root_dir)
        violations = validate_file_frontmatter(file_path)

        if violations:
            files_with_violations += 1
            total_violations += len(violations)
            print(f"\n❌ [{rel_path}] ({len(violations)} problemas):")
            for msg in violations:
                print(f"   • {msg}")

    print("\n" + "=" * 70)
    if total_violations == 0:
        print("✅ Sucesso: Todos os arquivos .mdx estão em total conformidade!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"❌ Falha: Encontradas {total_violations} violações em {files_with_violations} arquivos.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
