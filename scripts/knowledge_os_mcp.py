#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
KNOWLEDGE OS MCP SERVER
Servidor nativo do Model Context Protocol (MCP) para o Agentic Knowledge OS.
Permite que qualquer harness ou agente (Antigravity, Cursor, Zed, Goose, Claude)
invoque ferramentas do repositório sem navegar por arquivos às cegas.
=============================================================================
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

# Configuração de encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp.server.mcpserver import MCPServer

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
GERAR_PDF_SCRIPT = SCRIPTS_DIR / "gerar_pdf.py"
OPTMEM_SCRIPT = SCRIPTS_DIR / "optmem_memo.py"

server = MCPServer("agentic-knowledge-os")


@server.tool()
def generate_pdf(file_path: str, output_path: str = "", theme: str = "corporate") -> str:
    """Compila um documento (.html ou .mdx) em PDF corporativo A4 pixel-perfect utilizando o motor oficial Playwright.
    
    Args:
        file_path: Caminho relativo ou absoluto do arquivo .html ou .mdx.
        output_path: Caminho customizado para salvar o PDF (opcional).
        theme: Tema visual (corporate, join4, studio_kustom, triade, etc.).
    """
    target = Path(file_path)
    if not target.is_absolute():
        target = WORKSPACE_DIR / target

    if not target.exists():
        return f"Erro: Arquivo de origem não encontrado: {target}"

    cmd = [sys.executable, str(GERAR_PDF_SCRIPT), str(target), "-t", theme]
    if output_path:
        out_target = Path(output_path)
        if not out_target.is_absolute():
            out_target = WORKSPACE_DIR / out_target
        cmd.extend(["-o", str(out_target)])

    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
    if res.returncode == 0:
        return f"Sucesso:\n{res.stdout}"
    return f"Falha na compilação do PDF (código {res.returncode}):\n{res.stderr}\n{res.stdout}"


@server.tool()
def validate_document(file_path: str) -> str:
    """Executa a auditoria de qualidade e linter do documento (anti-órfãos, proporção Mermaid e sintaxe).
    
    Args:
        file_path: Caminho do arquivo a ser validado.
    """
    target = Path(file_path)
    if not target.is_absolute():
        target = WORKSPACE_DIR / target

    if not target.exists():
        return f"Erro: Arquivo não encontrado: {target}"

    cmd = [sys.executable, str(GERAR_PDF_SCRIPT), str(target), "--check-only"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
    return res.stdout if res.returncode == 0 else f"Pendências encontradas:\n{res.stdout}\n{res.stderr}"


@server.tool()
def search_knowledge(query: str, category: str = "") -> str:
    """Pesquisa no acervo de notas, relatórios e tarefas por palavras-chave sem necessidade de varredura cega.
    
    Args:
        query: Palavra-chave ou termo de pesquisa.
        category: Filtro opcional por pasta/categoria (ex: 'join4', 'studio-kustom', 'sites').
    """
    query_lower = query.lower()
    matches = []

    # Escanear arquivos .html, .mdx e .md
    for ext in ("*.html", "*.mdx", "*.md"):
        for path in WORKSPACE_DIR.rglob(ext):
            # Ignora pastas de cache ou ambientes virtuais
            if any(p in path.parts for p in (".git", "node_modules", ".gemini", "dist", "build", "__pycache__")):
                continue
            if category and category.lower() not in str(path).lower():
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                if query_lower in content.lower():
                    # Extrair trecho
                    idx = content.lower().find(query_lower)
                    start = max(0, idx - 80)
                    end = min(len(content), idx + 120)
                    snippet = content[start:end].replace("\n", " ").strip()
                    rel = path.relative_to(WORKSPACE_DIR)
                    matches.append(f"- **{rel}**\n  > ...{snippet}...")
                    if len(matches) >= 15:
                        break
            except Exception:
                pass
        if len(matches) >= 15:
            break

    if not matches:
        return f"Nenhum documento encontrado contendo '{query}'."

    return f"Encontrados {len(matches)} resultado(s) para '{query}':\n\n" + "\n\n".join(matches)


@server.tool()
def optmem_record(memory_text: str) -> str:
    """Registra uma memória persistente (máximo 280 bytes) na árvore OptMem oficial.
    
    Args:
        memory_text: Fato novo, lição aprendida ou decisão a ser guardada para futuras sessões.
    """
    cmd = [sys.executable, str(OPTMEM_SCRIPT), "note", memory_text]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
    return res.stdout if res.returncode == 0 else f"Erro ao registrar memória:\n{res.stderr}"


@server.tool()
def optmem_wake() -> str:
    """Lê o estado mental consolidado do agente na inicialização de uma sessão."""
    cmd = [sys.executable, str(OPTMEM_SCRIPT), "wake"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
    return res.stdout if res.returncode == 0 else f"Erro ao executar wake:\n{res.stderr}"


@server.tool()
def optmem_recall(query_regex: str) -> str:
    """Busca exata por expressão regular em todo o histórico de memórias gravadas no OptMem."""
    cmd = [sys.executable, str(OPTMEM_SCRIPT), "recall", query_regex]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
    return res.stdout if res.returncode == 0 else f"Erro ao buscar memória:\n{res.stderr}"


def main():
    # Executa o servidor MCP via stdio (padrão JSON-RPC)
    server.run()


if __name__ == "__main__":
    main()
