#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/drawdb_to_neon.py
Conversor e Visualizador de Modelagem Relacional (Padrão DrawDB / Prisma / Neon Postgres)
1. Converte schemas visuais exportados do DrawDB (.json) em DDL PostgreSQL e modelos Prisma.
2. Lê o schema ativo do Prisma (Neon PostgreSQL) e gera a documentação viva em HTML5.
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
PRISMA_FILE = WORKSPACE_DIR / "projetos" / "wa-akg-gateway" / "prisma" / "schema.prisma"
OUTPUT_SCHEMA_HTML = WORKSPACE_DIR / "00-meta" / "schemas" / "neon_database_schema.html"
NOVO_DOC_SCRIPT = WORKSPACE_DIR / "scripts" / "novo_documento.py"

TYPE_MAP_DRAWDB_TO_PG = {
    "VARCHAR": "VARCHAR(255)",
    "TEXT": "TEXT",
    "INTEGER": "INTEGER",
    "INT": "INTEGER",
    "BIGINT": "BIGINT",
    "BOOLEAN": "BOOLEAN",
    "TIMESTAMP": "TIMESTAMP WITH TIME ZONE",
    "JSON": "JSONB",
    "JSONB": "JSONB",
    "FLOAT": "DOUBLE PRECISION"
}

def converter_drawdb_para_ddl(drawdb_data: dict) -> str:
    """Converte JSON do DrawDB em DDL PostgreSQL."""
    tabelas = drawdb_data.get("tables", [])
    sql_statements = []

    for tab in tabelas:
        nome = tab.get("name", "sem_nome")
        campos = tab.get("fields", [])
        colunas_sql = []

        for c in campos:
            c_nome = c.get("name")
            c_tipo_raw = c.get("type", "TEXT").upper()
            c_tipo = TYPE_MAP_DRAWDB_TO_PG.get(c_tipo_raw, c_tipo_raw)
            pk = " PRIMARY KEY" if c.get("pk") else ""
            not_null = " NOT NULL" if c.get("notNull") and not c.get("pk") else ""
            default = f" DEFAULT {c.get('default')}" if c.get("default") is not None else ""
            colunas_sql.append(f"    {c_nome} {c_tipo}{pk}{not_null}{default}")

        cols_str = ",\n".join(colunas_sql)
        sql_statements.append(f"CREATE TABLE IF NOT EXISTS {nome} (\n{cols_str}\n);")

    return "\n\n".join(sql_statements)

def extrair_modelos_prisma(prisma_path: Path) -> list[dict]:
    """Extrai modelos e campos de um arquivo schema.prisma."""
    if not prisma_path.exists():
        return []

    content = prisma_path.read_text(encoding="utf-8")
    model_regex = re.compile(r'model\s+([A-Za-z0-9_]+)\s*\{([^}]+)\}', re.MULTILINE)
    
    modelos = []
    for match in model_regex.finditer(content):
        nome_modelo = match.group(1)
        bloco_campos = match.group(2)
        campos = []
        for linha in bloco_campos.splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("//") or linha.startswith("@@"):
                continue
            partes = linha.split()
            if len(partes) >= 2:
                campo_nome = partes[0]
                campo_tipo = partes[1]
                modificadores = " ".join(partes[2:]) if len(partes) > 2 else ""
                campos.append({
                    "nome": campo_nome,
                    "tipo": campo_tipo,
                    "modificadores": modificadores
                })
        modelos.append({
            "nome": nome_modelo,
            "campos": campos
        })
    return modelos

