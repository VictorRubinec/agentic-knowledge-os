#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/schemas/jantt_generator.py
Gerador de Cronogramas Gantt Interativos (Padrão Jantt - Zero Dependências)
Renderiza cronogramas a partir de dados JSON declarativos em HTML5 e CSS puro,
otimizado tanto para visualização em tela quanto para compilação pixel-perfect em PDF A4.
"""

import html
from datetime import datetime

def escape(val: str) -> str:
    return html.escape(str(val))

def render_gantt(tarefas: list[dict], titulo: str = "Cronograma de Entregas", colunas: list[str] = None) -> str:
    """Renderiza um cronograma Gantt declarativo.
    
    tarefas: [
        {"nome": "Fase 1: Anti-Slop", "categoria": "Qualidade", "inicio_col": 1, "duracao_col": 2, "progresso": 100, "status": "CONCLUIDO"},
        {"nome": "Fase 2: Webhook WA", "categoria": "Ingestão", "inicio_col": 2, "duracao_col": 3, "progresso": 100, "status": "CONCLUIDO"},
        {"nome": "Fase 3: Jantt & Archify", "categoria": "Visualização", "inicio_col": 4, "duracao_col": 2, "progresso": 80, "status": "ATIVO"},
        {"nome": "Fase 4: Neon Schemas", "categoria": "Dados", "inicio_col": 5, "duracao_col": 2, "progresso": 0, "status": "PLANEJAMENTO"}
    ]
    """
    if not colunas:
        colunas = ["Sem 1", "Sem 2", "Sem 3", "Sem 4", "Sem 5", "Sem 6"]

    total_cols = len(colunas)

    header_cols_html = "".join([
        f'<div style="flex: 1; text-align: center; font-size: 11px; font-weight: 600; color: #475569; padding: 6px 0; border-left: 1px solid #e2e8f0;">{escape(c)}</div>'
        for c in colunas
    ])

    linhas_html = []
    cores_status = {
        "CONCLUIDO": "#10b981",
        "ATIVO": "#0284c7",
        "PLANEJAMENTO": "#94a3b8",
        "BLOQUEADO": "#ef4444"
    }

    for t in tarefas:
        nome = escape(t.get("nome", ""))
        categoria = escape(t.get("categoria", ""))
        inicio = max(1, min(total_cols, t.get("inicio_col", 1)))
        duracao = max(1, min(total_cols - inicio + 1, t.get("duracao_col", 1)))
        progresso = max(0, min(100, t.get("progresso", 0)))
        status = t.get("status", "PLANEJAMENTO")
        cor_barra = cores_status.get(status, "#0284c7")

        left_pct = ((inicio - 1) / total_cols) * 100
        width_pct = (duracao / total_cols) * 100

        badge_status = f'<span style="font-size: 9px; font-weight: 700; padding: 2px 5px; border-radius: 3px; background: {cor_barra}20; color: {cor_barra}; border: 1px solid {cor_barra}40;">{status}</span>'

        linha = f"""
        <div style="display: flex; align-items: center; border-bottom: 1px solid #f1f5f9; padding: 8px 0;">
            <div style="width: 220px; min-width: 220px; padding-right: 12px; box-sizing: border-box;">
                <div style="font-size: 12px; font-weight: 600; color: #0f172a;">{nome}</div>
                <div style="display: flex; align-items: center; gap: 6px; margin-top: 3px;">
                    <span style="font-size: 10px; color: #64748b;">{categoria}</span>
                    {badge_status}
                </div>
            </div>
            <div style="flex: 1; position: relative; height: 26px; background: #fafafa; border-left: 1px solid #e2e8f0; display: flex;">
                <!-- Linhas verticais de grade -->
                {"".join(['<div style="flex: 1; border-right: 1px dashed #e2e8f0; height: 100%;"></div>' for _ in range(total_cols)])}
                
                <!-- Barra de Tarefa -->
                <div style="position: absolute; left: {left_pct:.2f}%; width: {width_pct:.2f}%; top: 3px; height: 20px; background: {cor_barra}; border-radius: 4px; display: flex; align-items: center; justify-content: space-between; padding: 0 6px; box-sizing: border-box; overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <span style="font-size: 10px; font-weight: 600; color: #ffffff; white-space: nowrap;">{progresso}%</span>
                </div>
            </div>
        </div>
        """
        linhas_html.append(linha)

    return f"""
    <div class="jantt-gantt-container" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 14px; margin: 16px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0f172a;">{escape(titulo)}</div>
            <div style="display: flex; gap: 12px; font-size: 10px; color: #64748b;">
                <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 8px; height: 8px; border-radius: 2px; background: #10b981;"></span> Concluído</span>
                <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 8px; height: 8px; border-radius: 2px; background: #0284c7;"></span> Em Andamento</span>
                <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 8px; height: 8px; border-radius: 2px; background: #94a3b8;"></span> Planejado</span>
            </div>
        </div>
        
        <!-- Cabeçalho de Colunas -->
        <div style="display: flex; align-items: center; background: #f8fafc; border-bottom: 1px solid #cbd5e1; border-top: 1px solid #cbd5e1;">
            <div style="width: 220px; min-width: 220px; font-size: 11px; font-weight: 700; color: #334155; padding: 6px 10px;">Atividade / Entrega</div>
            <div style="flex: 1; display: flex;">
                {header_cols_html}
            </div>
        </div>

        <!-- Linhas de Atividades -->
        {"".join(linhas_html)}
    </div>
    """
