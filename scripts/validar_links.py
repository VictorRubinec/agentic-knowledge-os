#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação de links markdown relativos em arquivos .md e .mdx.
Verifica se os arquivos e diretórios de destino existem no disco.
"""

import os
import re
import sys
import urllib.parse
from pathlib import Path

# Garante suporte a UTF-8 no terminal Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Diretórios e arquivos a serem ignorados
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
    "memoria",
}

# Regex para links markdown: [texto](url) e ![alt](url)
MARKDOWN_LINK_REGEX = re.compile(r'!?\[.*?\]\((.*?)\)')
# Regex para tags HTML com href ou src
HTML_SRC_HREF_REGEX = re.compile(r'<(?:a|img|link)\s+[^>]*(?:href|src)=["\'](.*?)["\']', re.IGNORECASE)
# Blocos de código cercados (``` ou ~~~) e trechos de código inline
FENCE_REGEX = re.compile(r'^\s*(```|~~~)')
INLINE_CODE_REGEX = re.compile(r'(`+).*?\1')
# Modelos em 00-meta/ contêm links relativos ao destino onde serão copiados
TEMPLATE_PREFIX = "TEMPLATE_"

SCHEMES_TO_IGNORE = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "ftp://",
    "conversation://",
    "javascript:",
    "data:",
    "about:",
    "blob:",
    "#",
)


def find_documents(root_dir: Path, include_html: bool = True):
    doc_files = []
    exts = (".md", ".mdx", ".html") if include_html else (".md", ".mdx")
    for root, dirs, files in os.walk(root_dir):
        # Filtra diretórios ignorados in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(exts) and not file.startswith(TEMPLATE_PREFIX):
                doc_files.append(Path(root) / file)
    return doc_files


def clean_link_target(raw_url: str) -> str:
    # Remove fragments (#...) e queries (?...)
    url = raw_url.strip()
    if not url:
        return ""
    # Se começar com #, é âncora interna
    if url.startswith("#"):
        return ""
    # Remove aspas se existirem
    url = url.strip("\"'")
    # Remove âncora/query
    url = url.split("#")[0].split("?")[0].strip()
    # Decodifica url encoding (%20, etc.)
    return urllib.parse.unquote(url)


def validate_links_in_file(file_path: Path, root_dir: Path):
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [(0, f"Erro ao ler arquivo: {e}", str(file_path))]

    lines = content.splitlines()

    fence = None
    for line_num, line in enumerate(lines, start=1):
        fence_match = FENCE_REGEX.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is not None:
            continue
        line = INLINE_CODE_REGEX.sub("", line)

        # Encontra links markdown
        md_matches = MARKDOWN_LINK_REGEX.findall(line)
        html_matches = HTML_SRC_HREF_REGEX.findall(line)
        all_links = md_matches + html_matches

        for raw_link in all_links:
            raw_link = raw_link.strip()
            if not raw_link or any(raw_link.startswith(s) for s in SCHEMES_TO_IGNORE):
                continue

            target = clean_link_target(raw_link)
            if not target:
                continue

            # Se for link absoluto com file:///
            if target.startswith("file:///"):
                violations.append((
                    line_num,
                    f"Link absoluto legado 'file:///' proibido: {raw_link}",
                    target
                ))
                continue

            # Resolve caminho relativo ao diretório do arquivo atual
            if target.startswith("/"):
                # Relativo à raiz do repositório
                resolved = root_dir / target.lstrip("/")
            else:
                resolved = (file_path.parent / target).resolve()

            # Checa se o arquivo ou diretório existe
            if not resolved.exists():
                # Fallback: se o link original apontava para .mdx mas o arquivo foi migrado para .html
                if resolved.suffix == ".mdx" and resolved.with_suffix(".html").exists():
                    continue

                violations.append((
                    line_num,
                    f"Link quebrado: destino não encontrado '{raw_link}' -> ({resolved})",
                    raw_link
                ))

    return violations


def main():
    root_dir = Path(__file__).resolve().parent.parent
    doc_files = find_documents(root_dir, include_html=False)

    total_files = len(doc_files)
    total_violations = 0
    files_with_violations = 0

    print("=" * 70)
    print(f"🔍 Validador de Links - Repositório: {root_dir.name}")
    print(f"📁 Documentos analisados: {total_files}")
    print("=" * 70)

    for file_path in sorted(doc_files):
        rel_path = file_path.relative_to(root_dir)
        violations = validate_links_in_file(file_path, root_dir)

        if violations:
            files_with_violations += 1
            total_violations += len(violations)
            print(f"\n❌ [{rel_path}] ({len(violations)} violações):")
            for line_num, msg, raw_link in violations:
                print(f"   • Linha {line_num}: {msg}")

    print("\n" + "=" * 70)
    if total_violations == 0:
        print("✅ Sucesso: Nenhum link quebrado ou inválido encontrado!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"❌ Falha: Encontradas {total_violations} violações em {files_with_violations} arquivos.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