def gerar_relatorio_schema_html(modelos: list[dict]) -> str:
    """Gera o HTML5 corporativo com o catálogo de tabelas do Neon."""
    total_tabelas = len(modelos)
    total_campos = sum(len(m["campos"]) for m in modelos)

    cards_tabelas = []
    for m in modelos:
        nome_tab = m["nome"]
        campos = m["campos"]
        
        linhas_tr = []
        for c in campos:
            is_pk = "@id" in c["modificadores"]
            is_fk = "@relation" in c["modificadores"]
            pk_badge = '<span style="font-size: 9px; font-weight: bold; background: #e0f2fe; color: #0369a1; padding: 2px 4px; border-radius: 3px;">PK</span>' if is_pk else ""
            fk_badge = '<span style="font-size: 9px; font-weight: bold; background: #fef3c7; color: #b45309; padding: 2px 4px; border-radius: 3px;">FK</span>' if is_fk else ""
            
            linhas_tr.append(f"""
            <tr>
                <td style="font-family: monospace; font-size: 11px; font-weight: 600;">{c['nome']} {pk_badge} {fk_badge}</td>
                <td style="font-family: monospace; font-size: 11px; color: #475569;">{c['tipo']}</td>
                <td style="font-size: 10px; color: #64748b;">{c['modificadores']}</td>
            </tr>
            """)

        tabela_html = f"""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 8px;">
                <span style="font-size: 13px; font-weight: 700; color: #0284c7; text-transform: uppercase;">Tabela: {nome_tab}</span>
                <span style="font-size: 10px; font-weight: 600; color: #64748b;">{len(campos)} colunas</span>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                <thead>
                    <tr style="border-bottom: 1px solid #cbd5e1; text-align: left; background: #f8fafc;">
                        <th style="padding: 4px 6px;">Coluna</th>
                        <th style="padding: 4px 6px;">Tipo</th>
                        <th style="padding: 4px 6px;">Atributos / Relações</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(linhas_tr)}
                </tbody>
            </table>
        </div>
        """
        cards_tabelas.append(tabela_html)

    return f"""
    <section class="section">
        <h2>1. Visão Geral do Banco Neon PostgreSQL (AWS São Paulo)</h2>
        <div class="grid grid-3 my-4">
            <div class="card">
                <div class="text-sm font-bold text-muted">TABELAS ATIVAS</div>
                <div class="text-xl font-bold text-primary mt-1">{total_tabelas}</div>
                <p class="text-xs text-secondary mt-1">Modelos persistidos via Prisma ORM.</p>
            </div>
            <div class="card">
                <div class="text-sm font-bold text-muted">COLUNAS / CAMPOS</div>
                <div class="text-xl font-bold text-primary mt-1">{total_campos}</div>
                <p class="text-xs text-secondary mt-1">Campos estruturados e relacionamentos.</p>
            </div>
            <div class="card">
                <div class="text-sm font-bold text-muted">REGIÃO NEON</div>
                <div class="text-xl font-bold text-primary mt-1">aws-sa-east-1</div>
                <p class="text-xs text-secondary mt-1">São Paulo (Latência sub-50ms).</p>
            </div>
        </div>
    </section>

    <section class="section">
        <h2>2. Dicionário de Dados e Schemas Relacionais</h2>
        {"".join(cards_tabelas)}
    </section>
    """

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Conversor DrawDB & Visualizador de Schemas Neon Postgres")
    parser.add_argument("--drawdb", "-d", help="Caminho do arquivo JSON do DrawDB para converter em DDL")
    parser.add_argument("--gerar-docs", "-g", action="store_true", help="Gera documentação viva do schema Prisma em HTML5")
    parser.add_argument("--saida", "-o", default=str(OUTPUT_SCHEMA_HTML), help="Caminho de saída da documentação")

    args = parser.parse_args()

    if args.drawdb:
        p = Path(args.drawdb)
        if not p.exists():
            print(f"[ERRO] Arquivo DrawDB não encontrado: {p}")
            sys.exit(1)
        dados = json.loads(p.read_text(encoding="utf-8"))
        ddl = converter_drawdb_para_ddl(dados)
        print("=== DDL PostgreSQL Gerado ===")
        print(ddl)

    elif args.gerar_docs:
        print(f"[DrawDB] Lendo schema Prisma: {PRISMA_FILE}...")
        modelos = extrair_modelos_prisma(PRISMA_FILE)
        print(f"[DrawDB] {len(modelos)} modelos encontrados.")

        conteudo_html = gerar_relatorio_schema_html(modelos)

        saida_path = Path(args.saida)
        saida_path.parent.mkdir(parents=True, exist_ok=True)

        temp_content_file = saida_path.parent / ".temp_schema_content.html"
        temp_content_file.write_text(conteudo_html, encoding="utf-8")

        cmd = [
            sys.executable,
            str(NOVO_DOC_SCRIPT),
            "--titulo", "Catálogo de Schemas: Neon PostgreSQL (AWS São Paulo)",
            "--arquivo", str(saida_path),
            "--preset", "nota-tecnica",
            "--tags", "BancoDeDados,Neon,PostgreSQL,Prisma,DrawDB",
            "--conteudo-arquivo", str(temp_content_file),
            "--force"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=WORKSPACE_DIR)
        if temp_content_file.exists():
            temp_content_file.unlink()
        if res.returncode == 0:
            print(f"[SUCESSO] Documentação viva do Neon DB gerada em: {saida_path}")
        else:
            print(f"[FALHA] Erro ao criar documento: {res.stderr}\n{res.stdout}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
