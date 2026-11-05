#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/schemas/diagram_design.py
Motor de Diagramação Editorial em HTML + SVG puro (Padrão Diagram Design)
Substitui saídas brutas e distorcidas de Mermaid por componentes com:
- Grid rígido de 4px
- Linhas e bordas hairlines de 1px
- Zero sombras borradas ou gradientes desnecessários
- Tipografia sóbria e alto contraste
- Compatibilidade pixel-perfect com Playwright PDF
"""

import html

def escape(val: str) -> str:
    return html.escape(str(val))

def linear_flow(passos: list[dict], direcao: str = "horizontal") -> str:
    """Gera um fluxo linear de passos em cards conectados por hairlines.
    
    Cada passo: {"num": "01", "titulo": "...", "desc": "...", "badge": "..."}
    """
    is_horiz = direcao == "horizontal"
    flex_dir = "flex-row" if is_horiz else "flex-col"
    
    items_html = []
    total = len(passos)
    for idx, p in enumerate(passos, start=1):
        num = escape(p.get("num", f"{idx:02d}"))
        titulo = escape(p.get("titulo", ""))
        desc = escape(p.get("desc", ""))
        badge = p.get("badge")
        badge_html = f'<span style="font-size: 10px; font-weight: 600; text-transform: uppercase; padding: 2px 6px; border: 1px solid var(--border-color, #cbd5e1); border-radius: 4px; color: var(--text-secondary, #475569);">{escape(badge)}</span>' if badge else ""
        
        arrow_html = ""
        if idx < total:
            if is_horiz:
                arrow_html = '<div style="display: flex; align-items: center; justify-content: center; padding: 0 8px; color: var(--border-color, #94a3b8); font-size: 16px;">→</div>'
            else:
                arrow_html = '<div style="display: flex; align-items: center; justify-content: center; padding: 6px 0; color: var(--border-color, #94a3b8); font-size: 16px;">↓</div>'

        card = f"""
        <div style="flex: 1; min-width: 180px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 14px; box-sizing: border-box;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-family: monospace; font-size: 11px; font-weight: 700; color: #0284c7;">{num}</span>
                {badge_html}
            </div>
            <div style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">{titulo}</div>
            <div style="font-size: 11px; line-height: 1.4; color: #475569;">{desc}</div>
        </div>
        """
        items_html.append(card)
        if arrow_html:
            items_html.append(arrow_html)

    layout = "display: flex; flex-direction: row; align-items: stretch; gap: 4px; overflow-x: auto; padding: 12px 0;" if is_horiz else "display: flex; flex-direction: column; gap: 4px; padding: 12px 0;"
    return f"""
    <div class="diagram-design-flow" style="{layout}">
        {"".join(items_html)}
    </div>
    """

def architecture_grid(camadas: list[dict]) -> str:
    """Gera um diagrama de arquitetura em blocos modulares estruturados.
    
    Cada camada: {"titulo": "...", "modulos": [{"nome": "...", "sub": "..."}]}
    """
    camadas_html = []
    for c in camadas:
        titulo = escape(c.get("titulo", ""))
        mods = c.get("modulos", [])
        mods_html = []
        for m in mods:
            nome = escape(m.get("nome", ""))
            sub = escape(m.get("sub", ""))
            mods_html.append(f"""
            <div style="flex: 1; min-width: 140px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 8px 10px;">
                <div style="font-size: 12px; font-weight: 700; color: #0f172a;">{nome}</div>
                <div style="font-size: 10px; color: #64748b; margin-top: 2px;">{sub}</div>
            </div>
            """)
        
        camadas_html.append(f"""
        <div style="background: #ffffff; border: 1px solid #94a3b8; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #0284c7; letter-spacing: 0.5px; margin-bottom: 8px;">{titulo}</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                {"".join(mods_html)}
            </div>
        </div>
        """)

    return f"""
    <div class="diagram-design-architecture" style="padding: 10px 0;">
        {"".join(camadas_html)}
    </div>
    """

def matrix_2x2(quadrantes: dict, titulo_x: str = "Impacto", titulo_y: str = "Esforço") -> str:
    """Gera matriz 2x2 com eixos ortogonais e posicionamento de prioridade."""
    # quadrantes: {"q1_alto_baixo": [...], "q2_alto_alto": [...], "q3_baixo_baixo": [...], "q4_baixo_alto": [...]}
    def render_itens(lista):
        return "".join([f'<li style="font-size: 11px; color: #334155; margin-bottom: 3px;">{escape(it)}</li>' for it in lista])

    return f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px;">
        <div style="border: 1px dashed #cbd5e1; border-radius: 4px; padding: 8px; background: #f0fdf4;">
            <span style="font-size: 11px; font-weight: 700; color: #166534;">Alto {escape(titulo_x)} / Baixo {escape(titulo_y)} (Vitórias Rápidas)</span>
            <ul style="margin: 6px 0 0 16px; padding: 0;">{render_itens(quadrantes.get("quick_wins", []))}</ul>
        </div>
        <div style="border: 1px dashed #cbd5e1; border-radius: 4px; padding: 8px; background: #eff6ff;">
            <span style="font-size: 11px; font-weight: 700; color: #1e40af;">Alto {escape(titulo_x)} / Alto {escape(titulo_y)} (Estratégico)</span>
            <ul style="margin: 6px 0 0 16px; padding: 0;">{render_itens(quadrantes.get("strategic", []))}</ul>
        </div>
        <div style="border: 1px dashed #cbd5e1; border-radius: 4px; padding: 8px; background: #fafaf9;">
            <span style="font-size: 11px; font-weight: 700; color: #57534e;">Baixo {escape(titulo_x)} / Baixo {escape(titulo_y)} (Secundário)</span>
            <ul style="margin: 6px 0 0 16px; padding: 0;">{render_itens(quadrantes.get("secondary", []))}</ul>
        </div>
        <div style="border: 1px dashed #cbd5e1; border-radius: 4px; padding: 8px; background: #fef2f2;">
            <span style="font-size: 11px; font-weight: 700; color: #991b1b;">Baixo {escape(titulo_x)} / Alto {escape(titulo_y)} (Evitar / Descartar)</span>
            <ul style="margin: 6px 0 0 16px; padding: 0;">{render_itens(quadrantes.get("avoid", []))}</ul>
        </div>
    </div>
    """
