#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/mapear_arquitetura.py
Mapeador de Arquitetura e Codebase em HTML5 (Padrão Archify / Floorplan)
Varre um diretório de software, audita a distribuição de arquivos, calcula LOC e
gera um dossiê técnico visual navegável no padrão oficial do Knowledge OS.
"""

import sys
import os
import subprocess
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
NOVO_DOC_SCRIPT = SCRIPTS_DIR / "novo_documento.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from schemas.diagram_design import architecture_grid

IGNORED_DIRS = {".git", "node_modules", ".gemini", ".next", "dist", "build", "__pycache__", "temp_media"}

EXT_LANG_MAP = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".html": "HTML5",
    ".css": "CSS3",
    ".json": "JSON",
    ".md": "Markdown",
    ".sql": "SQL",
    ".ps1": "PowerShell",
    ".sh": "Shell Script"
}

def auditar_diretorio(alvo_dir: Path) -> dict:
    stats = {
        "total_arquivos": 0,
        "total_linhas": 0,
        "por_linguagem": defaultdict(lambda: {"arquivos": 0, "linhas": 0}),
        "modulos": defaultdict(list)
    }

    for root, dirs, files in os.walk(alvo_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        rel_root = Path(root).relative_to(alvo_dir)
        modulo_nome = rel_root.parts[0] if rel_root.parts else "raiz"

        for f in files:
            p = Path(root) / f
            ext = p.suffix.lower()
            lang = EXT_LANG_MAP.get(ext, "Outros")

            # Contar linhas se for texto
            loc = 0
            try:
                loc = len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
            except Exception:
                pass

            stats["total_arquivos"] += 1
            stats["total_linhas"] += loc
            stats["por_linguagem"][lang]["arquivos"] += 1
            stats["por_linguagem"][lang]["linhas"] += loc
            stats["modulos"][modulo_nome].append({
                "nome": f,
                "caminho": str(p.relative_to(alvo_dir)),
                "lang": lang,
                "loc": loc
            })

    return stats

def gerar_conteudo_html(alvo_nome: str, stats: dict) -> str:
    # 1. Montar Camadas de Arquitetura para o Diagram Design
    camadas_diagrama = []
    top_modulos = sorted(stats["modulos"].items(), key=lambda x: len(x[1]), reverse=True)[:6]
    for mod_nome, arquivos in top_modulos:
        top_files = sorted(arquivos, key=lambda x: x["loc"], reverse=True)[:4]
        camadas_diagrama.append({
            "titulo": f"Módulo: {mod_nome.upper()} ({len(arquivos)} arquivos, {sum(a['loc'] for a in arquivos):,} linhas)",
            "modulos": [{"nome": a["nome"], "sub": f"{a['lang']} · {a['loc']} LOC"} for a in top_files]
        })

    grid_diagrama_html = architecture_grid(camadas_diagrama)

    # 2. Tabela de Linguagens
    linhas_lang = []
    for lang, dados in sorted(stats["por_linguagem"].items(), key=lambda x: x[1]["linhas"], reverse=True):
        linhas_lang.append(
            f"<tr><td><strong>{lang}</strong></td>"
            f"<td class='text-center'>{dados['arquivos']}</td>"
            f"<td class='text-right font-mono'>{dados['linhas']:,}</td></tr>"
        )
    tabela_lang_html = f"""
    <div class="table-container my-4">
        <table>
            <thead>
                <tr><th>Linguagem / Formato</th><th class='text-center'>Qtd. Arquivos</th><th class='text-right'>Linhas de Código (LOC)</th></tr>
            </thead>
            <tbody>
                {"".join(linhas_lang)}
            </tbody>
        </table>
    </div>
    """

    return f"""
    <section class="section">
        <h2>1. Visão Geral da Codebase: {alvo_nome}</h2>
        <div class="grid grid-3 my-4">
            <div class="card">
                <div class="text-sm font-bold text-muted">VOLUME DE ARQUIVOS</div>
                <div class="text-xl font-bold text-primary mt-1">{stats['total_arquivos']:,}</div>
                <p class="text-xs text-secondary mt-1">Arquivos auditados no escopo ativo.</p>
            </div>
            <div class="card">
                <div class="text-sm font-bold text-muted">LINHAS DE CÓDIGO (LOC)</div>
                <div class="text-xl font-bold text-primary mt-1">{stats['total_linhas']:,}</div>
                <p class="text-xs text-secondary mt-1">Densidade total de implementação.</p>
            </div>
            <div class="card">
                <div class="text-sm font-bold text-muted">MÓDULOS DETECTADOS</div>
                <div class="text-xl font-bold text-primary mt-1">{len(stats['modulos'])}</div>
                <p class="text-xs text-secondary mt-1">Divisões arquiteturais identificadas.</p>
            </div>
        </div>
    </section>

    <section class="section">
        <h2>2. Mapa Estrutural de Módulos (Diagram Design)</h2>
        <p>Distribuição dos principais subsistemas e seus componentes de maior densidade lógica:</p>
        {grid_diagrama_html}
    </section>

    <section class="section">
        <h2>3. Distribuição por Tecnologia</h2>
        {tabela_lang_html}
    </section>
    """

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mapeador de Arquitetura de Software em HTML5")
    parser.add_argument("--diretorio", "-d", default=str(WORKSPACE_DIR), help="Diretório a ser mapeado")
    parser.add_argument("--saida", "-o", default="projetos/mapa-arquitetura-knowledge-os.html", help="Caminho do arquivo de saída")
    parser.add_argument("--titulo", "-t", default="Dossiê de Arquitetura: Knowledge OS", help="Título do documento")

    args = parser.parse_args()

    alvo_path = Path(args.diretorio)
    if not alvo_path.is_absolute():
        alvo_path = WORKSPACE_DIR / alvo_path

    if not alvo_path.exists():
        print(f"[ERRO] Diretório não encontrado: {alvo_path}")
        sys.exit(1)

    print(f"[Archify] Auditando diretório: {alvo_path}...")
    stats = auditar_diretorio(alvo_path)
    print(f"[Archify] Varredura concluída: {stats['total_arquivos']} arquivos, {stats['total_linhas']:,} linhas.")

    html_content = gerar_conteudo_html(alvo_path.name, stats)

    # Injetar via CLI oficial novo_documento.py
    cmd = [
        sys.executable,
        str(NOVO_DOC_SCRIPT),
        "--titulo", args.titulo,
        "--arquivo", args.saida,
        "--preset", "relatorio-executivo",
        "--tags", "Arquitetura,Codebase,Archify,KnowledgeOS",
        "--conteudo", html_content,
        "--force"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
    if res.returncode == 0:
        print(f"[SUCESSO] Mapa de arquitetura gerado em: {args.saida}")
    else:
        print(f"[FALHA] Erro ao criar documento: {res.stderr}\n{res.stdout}")

if __name__ == "__main__":
    main()
