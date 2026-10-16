#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CONVERSOR DE MDX PARA ARTEFATOS HTML5 COM TAILWIND CSS
Agentic Knowledge OS • Migração com Garantia de Paridade de Conteúdo
=============================================================================
Uso:
  python scripts/converter_mdx_para_html.py <arquivo.mdx> [opcoes]
  python scripts/converter_mdx_para_html.py --lote 0
  python scripts/converter_mdx_para_html.py --dir <pasta>
=============================================================================
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path

# Configuração de encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import markdown

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = WORKSPACE_DIR / "templates" / "artefato_documento.html"


class MDXToHTMLConverter:
    """Converte um documento .mdx em um artefato HTML5 standalone moderno com Tailwind CSS."""

    def __init__(self, mdx_path: Path, backup: bool = True):
        self.mdx_path = mdx_path if mdx_path.is_absolute() else (WORKSPACE_DIR / mdx_path).resolve()
        self.backup = backup
        self.metadata = {
            "title": "Documento Técnico",
            "category": "Documentação",
            "category_display": "Documentação Técnica",
            "updatedAt": "2026-10-15",
            "status": "Homologado",
            "author": "Victor Rubinec",
            "client": "Knowledge OS",
            "version": "v2.0"
        }
        self.mermaid_placeholders = {}
        self.code_placeholders = {}
        self.math_placeholders = {}

    def convert(self) -> Path:
        source_path = self.mdx_path
        bak_path = self.mdx_path.with_suffix(".mdx.bak")
        if not source_path.exists() and bak_path.exists():
            source_path = bak_path

        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.mdx_path}")

        raw_text = source_path.read_text(encoding="utf-8")

        # 1. Salvar backup de segurança
        if self.backup and not bak_path.exists():
            bak_path.write_text(raw_text, encoding="utf-8")

        # 2. Extrair Frontmatter
        content = self._extract_frontmatter(raw_text)

        # 3. Limpar imports React
        content = re.sub(r'^\s*import\s+.*?;\s*$', '', content, flags=re.MULTILINE)

        # 4. Desduplicar Título H1 inicial (o header corporativo já o exibe com destaque)
        content = self._strip_leading_h1(content)

        # 5. Higienizar títulos removendo emojis decorativos (Diretriz AGENTS.md regra 8)
        content = self._clean_decorative_emojis(content)

        # 6. Proteger blocos de código, Mermaid e Matemática antes do processamento Markdown
        content = self._protect_code_and_mermaid(content)
        content = self._protect_math(content)

        # 7. Converter componentes pseudo-JSX
        content = self._transform_badges(content)
        content = self._transform_callouts(content)
        content = self._transform_timelines(content)
        content = self._transform_deployment_timelines(content)
        content = self._transform_pontos_de_interesse(content)
        content = self._transform_param_tables(content)
        content = self._transform_linkcards(content)
        content = self._transform_checkboxes(content)
        content = self._transform_clickup_components(content)
        content = self._normalize_links(content)
        content = self._fix_markdown_lists(content)

        # 7. Converter Markdown para HTML (sem nl2br para evitar quebras desnecessárias)
        html_body = markdown.markdown(
            content,
            extensions=[
                'tables',
                'fenced_code'
            ]
        )

        # 8. Restaurar blocos de código, Mermaid e Matemática
        html_body = self._restore_code_and_mermaid(html_body)
        html_body = self._restore_math(html_body)

        # 9. Montar Artefato HTML Completo a partir do template unificado
        final_html = self._build_page(html_body)

        out_html_path = self.mdx_path.with_suffix(".html")
        out_html_path.write_text(final_html, encoding="utf-8")
        return out_html_path

    def _extract_frontmatter(self, text: str) -> str:
        fm_match = re.search(r'^---([\s\S]*?)---\s*', text)
        if fm_match:
            fm_text = fm_match.group(1)
            for line in fm_text.splitlines():
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    k = k.strip()
                    # Remove comentários inline (# ...)
                    v = re.sub(r'\s+#.*$', '', v).strip().strip('"\'')
                    if k in self.metadata:
                        self.metadata[k] = v
            # Formatação visual da categoria
            cat = self.metadata.get("category", "")
            self.metadata["category_display"] = cat.replace("/", " • ").replace("-", " ").title()
            return text[fm_match.end():]
        return text

    def _strip_leading_h1(self, content: str) -> str:
        """Remove o primeiro H1 do corpo markdown caso coincida ou represente o título principal."""
        leading_h1 = re.match(r'^\s*#\s+([^\n]+)\n*', content)
        if leading_h1:
            h1_text = leading_h1.group(1).strip()
            # Se o título do frontmatter for genérico ou vazio, aproveita o H1
            if not self.metadata.get("title") or self.metadata["title"] == "Documento Técnico":
                self.metadata["title"] = h1_text
            content = content[leading_h1.end():]
        return content

    def _clean_decorative_emojis(self, content: str) -> str:
        """Remove emojis decorativos de cabeçalhos e títulos respeitando a diretriz de sobriedade profissional."""
        # 1. Remover emojis no início de títulos Markdown (ex: ## 📜 Linha do Tempo, ## 🏨 2. Alojamento)
        content = re.sub(
            r'^(#+\s*)[📜🔗📋📁💼🗓️📅✅❌🟢🔴⚪✨🔥🚀💡💬📌🎯🏷️⚡✉️🏨👉]\s*(?:\d+\.)?\s*',
            r'\1',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^(#+\s*(?:\d+\.)?\s*)[📜🔗📋📁💼🗓️📅✅❌🟢🔴⚪✨🔥🚀💡💬📌🎯🏷️⚡✉️🏨👉]\s*',
            r'\1',
            content,
            flags=re.MULTILINE
        )
        # 2. Remover emojis residuais comuns em seções estruturais
        content = re.sub(
            r'^(#+[^\n]*?)\s*[📜🔗📋📁💼🗓️📅✅❌🟢🔴⚪✨🔥🚀💡💬📌🎯🏷️⚡✉️🏨👉]\s*',
            r'\1 ',
            content,
            flags=re.MULTILINE
        )
        # 3. Remover emojis decorativos em prefixos em negrito ou blockquotes (ex: > **🎯 Motivação Operacional**, _(👉 ...)
        content = re.sub(r'(\*\*|>|_|\()\s*[🎯👉🏨💡🚀✨🔥📌]\s*', r'\1', content)
        return content

    def _protect_code_and_mermaid(self, text: str) -> str:
        # 0. Normalizar blocos Mermaid com 1 ou 2 crases acidentais (ex: `mermaid ... `)
        text = re.sub(r'(?m)^`{1,2}mermaid\b', '```mermaid', text)
        text = re.sub(r'(?ms)(```mermaid[ \t]*\r?\n[\s\S]*?\r?\n)`{1,2}$', r'\1```', text)

        # 1. Proteger blocos Mermaid
        def mermaid_sub(m):
            key = f"MERMAIDBLOCKPLACEHOLDER{len(self.mermaid_placeholders)}XYZ"
            chart_body = m.group(1).strip()
            self.mermaid_placeholders[key] = chart_body
            return f"\n\n{key}\n\n"

        text = re.sub(r'```(?:mermaid)[ \t]*\r?\n([\s\S]*?)```', mermaid_sub, text, flags=re.IGNORECASE)

        # 2. Proteger outros blocos de código
        def code_sub(m):
            key = f"CODEBLOCKPLACEHOLDER{len(self.code_placeholders)}XYZ"
            lang = m.group(1) or ""
            code_body = m.group(2)
            self.code_placeholders[key] = (lang, code_body)
            return f"\n\n{key}\n\n"

        text = re.sub(r'```([a-zA-Z0-9_\-\+]*)[ \t]*\r?\n([\s\S]*?)```', code_sub, text)
        return text

    def _transform_badges(self, text: str) -> str:
        # Remover crases que envolvam Badges (ex: `<Badge label="..." />` em tabelas)
        text = re.sub(r'`\s*(<Badge\s+[^>]*?/>)\s*`', r'\1', text)
        text = re.sub(r'`\s*(<Badge\s+[^>]*?>[\s\S]*?</Badge>)\s*`', r'\1', text)

        def badge_sub(m):
            full = m.group(0)
            variant_m = re.search(r'(?:variant|type)=["\'](.*?)["\']', full)
            var = variant_m.group(1) if variant_m else "blue"
            inner_m = re.search(r'>([\s\S]*?)</Badge>', full)
            label = inner_m.group(1).strip() if inner_m else (re.search(r'label=["\'](.*?)["\']', full) or [None, ""])[1]

            color_classes = {
                "blue": "bg-blue-50 text-blue-700 border border-blue-200/80",
                "trabalho": "bg-blue-50 text-blue-700 border border-blue-200/80",
                "green": "bg-emerald-50 text-emerald-700 border border-emerald-200/80",
                "sucesso": "bg-emerald-50 text-emerald-700 border border-emerald-200/80",
                "yellow": "bg-amber-50 text-amber-700 border border-amber-200/80",
                "orange": "bg-orange-50 text-orange-700 border border-orange-200/80",
                "projeto": "bg-purple-50 text-purple-700 border border-purple-200/80",
                "red": "bg-rose-50 text-rose-700 border border-rose-200/80",
                "danger": "bg-rose-50 text-rose-700 border border-rose-200/80",
                "purple": "bg-purple-50 text-purple-700 border border-purple-200/80",
                "gray": "bg-slate-100 text-slate-700 border border-slate-200",
                "ideia": "bg-amber-50 text-amber-700 border border-amber-200/80",
                "info": "bg-blue-50 text-blue-700 border border-blue-200/80"
            }
            cls = color_classes.get(var.lower(), "bg-blue-50 text-blue-700 border border-blue-200/80")
            return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {cls}">{label}</span>'

        text = re.sub(r'<Badge\s+[^>]*?/>', badge_sub, text)
        text = re.sub(r'<Badge\s+[^>]*?>[\s\S]*?</Badge>', badge_sub, text)

        # Agrupar badges consecutivos em um container flex horizontal APENAS em linhas isoladas (fora de tabelas)
        def group_standalone_badges(m):
            block = m.group(0)
            if "|" in block:
                return block
            spans = block.strip()
            spans_clean = re.sub(r'\s*\n\s*', ' ', spans)
            return f'\n\n<div class="flex flex-wrap gap-2 my-3">{spans_clean}</div>\n\n'

        text = re.sub(
            r'(?:^[ \t]*<span class="inline-flex items-center px-2\.5 py-0\.5 rounded-full[^\"]*">[^<]+</span>[ \t]*(?:\r?\n|$))+',
            group_standalone_badges,
            text,
            flags=re.MULTILINE
        )
        return text

    def _transform_callouts(self, text: str) -> str:
        def callout_sub(m):
            attrs = m.group(1)
            body = m.group(2).strip()
            type_m = re.search(r'type=["\'](.*?)["\']', attrs)
            title_m = re.search(r'title=["\'](.*?)["\']', attrs)
            c_type = type_m.group(1).lower() if type_m else "info"
            c_title = title_m.group(1) if title_m else ""

            type_map = {
                "info": ("callout-info", "Nota Técnica"),
                "warn": ("callout-warn", "Atenção"),
                "warning": ("callout-warn", "Atenção"),
                "danger": ("callout-danger", "Alerta Crítico"),
                "success": ("callout-success", "Sucesso / Homologado"),
                "tip": ("callout-info", "Dica Técnica"),
                "important": ("callout-info", "Diretriz Importante")
            }
            css_class, default_title = type_map.get(c_type, ("callout-info", "Nota Técnica"))
            title_final = c_title if c_title else default_title

            body_html = markdown.markdown(body, extensions=['tables', 'sane_lists'])
            return f'<div class="callout {css_class}"><strong class="block font-semibold mb-1">{title_final}</strong><div class="text-sm opacity-90">{body_html}</div></div>\n'

        text = re.sub(r'<Callout\s+([^>]*?)>([\s\S]*?)</Callout>', callout_sub, text)
        return text

    def _transform_timelines(self, text: str) -> str:
        # 1. Transformar componentes JSX <Timeline ... />
        def timeline_sub(m):
            raw_block = m.group(1)
            item_blocks = re.split(r'\{\s*(?=date:)', raw_block)
            out = ['<div class="timeline mt-6">']
            for b in item_blocks:
                b = b.strip()
                if not b or not re.search(r'date:', b):
                    continue
                date_m = re.search(r'date:\s*["\'](.*?)["\']', b)
                title_m = re.search(r'title:\s*["\'](.*?)["\']', b)
                
                # Suporte a badge como objeto { label: "...", variant: "..." } ou como string direta
                badge = ''
                badge_obj_m = re.search(r'(?:badge|status):\s*\{[^}]*?label:\s*["\'](.*?)["\']', b)
                if badge_obj_m:
                    badge = badge_obj_m.group(1)
                else:
                    badge_str_m = re.search(r'(?:badge|status):\s*["\'](.*?)["\']', b)
                    if badge_str_m:
                        badge = badge_str_m.group(1)
                if not badge:
                    badge = 'Registro'

                desc_m = re.search(r'(?:content|description):\s*["\']([\s\S]*?)["\']\s*(?:,\s*(?:badge|status)|$)', b)
                desc = desc_m.group(1).strip() if desc_m else ''

                date = date_m.group(1) if date_m else ''
                title = title_m.group(1) if title_m else ''

                status_color = "bg-emerald-50 text-emerald-700 border-emerald-200" if badge.lower() in ("concluído", "concluido", "homologado", "ativo") else "bg-blue-50 text-blue-700 border-blue-200"
                out.append(f'''
  <div class="timeline-item">
    <div class="timeline-dot"></div>
    <div class="flex items-center gap-2 mb-1">
      <span class="font-semibold text-slate-800 text-sm font-mono">{date}</span>
      <span class="px-2 py-0.5 rounded text-[11px] font-medium {status_color}">{badge}</span>
    </div>
    <h4 class="font-semibold text-slate-900 text-base">{title}</h4>
    <p class="text-sm text-slate-600 mt-0.5">{desc}</p>
  </div>''')
            out.append('</div>\n')
            return '\n'.join(out)

        text = re.sub(r'<Timeline\s+(?:items|events)=\{\[([\s\S]*?)\]\}\s*/>', timeline_sub, text)

        # 2. Transformar listas Markdown dentro de seções de Linha do Tempo
        def markdown_timeline_section_sub(m):
            header = m.group(1)
            body = m.group(2)

            item_pattern = re.compile(
                r'^[ \t]*[-*]\s+\*{0,2}([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}/[0-9]{2}/[0-9]{4})\*{0,2}[:\s—–-]*(?:\[(.*?)\])?[:\s—–]*(.*)$',
                re.MULTILINE
            )

            items = list(item_pattern.finditer(body))
            if not items:
                return m.group(0)

            timeline_items = []
            for it in items:
                date = it.group(1).strip()
                badge = it.group(2) or "Concluído"
                rest = it.group(3).strip()

                split_m = re.match(r'^([^:—–]{4,60})[:—–]\s+(.+)$', rest)
                if split_m and not rest.startswith("http"):
                    title = split_m.group(1).strip()
                    desc = split_m.group(2).strip()
                else:
                    title = ""
                    desc = rest

                status_color = "bg-emerald-50 text-emerald-700 border-emerald-200" if badge.lower() in ("concluído", "concluido", "homologado", "ativo") else "bg-blue-50 text-blue-700 border-blue-200"

                timeline_items.append(f'''
  <div class="timeline-item">
    <div class="timeline-dot"></div>
    <div class="flex items-center gap-2 mb-1">
      <span class="font-semibold text-slate-800 text-sm font-mono">{date}</span>
      <span class="px-2 py-0.5 rounded text-[11px] font-medium {status_color}">{badge}</span>
    </div>
    {f'<h4 class="font-semibold text-slate-900 text-base">{title}</h4>' if title else ''}
    <p class="text-sm text-slate-600 mt-0.5">{desc}</p>
  </div>''')

            rendered_timeline = '<div class="timeline mt-6">\n' + '\n'.join(timeline_items) + '\n</div>\n'
            new_body = item_pattern.sub('', body).strip()
            if new_body:
                return f"{header}\n\n{rendered_timeline}\n\n{new_body}\n"
            else:
                return f"{header}\n\n{rendered_timeline}\n"

        text = re.sub(
            r'(##+[ \t]*[^\n]*?Linha do Tempo[^\n]*\n)([\s\S]*?)(?=(?:\n##+|\Z))',
            markdown_timeline_section_sub,
            text,
            flags=re.IGNORECASE
        )
        return text

    def _transform_deployment_timelines(self, text: str) -> str:
        def deploy_sub(m):
            raw = m.group(1)
            blocks = re.split(r'\{\s*(?=date:)', raw)
            items = []
            for b in blocks:
                b = b.strip()
                if not b or not re.search(r'date:', b):
                    continue
                date = (re.search(r'date:\s*["\'](.*?)["\']', b) or [None, ""])[1]
                version = (re.search(r'version:\s*["\'](.*?)["\']', b) or [None, ""])[1]
                title = (re.search(r'title:\s*["\'](.*?)["\']', b) or [None, ""])[1]
                author = (re.search(r'author:\s*["\'](.*?)["\']', b) or [None, ""])[1]
                status = (re.search(r'status:\s*["\'](.*?)["\']', b) or [None, ""])[1]
                summary = (re.search(r'summary:\s*["\']([\s\S]*?)["\']', b) or [None, ""])[1].strip()

                changes_m = re.search(r'changes:\s*\[([\s\S]*?)\]', b)
                changes_html = ""
                if changes_m:
                    ch_items = re.findall(r'["\']([\s\S]*?)["\']', changes_m.group(1))
                    ch_li = ''.join(f'<li class="text-xs text-slate-600 my-0.5">{c}</li>' for c in ch_items if c.strip())
                    if ch_li:
                        changes_html = f'<ul class="mt-2 pl-4 space-y-0.5 list-disc">{ch_li}</ul>'

                ver_badge = f'<span class="px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-brand-50 text-brand-700 border border-brand-200">{version}</span>' if version else ''
                status_badge = f'<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">{status}</span>' if status else ''

                items.append(f'''
<div class="timeline-item">
  <div class="timeline-dot"></div>
  <div class="flex flex-wrap items-center gap-2 mb-1">
    <span class="font-semibold text-slate-800 text-sm font-mono">{date}</span>
    {ver_badge}
    {status_badge}
    {f'<span class="text-xs text-slate-400">por {author}</span>' if author else ''}
  </div>
  <h4 class="font-semibold text-slate-900 text-base">{title}</h4>
  <p class="text-sm text-slate-600 mt-1">{summary}</p>
  {changes_html}
</div>''')

            inner = '\n'.join(items)
            return f'<div class="timeline mt-6">{inner}</div>\n'

        text = re.sub(r'<DeploymentTimeline\s+releases=\{\[([\s\S]*?)\]\}\s*/>', deploy_sub, text)
        return text

    def _transform_pontos_de_interesse(self, text: str) -> str:
        def extract_balanced_expr(block: str, prop_name: str) -> str:
            m = re.search(r'\b' + re.escape(prop_name) + r'\s*=\s*\{', block)
            if not m:
                return ""
            start_idx = m.end() - 1
            depth = 0
            in_quote = None
            for i in range(start_idx, len(block)):
                ch = block[i]
                if in_quote:
                    if ch == in_quote and block[i-1] != '\\':
                        in_quote = None
                elif ch in ('"', "'", '`'):
                    in_quote = ch
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        return block[start_idx+1:i].strip()
            return ""

        def parse_js_expr(raw: str):
            if not raw:
                return None
            raw = raw.strip()
            s = raw
            s = re.sub(r'//.*$', '', s, flags=re.M)
            s = re.sub(r'(\b[a-zA-Z_]\w*\b)\s*:', r'"\1":', s)
            s = re.sub(r',\s*([\]\}])', r'\1', s)
            try:
                return json.loads(s)
            except Exception:
                try:
                    import subprocess
                    cmd = ['node', '-e', f'console.log(JSON.stringify({raw}))']
                    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                    if res.returncode == 0:
                        return json.loads(res.stdout)
                except Exception:
                    pass
                return None

        def pdi_sub(m):
            block_str = m.group(1)
            tit_m = re.search(r'titulo=["\'](.*?)["\']', block_str)
            titulo = tit_m.group(1) if tit_m else "Ponto de Interesse"
            
            num_m = re.search(r'numero=["\'](.*?)["\']', block_str)
            numero = num_m.group(1) if num_m else ""
            
            desc_m = re.search(r'descricao=["\']([\s\S]*?)["\'](?=\s+[a-zA-Z0-9_]+=|\s*$)', block_str)
            descricao = desc_m.group(1).strip() if desc_m else ""
            
            per_raw = extract_balanced_expr(block_str, 'pericias')
            pericias = parse_js_expr(per_raw) if per_raw else []
            
            fer_raw = extract_balanced_expr(block_str, 'ferramentas')
            ferramentas = parse_js_expr(fer_raw) if fer_raw else []
            
            des_raw = extract_balanced_expr(block_str, 'desafioDeAcesso') or extract_balanced_expr(block_str, 'desafio') or extract_balanced_expr(block_str, 'acesso')
            desafio = parse_js_expr(des_raw) if des_raw else None
            
            mes_raw = extract_balanced_expr(block_str, 'mestre')
            if mes_raw:
                mestre = parse_js_expr(mes_raw)
            else:
                mes_str_m = re.search(r'mestre=["\']([\s\S]*?)["\'](?=\s+[a-zA-Z0-9_]+=|\s*$)', block_str)
                mestre = mes_str_m.group(1).strip() if mes_str_m else ""
            
            is_evidencia = bool(re.search(r'\[EVID[EÊ]NCIA-CHAVE\]', titulo, re.IGNORECASE))
            titulo_limpo = re.sub(r'\[EVID[EÊ]NCIA-CHAVE\]', '', titulo, flags=re.IGNORECASE).strip()
            
            cores_pericias = {
                'amarelo': '#fef3c7',
                'verde': '#dcfce7',
                'azul': '#dbeafe',
                'roxo': '#f3e8ff',
                'cinza': '#f3f4f6',
                'padrao': '#fef9c3'
            }

            html = []
            html.append('<div class="pdi-card my-6 rounded-md overflow-hidden border border-neutral-800 shadow-md font-sans">')
            
            # CABEÇALHO
            html.append('  <div class="bg-neutral-950 text-white p-4 flex items-start justify-between gap-4">')
            html.append('    <div class="flex items-start gap-3 flex-grow">')
            html.append('      <div class="shrink-0 w-6 h-6 mt-0.5 text-white">')
            html.append('        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" class="w-full h-full"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>')
            html.append('      </div>')
            html.append('      <div class="flex-grow">')
            html.append('        <div class="text-base font-extrabold uppercase tracking-wide flex items-center flex-wrap gap-2 text-white">')
            html.append(f'          <span>{titulo_limpo}</span>')
            if is_evidencia:
                html.append('          <span class="bg-amber-400 text-black text-xs font-black px-2 py-0.5 rounded tracking-wider">[EVIDÊNCIA-CHAVE]</span>')
            html.append('        </div>')
            if descricao:
                html.append(f'        <div class="text-xs leading-relaxed italic text-neutral-300 mt-1">{descricao}</div>')
            html.append('      </div>')
            html.append('    </div>')
            if numero:
                html.append(f'    <div class="shrink-0 bg-neutral-700 text-white text-xl font-black px-3 py-1.5 rounded flex items-center justify-center min-w-[2.5rem] tracking-wider">{numero}</div>')
            html.append('  </div>')

            # DESAFIO DE ACESSO
            if desafio:
                rotulo = desafio.get('rotulo') or desafio.get('tipo') or "MECÂNICA DE ACESSO"
                subtitulo = desafio.get('subtitulo') or ""
                titulo_desafio = desafio.get('titulo') or desafio.get('dificuldade') or ""
                destaque = desafio.get('destaque') or ""
                desc_desafio = desafio.get('descricao') or ""
                
                html.append('  <div class="bg-[#d68b78] border-b-2 border-neutral-800 text-neutral-900 flex flex-col md:flex-row w-full">')
                html.append('    <div class="md:w-1/3 p-3 border-b md:border-b-0 md:border-r border-[#944b39] flex flex-col justify-center gap-1">')
                html.append('      <div class="flex items-center gap-1.5 font-black text-xs text-black">')
                html.append('        <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4 shrink-0"><path fill-rule="evenodd" d="M12 1.5a5.25 5.25 0 00-5.25 5.25v3a3 3 0 00-3 3v6.75a3 3 0 003 3h10.5a3 3 0 003-3v-6.75a3 3 0 00-3-3v-3c0-2.9-2.35-5.25-5.25-5.25zm3.75 8.25v-3a3.75 3.75 0 00-7.5 0v3h7.5z" clip-rule="evenodd"/></svg>')
                html.append(f'        <span>{rotulo}</span>')
                html.append('      </div>')
                if titulo_desafio:
                    html.append(f'      <div class="font-black text-xs text-neutral-900 tracking-wide">✦ {titulo_desafio.upper()}</div>')
                if destaque:
                    html.append(f'      <div><span class="bg-black text-white px-2 py-0.5 text-xs font-black rounded">{destaque}</span></div>')
                if subtitulo:
                    html.append(f'      <div class="font-bold text-xs text-neutral-800">{subtitulo}</div>')
                if desc_desafio:
                    html.append(f'      <div class="text-xs italic text-neutral-800 leading-snug">{desc_desafio}</div>')
                html.append('    </div>')
                
                html.append('    <div class="md:w-2/3 flex flex-col justify-center">')
                if desafio.get('perguntas'):
                    for p_idx, p_item in enumerate(desafio['perguntas']):
                        bb = 'border-b border-[#944b39]' if p_idx < len(desafio['perguntas']) - 1 else ''
                        html.append(f'      <div class="p-2.5 text-center flex flex-col items-center gap-1 {bb}">')
                        html.append(f'        <div class="font-extrabold text-xs text-black">{p_item.get("pergunta", "")}</div>')
                        if p_item.get('respostas'):
                            for r in p_item['respostas']:
                                html.append(f'        <span class="bg-emerald-200 text-emerald-900 font-bold text-xs px-2 py-0.5 rounded">{r}</span>')
                        elif p_item.get('resposta'):
                            html.append(f'        <span class="bg-emerald-200 text-emerald-900 font-bold text-xs px-2 py-0.5 rounded">{p_item["resposta"]}</span>')
                        html.append('      </div>')
                elif desafio.get('opcoes'):
                    for o_idx, op in enumerate(desafio['opcoes']):
                        texto = op if isinstance(op, str) else f"{op.get('acao', '')}: {op.get('detalhe', '')}"
                        bb = 'border-b border-[#b86b58]' if o_idx < len(desafio['opcoes']) - 1 else ''
                        html.append(f'      <div class="p-2 font-bold text-xs text-black leading-snug {bb}">{texto}</div>')
                elif desafio.get('tabela'):
                    tab = desafio['tabela']
                    html.append('      <table class="w-full text-xs m-0 border-collapse">')
                    html.append('        <thead><tr class="bg-[#c57864] text-black font-black border-b border-[#a35a49]">')
                    html.append(f'          <th class="p-1.5 text-center border-r border-[#a35a49]">{tab.get("coluna1", "ROLAGEM")}</th>')
                    html.append(f'          <th class="p-1.5 text-left">{tab.get("coluna2", "EQUAÇÃO")}</th>')
                    html.append('        </tr></thead><tbody>')
                    for r_idx, row in enumerate(tab.get('linhas', [])):
                        bb = 'border-b border-[#b86b58]' if r_idx < len(tab['linhas']) - 1 else ''
                        resp = f' = <strong class="text-emerald-800">{row["resposta"]}</strong>' if row.get('resposta') else ''
                        html.append(f'        <tr class="{bb}"><td class="p-1.5 text-center font-bold border-r border-[#b86b58]">{row.get("rolagem", "")}</td><td class="p-1.5 font-bold">{row.get("expressao", "")}{resp}</td></tr>')
                    html.append('        </tbody></table>')
                html.append('    </div>')
                html.append('  </div>')

            # QUADRO DE PERÍCIAS
            if pericias:
                html.append('  <div class="overflow-x-auto">')
                html.append('    <table class="w-full text-xs m-0 border-collapse leading-normal">')
                html.append('      <thead><tr class="bg-neutral-800 text-white font-bold">')
                html.append('        <th class="p-2 text-left border-r border-neutral-700 w-1/4">Perícia</th>')
                html.append('        <th class="p-2 text-center border-r border-neutral-700 w-16">DT</th>')
                html.append('        <th class="p-2 text-left">Informação</th>')
                html.append('      </tr></thead><tbody>')
                for g_idx, grupo in enumerate(pericias):
                    cor_bg = cores_pericias.get(grupo.get('cor', ''), '#fef3c7' if g_idx % 2 == 0 else '#dcfce7')
                    raw_itens = grupo.get('itens')
                    if raw_itens and isinstance(raw_itens, list):
                        itens = []
                        for it in raw_itens:
                            dt_val = it.get('dt') or it.get('dificuldade') or '-'
                            info_val = it.get('info') or it.get('descricao') or it.get('informacao') or ''
                            itens.append({'dt': dt_val, 'info': info_val})
                    else:
                        dt_val = grupo.get('dt') or grupo.get('dificuldade') or '-'
                        info_val = grupo.get('info') or grupo.get('descricao') or grupo.get('informacao') or ''
                        itens = [{'dt': dt_val, 'info': info_val}]

                    total_linhas = len(itens)
                    is_trancado = grupo.get('trancado') or '🔒' in str(grupo.get('nome', ''))
                    nome_pericia = re.sub(r'🔒', '', str(grupo.get('nome', 'Perícia'))).strip()
                    condicao = grupo.get('condicao', '')
                    
                    for i_idx, item in enumerate(itens):
                        html.append(f'      <tr style="background-color: {cor_bg};" class="text-neutral-900 border-b border-neutral-300">')
                        if i_idx == 0:
                            html.append(f'        <td rowspan="{total_linhas}" class="p-2 border-r border-neutral-300 font-bold align-middle">')
                            html.append('          <div class="flex flex-col gap-0.5">')
                            html.append(f'            <div class="flex items-center gap-1"><span>{nome_pericia}</span>')
                            if is_trancado:
                                html.append('              <svg viewBox="0 0 24 24" fill="currentColor" class="w-3.5 h-3.5 shrink-0" title="Trancado"><path fill-rule="evenodd" d="M12 1.5a5.25 5.25 0 00-5.25 5.25v3a3 3 0 00-3 3v6.75a3 3 0 003 3h10.5a3 3 0 003-3v-6.75a3 3 0 00-3-3v-3c0-2.9-2.35-5.25-5.25-5.25zm3.75 8.25v-3a3.75 3.75 0 00-7.5 0v3h7.5z" clip-rule="evenodd"/></svg>')
                            html.append('            </div>')
                            if condicao:
                                html.append(f'            <span class="text-[0.7rem] font-medium text-neutral-600">{condicao}</span>')
                            html.append('          </div></td>')
                        html.append(f'        <td class="p-2 text-center font-extrabold border-r border-neutral-300 align-middle">{item["dt"]}</td>')
                        html.append(f'        <td class="p-2 align-middle text-neutral-800">{item["info"]}</td>')
                        html.append('      </tr>')
                html.append('    </tbody></table>')
                html.append('  </div>')

            # FERRAMENTAS FORENSES
            if ferramentas:
                html.append('  <div class="w-full overflow-x-auto">')
                html.append('    <div class="bg-[#2e4e68] text-white text-center font-black text-xs tracking-wider uppercase py-1 border-t border-b border-[#1a3348]">FERRAMENTAS</div>')
                html.append('    <table class="w-full text-xs m-0 border-collapse leading-normal"><tbody>')
                for f_idx, f_item in enumerate(ferramentas):
                    bb = 'border-b border-[#335570]' if f_idx < len(ferramentas) - 1 else ''
                    param = f_item.get('parametro') or f_item.get('detalhe') or (f'Sequência mínima: {f_item["sequencia"]}' if f_item.get('sequencia') else '')
                    html.append(f'      <tr class="bg-[#4a6f8c] text-white {bb}">')
                    html.append('        <td class="p-2.5 border-r border-[#335570] font-bold w-1/4 align-middle">')
                    html.append(f'          <div class="flex flex-col gap-0.5"><span class="font-extrabold">{f_item.get("nome", "")}</span>')
                    if param:
                        html.append(f'            <span class="text-[0.7rem] text-sky-100 font-medium">{param}</span>')
                    html.append('          </div></td>')
                    html.append(f'        <td class="p-2.5 text-slate-100 align-middle leading-relaxed">{f_item.get("info") or f_item.get("informacao") or f_item.get("descricao", "")}</td>')
                    html.append('      </tr>')
                html.append('    </tbody></table>')
                html.append('  </div>')

            # BASTIDORES DO MESTRE
            if mestre:
                html.append('  <div class="bg-neutral-200 text-neutral-800 p-3.5 flex gap-3 items-start border-t-2 border-neutral-950">')
                html.append('    <div class="shrink-0 w-6 h-6 mt-0.5 text-neutral-900">')
                html.append('      <svg viewBox="0 0 24 24" fill="currentColor" class="w-full h-full"><path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/></svg>')
                html.append('    </div>')
                html.append('    <div class="text-xs leading-relaxed text-neutral-900 flex-grow">')
                if isinstance(mestre, list):
                    for p_idx, p in enumerate(mestre):
                        mt = 'mt-1.5' if p_idx > 0 else ''
                        html.append(f'      <p class="m-0 {mt}">{p}</p>')
                else:
                    html.append(f'      <p class="m-0">{mestre}</p>')
                html.append('    </div>')
                html.append('  </div>')

            html.append('</div>\n')
            return '\n'.join(html)

        text = re.sub(r'<PontoDeInteresse\b([\s\S]*?)/>', pdi_sub, text)
        return text

    def _transform_param_tables(self, text: str) -> str:
        def table_sub(m):
            raw = m.group(1)
            obj_matches = re.findall(r'\{([^{}]+)\}', raw)
            if not obj_matches:
                return ''

            rows = []
            for obj_str in obj_matches:
                name = (re.search(r'name:\s*["\'](.*?)["\']', obj_str) or [None, ""])[1]
                env = (re.search(r'env:\s*["\'](.*?)["\']', obj_str) or [None, ""])[1]
                t_type = (re.search(r'type:\s*["\'](.*?)["\']', obj_str) or [None, ""])[1]
                req = (re.search(r'required:\s*(true|false)', obj_str, re.IGNORECASE) or [None, "false"])[1]
                ex = (re.search(r'example:\s*["\'](.*?)["\']', obj_str) or [None, ""])[1]
                desc = (re.search(r'description:\s*["\']([\s\S]*?)["\']', obj_str) or [None, ""])[1].strip()

                is_req = req.lower() == "true"
                req_badge = '<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">Sim</span>' if is_req else '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600">Não</span>'

                env_badge = f'<span class="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-purple-50 text-purple-700 border border-purple-200">{env}</span>' if env else ''

                rows.append(f'''
<tr class="hover:bg-slate-50/80 transition-colors">
  <td class="px-4 py-3 font-mono text-xs font-semibold text-brand-700">{name}</td>
  <td class="px-4 py-3 text-center">{env_badge}</td>
  <td class="px-4 py-3 font-mono text-xs text-slate-600">{t_type}</td>
  <td class="px-4 py-3 text-center">{req_badge}</td>
  <td class="px-4 py-3 text-xs text-slate-600">
    <div>{desc}</div>
    {f'<div class="mt-1 font-mono text-[11px] text-slate-400 bg-slate-100/70 px-2 py-0.5 rounded inline-block">Ex: {ex}</div>' if ex else ''}
  </td>
</tr>''')

            tbody = '\n'.join(rows)
            return f'''
<div class="my-6 overflow-x-auto rounded-xl border border-slate-200 shadow-sm bg-white">
  <table class="w-full text-left text-sm border-collapse m-0">
    <thead>
      <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <th class="px-4 py-3">Variável</th>
        <th class="px-4 py-3 text-center">Ambiente</th>
        <th class="px-4 py-3">Tipo</th>
        <th class="px-4 py-3 text-center">Obrigatório</th>
        <th class="px-4 py-3">Descrição & Exemplo</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-slate-100">
      {tbody}
    </tbody>
  </table>
</div>\n
'''

        text = re.sub(r'<ParamTable\s+params=\{\[([\s\S]*?)\]\}\s*/>', table_sub, text)
        return text

    def _transform_linkcards(self, text: str) -> str:
        def linkcard_sub(m):
            attrs = m.group(1)
            title = (re.search(r'title=["\'](.*?)["\']', attrs) or [None, "Link"])[1]
            desc = (re.search(r'description=["\'](.*?)["\']', attrs) or [None, ""])[1]
            href = (re.search(r'href=["\'](.*?)["\']', attrs) or [None, "#"])[1]
            return f'''
<a href="{href}" class="block p-4 my-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl transition-colors no-underline">
  <div class="font-semibold text-brand-600 text-sm">{title}</div>
  <div class="text-xs text-slate-500 mt-1">{desc}</div>
  <div class="text-[11px] text-slate-400 font-mono mt-1">{href}</div>
</a>
'''
        text = re.sub(r'<LinkCard\s+([^>]*?)/>', linkcard_sub, text)
        return text

    def _transform_checkboxes(self, text: str) -> str:
        """Converte itens de tarefa markdown - [x] e - [ ] para ícones estilizados."""
        def checked_sub(m):
            return f'* <span class="task-checkbox checked">☑</span> {m.group(1)}'
        def unchecked_sub(m):
            return f'* <span class="task-checkbox unchecked">☐</span> {m.group(1)}'

        text = re.sub(r'^\s*[-*]\s+\[[xX]\]\s+(.*)$', checked_sub, text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[-*]\s+\[\s*\]\s+(.*)$', unchecked_sub, text, flags=re.MULTILINE)
        return text

    def _transform_clickup_components(self, text: str) -> str:
        # 1. ClickUpTaskHeader
        def header_sub(m):
            raw = m.group(1)
            task_id = (re.search(r'taskId=["\'](.*?)["\']', raw) or [None, ""])[1]
            task_url = (re.search(r'taskUrl=["\'](.*?)["\']', raw) or [None, ""])[1]
            status = (re.search(r'status=["\'](.*?)["\']', raw) or [None, "Ativo"])[1]
            priority = (re.search(r'priority=["\'](.*?)["\']', raw) or [None, "normal"])[1]
            folder = (re.search(r'folder=["\'](.*?)["\']', raw) or [None, ""])[1]
            t_list = (re.search(r'list=["\'](.*?)["\']', raw) or [None, ""])[1]
            assignee = (re.search(r'assignee=["\'](.*?)["\']', raw) or [None, ""])[1]

            status_color = "bg-amber-50 text-amber-700 border-amber-200" if "aprov" in status.lower() or "espera" in status.lower() else "bg-emerald-50 text-emerald-700 border-emerald-200"
            prio_color = "text-rose-600 bg-rose-50 border-rose-200" if priority.lower() in ("high", "urgent") else "text-slate-600 bg-slate-100 border-slate-200"

            return f'''
<div class="my-6 p-4 bg-slate-50 border border-slate-200 rounded-xl shadow-xs">
  <div class="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
    <div class="flex items-center gap-2">
      <span class="font-mono text-xs font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">ClickUp #{task_id}</span>
      {f'<a href="{task_url}" target="_blank" class="text-xs text-brand-600 hover:underline">Abrir no ClickUp ↗</a>' if task_url else ''}
    </div>
    <div class="flex items-center gap-2">
      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border {status_color}">{status}</span>
      <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border {prio_color}">Prioridade: {priority.title()}</span>
    </div>
  </div>
  <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3 text-xs text-slate-600">
    <div><span class="text-slate-400 block text-[11px]">Localização:</span> {folder} / {t_list}</div>
    <div><span class="text-slate-400 block text-[11px]">Responsável:</span> {assignee}</div>
    <div><span class="text-slate-400 block text-[11px]">Ambiente:</span> Produção / K8s</div>
  </div>
</div>\n'''
        text = re.sub(r'<ClickUpTaskHeader\s+([\s\S]*?)/>', header_sub, text)

        # 2. ClickUpTaskCard
        def card_sub(m):
            raw = m.group(1)
            code = (re.search(r'code=["\'](.*?)["\']', raw) or [None, "TASK"])[1]
            title = (re.search(r'title=["\'](.*?)["\']', raw) or [None, "Tarefa"])[1]
            href = (re.search(r'href=["\'](.*?)["\']', raw) or [None, "#"])[1]
            if href.endswith(".mdx"):
                href = href[:-4] + ".html"
            clickup_url = (re.search(r'clickupUrl=["\'](.*?)["\']', raw) or [None, ""])[1]
            status = (re.search(r'status=["\'](.*?)["\']', raw) or [None, "Concluído"])[1]
            folder = (re.search(r'folder=["\'](.*?)["\']', raw) or [None, ""])[1]
            t_list = (re.search(r'list=["\'](.*?)["\']', raw) or [None, ""])[1]
            assignee = (re.search(r'assignee=["\'](.*?)["\']', raw) or [None, ""])[1]
            due = (re.search(r'dueDate=["\'](.*?)["\']', raw) or [None, ""])[1]

            prog_m = re.search(r'progress=\{\{\s*completed:\s*(\d+)\s*,\s*total:\s*(\d+)\s*\}\}', raw)
            completed = int(prog_m.group(1)) if prog_m else 0
            total = int(prog_m.group(2)) if prog_m else 0
            pct = int((completed / total) * 100) if total > 0 else 100

            status_color = "bg-emerald-50 text-emerald-700 border-emerald-200" if "conclu" in status.lower() else "bg-amber-50 text-amber-700 border-amber-200"

            return f'''
<div class="my-4 p-4 bg-white hover:bg-slate-50/80 border border-slate-200 rounded-xl transition-all shadow-xs">
  <div class="flex flex-wrap items-center justify-between gap-2">
    <div class="flex items-center gap-2">
      <a href="{href}" class="font-mono text-xs font-bold text-brand-700 bg-brand-50 px-2.5 py-1 rounded border border-brand-200 hover:underline">{code}</a>
      <a href="{href}" class="font-semibold text-slate-900 text-sm hover:text-brand-600 no-underline">{title}</a>
    </div>
    <div class="flex items-center gap-2">
      <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border {status_color}">{status}</span>
      {f'<a href="{clickup_url}" target="_blank" class="text-xs text-slate-400 hover:text-brand-600">ClickUp ↗</a>' if clickup_url else ''}
    </div>
  </div>
  <div class="flex flex-wrap items-center justify-between gap-4 mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
    <div class="flex items-center gap-4">
      <span>Local: {folder} / {t_list}</span>
      <span>Responsável: {assignee}</span>
      {f'<span>Prazo: {due}</span>' if due else ''}
    </div>
    <div class="flex items-center gap-2">
      <span class="font-mono text-[11px] text-slate-400">{completed}/{total} ({pct}%)</span>
      <div class="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div class="h-full bg-brand-500 rounded-full" style="width: {pct}%"></div>
      </div>
    </div>
  </div>
</div>\n'''
        text = re.sub(r'<ClickUpTaskCard\s+([\s\S]*?)/>', card_sub, text)

        # 3. ClickUpChecklist
        def checklist_sub(m):
            raw = m.group(1)
            title = (re.search(r'title=["\'](.*?)["\']', raw) or [None, "Checklist de Tarefas"])[1]
            item_regex = re.compile(r'\{\s*text:\s*["\']([\s\S]*?)["\']\s*,\s*done:\s*(true|false)\s*(?:,\s*tag:\s*["\'](.*?)["\'])?\s*\}', re.IGNORECASE)
            items = []
            for item in item_regex.finditer(raw):
                text_item = item.group(1).strip()
                done = item.group(2).lower() == "true"
                tag = item.group(3) or ""
                check_icon = '<span class="text-emerald-600 font-bold">☑</span>' if done else '<span class="text-slate-400">☐</span>'
                tag_badge = f'<span class="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-600 border border-slate-200">{tag}</span>' if tag else ''
                items.append(f'''
<li class="flex items-start gap-2.5 py-1.5 text-sm text-slate-700">
  {check_icon}
  <span class="flex-1">{text_item}</span>
  {tag_badge}
</li>''')
            inner = '\n'.join(items)
            return f'''
<div class="my-6 p-4 bg-slate-50/60 border border-slate-200 rounded-xl">
  <div class="font-semibold text-slate-900 text-sm mb-3">
    <span>{title}</span>
  </div>
  <ul class="divide-y divide-slate-100 m-0 p-0 list-none">
    {inner}
  </ul>
</div>\n'''
        text = re.sub(r'<ClickUpChecklist\s+([\s\S]*?)/>', checklist_sub, text)

        # 4. ClickUpActivityFeed
        def activity_sub(m):
            raw = m.group(1)
            act_regex = re.compile(
                r'\{\s*author:\s*["\'](.*?)["\']\s*,\s*type:\s*["\'](.*?)["\']\s*,\s*date:\s*["\'](.*?)["\']\s*,\s*badge:\s*["\'](.*?)["\']\s*,\s*title:\s*["\'](.*?)["\']\s*,\s*content:\s*["\']([\s\S]*?)["\']\s*\}'
            )
            activities = []
            for act in act_regex.finditer(raw):
                author = act.group(1)
                a_type = act.group(2)
                date = act.group(3)
                badge = act.group(4)
                title = act.group(5)
                content = act.group(6).strip()
                author_tag = '<span class="text-[10px] text-slate-400 font-mono">[Bot]</span> ' if a_type == "bot" else ''

                activities.append(f'''
<div class="timeline-item">
  <div class="timeline-dot"></div>
  <div class="flex items-center gap-2 mb-1">
    <span class="font-semibold text-slate-800 text-xs">{author_tag}{author}</span>
    <span class="text-slate-400 text-xs">• {date}</span>
    {f'<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">{badge}</span>' if badge else ''}
  </div>
  <h4 class="font-semibold text-slate-900 text-sm">{title}</h4>
  <p class="text-xs text-slate-600 mt-1 leading-relaxed">{content}</p>
</div>''')
            inner = '\n'.join(activities)
            return f'''
<div class="my-6 p-4 bg-slate-50/40 border border-slate-200 rounded-xl">
  <div class="font-semibold text-slate-900 text-sm mb-3">Feed de Atividades & Interações ClickUp</div>
  <div class="timeline mt-2">{inner}</div>
</div>\n'''
        text = re.sub(r'<ClickUpActivityFeed\s+([\s\S]*?)/>', activity_sub, text)
        return text

    def _protect_math(self, text: str) -> str:
        """Protege fórmulas matemáticas antes do parser Markdown, ignorando moedas (R$) e variáveis de shell (${VAR})."""
        def block_math(m):
            key = f"MATHBLOCKPLACEHOLDER{len(self.math_placeholders)}XYZ"
            self.math_placeholders[key] = f"\\[{m.group(1).strip()}\\]"
            return f"\n\n{key}\n\n"
        text = re.sub(r'\$\$([\s\S]*?)\$\$', block_math, text)

        def inline_math(m):
            key = f"MATHINLINEPLACEHOLDER{len(self.math_placeholders)}XYZ"
            self.math_placeholders[key] = f"\\({m.group(1).strip()}\\)"
            return key
        # Não casa se o $ estiver precedido por letras/dólares, se começar com espaço, crase ou { (evita ${VAR}), ou se tiver crases dentro
        math_pattern = re.compile(r'(?<![a-zA-Z0-9\\_\$])\$(?![\s{`])([^$`\n]+?)(?<![\s`])\$')
        text = math_pattern.sub(inline_math, text)
        return text

    def _restore_math(self, html: str) -> str:
        """Restaura as fórmulas matemáticas protegidas pós-Markdown para o KaTeX processar no browser."""
        for key, formula in self.math_placeholders.items():
            if formula.startswith("\\["):
                html = html.replace(f"<p>{key}</p>", f'<div class="my-4 text-center overflow-x-auto">{formula}</div>').replace(key, formula)
            else:
                html = html.replace(key, formula)
        return html

    def _normalize_links(self, text: str) -> str:
        """Normaliza links relativos substituindo .mdx por .html e barras invertidas de Windows por barras normais."""
        def md_link_sub(m):
            label = m.group(1)
            url = m.group(2)
            if ".mdx" in label:
                label = label.replace(".mdx", ".html")
            if ".mdx" in url:
                url = url.replace(".mdx", ".html")
            if "\\" in url and not url.startswith("http"):
                url = url.replace("\\", "/")
            return f"[{label}]({url})"

        text = re.sub(r'\[([^\]]+)\]\(([^\)]+?)\)', md_link_sub, text)

        def href_sub(m):
            prefix = m.group(1)
            url = m.group(2)
            suffix = m.group(3)
            if ".mdx" in url:
                url = url.replace(".mdx", ".html")
            if "\\" in url and not url.startswith("http"):
                url = url.replace("\\", "/")
            return f"{prefix}{url}{suffix}"

        text = re.sub(r'(href=["\'])([^"\']+?)(["\'])', href_sub, text)
        return text

    def _fix_markdown_lists(self, content: str) -> str:
        """Garante compatibilidade de listas Markdown com a especificação Python-Markdown."""
        # 1. Normalizar sub-itens de 2 a 3 espaços para exatamente 4 espaços para que aninhem corretamente
        content = re.sub(r'^( {2,3}|\t)([-*]|\d+\.)\s+', r'    \2 ', content, flags=re.MULTILINE)

        # 2. Inserir linha em branco antes do primeiro item de lista se a linha anterior for texto comum
        lines = content.splitlines()
        out = []
        list_item_re = re.compile(r'^\s*(?:[-*]|\d+\.)\s+')
        for i, line in enumerate(lines):
            if i > 0 and list_item_re.match(line):
                prev = lines[i - 1].strip()
                # Se a linha anterior contém texto mas não é lista, cabeçalho, quote, tabela, horizontal rule ou código
                if prev and not list_item_re.match(prev) and not prev.startswith(('#', '>', '|', '```', '---', '===', '<div', '<p', '<ul', '<ol')):
                    out.append('')
            out.append(line)
        return '\n'.join(out)

    def _restore_code_and_mermaid(self, html: str) -> str:
        # 1. Restaurar Mermaid
        for key, chart in self.mermaid_placeholders.items():
            mermaid_html = f'''
<div class="mermaid-wrapper">
  <pre class="mermaid">
{chart}
  </pre>
</div>
'''
            html = html.replace(f"<p>{key}</p>", mermaid_html).replace(key, mermaid_html)

        # 2. Restaurar blocos de código
        for key, (lang, code) in self.code_placeholders.items():
            escaped_code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_html = f'''
<div class="my-6 rounded-xl overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-sm shadow-sm">
  <div class="bg-slate-800 px-4 py-1.5 text-xs font-mono text-slate-400 border-b border-slate-700/60 flex justify-between">
    <span>{lang or 'code'}</span>
  </div>
  <pre class="p-4 overflow-x-auto font-mono text-xs leading-relaxed"><code>{escaped_code}</code></pre>
</div>
'''
            html = html.replace(f"<p>{key}</p>", code_html).replace(key, code_html)

        return html

    def _build_page(self, body_content: str) -> str:
        status = self.metadata.get("status", "Homologado")
        status_color = "bg-emerald-50 text-emerald-700 border border-emerald-200" if status.lower() in ("concluido", "ativo", "homologado", "producao") else "bg-blue-50 text-blue-700 border border-blue-200"

        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        replacements = {
            "{{TITLE}}": self.metadata.get("title", "Documento Técnico"),
            "{{CATEGORY_DISPLAY}}": self.metadata.get("category_display", "Documentação"),
            "{{STATUS}}": status.upper(),
            "{{STATUS_BADGE_CLASS}}": status_color,
            "{{UPDATED_AT}}": self.metadata.get("updatedAt", "2026-10-15"),
            "{{AUTHOR}}": self.metadata.get("author", "Victor Rubinec"),
            "{{CLIENT}}": self.metadata.get("client", "Knowledge OS"),
            "{{VERSION}}": self.metadata.get("version", "v2.0"),
            "{{CONTENT}}": body_content
        }

        output = template
        for k, v in replacements.items():
            output = output.replace(k, str(v))

        return output


LOTES = {
    0: [
        "starter-kit/exemplos/01-ata-reuniao-arquitetura.mdx",
        "starter-kit/exemplos/02-tarefa-autenticacao-jwt.mdx",
        "00-meta/TEMPLATE_TAREFA.mdx",
        "00-meta/TEMPLATE_NOTA.mdx",
        "00-meta/TEMPLATE_PROJETO_TRIADE.mdx"
    ],
    1: [
        "studio-kustom/README.mdx",
        "studio-kustom/01-negocio-e-operacao/auditoria-catalogo-shopee-e-produtos.mdx",
        "studio-kustom/01-negocio-e-operacao/maquinario-insumos-e-fluxo-produtivo.mdx",
        "studio-kustom/01-negocio-e-operacao/plano-pesquisa-contexto-loja-e-gestao-pedidos.mdx",
        "studio-kustom/02-engine-e-arquitetura/arquitetura-tecnologica-confiabilidade-shopee.mdx",
        "studio-kustom/02-engine-e-arquitetura/catalogo-capacidades-studio-kustom-engine.mdx",
        "studio-kustom/02-engine-e-arquitetura/diretriz-artistica-e-sistema-de-cores.mdx",
        "studio-kustom/02-engine-e-arquitetura/escopo-mockup-3d-threejs.mdx",
        "studio-kustom/02-engine-e-arquitetura/especificacao-catalogo-3d-e-correcoes-layout.mdx",
        "studio-kustom/02-engine-e-arquitetura/planejamento-mestre-studio-kustom-engine-saas.mdx",
        "studio-kustom/02-engine-e-arquitetura/upscaling-auto-studio-diagnostico-escopo.mdx",
        "studio-kustom/03-agente-ia-e-governanca/plano-acao-governanca-marcas-e-titulos.mdx",
        "studio-kustom/03-agente-ia-e-governanca/plano-desenvolvimento-agente-autonomo-engine.mdx",
        "studio-kustom/03-agente-ia-e-governanca/proposta-projeto-studio-kustom-engine-agente-ia.mdx"
    ],
    2: [
        "trabalho/join4/clientes/atlantica/automacoes/automacao-capere-trend.mdx",
        "trabalho/join4/clientes/atlantica/automacoes/automacao-rds-conciliacao-totvs.mdx",
        "trabalho/join4/clientes/atlantica/automacoes/automacao-tarifario-totvs-lecom.mdx",
        "trabalho/join4/clientes/atlantica/automacoes/dossie-transicao-automacoes-csc-capere-rds.mdx",
        "trabalho/join4/clientes/atlantica/erros/api-consultar-status-lecom.mdx",
        "trabalho/join4/clientes/atlantica/erros/automacao-d4sign-cadastro-investidor.mdx",
        "trabalho/join4/clientes/atlantica/erros/automacao-permissionamento-totvs.mdx",
        "trabalho/join4/clientes/atlantica/erros/automacao-publisher-cadastro-investidor.mdx",
        "trabalho/join4/clientes/atlantica/erros/automacao-tarifa-acordo-associacao.mdx",
        "trabalho/join4/clientes/atlantica/erros/automacao-totvs-cadastro-investidor.mdx",
        "trabalho/join4/clientes/atlantica/erros/checklist-erros-atlantica.mdx",
        "trabalho/join4/clientes/atlantica/erros/erro-hotel-nao-encontrado.mdx",
        "trabalho/join4/clientes/atlantica/erros/erro-lecom-tlsa-sem-opcoes.mdx",
        "trabalho/join4/clientes/atlantica/erros/formulario-comissoes-v5-campo-anexo.mdx",
        "trabalho/join4/clientes/atlantica/erros/formulario-lecom-cadastro-investidor.mdx",
        "trabalho/join4/clientes/atlantica/erros/relatorio-execucao-teste-totvs-cadastro-investidor.mdx",
        "trabalho/join4/clientes/atlantica/reuniao-comissoes-v5-esclarecimentos.mdx",
        "trabalho/join4/produto/consultas-portal/auditoria-comparativa-consultas-portal.mdx",
        "trabalho/join4/produto/consultas-portal/consultas-portal.mdx",
        "trabalho/join4/produto/relatorios/status-report-semana-42-2026.mdx",
        "trabalho/join4/produto/tarefas/README.mdx",
        "trabalho/join4/produto/tarefas/comunicado-tecnico-rotulo-a-resposta-liberacao-painel.mdx",
        "trabalho/join4/produto/tarefas/task-001-etl-piloto-docker-rebuild-guard.mdx",
        "trabalho/join4/produto/tarefas/task-002-migracao-etl-k8s-agendamento-envs.mdx",
        "trabalho/join4/produto/tarefas/task-003-etl-pendencias-rotulo-resposta.mdx",
        "trabalho/join4/produto/tarefas/task-004-portal-garantir-grupo-unico-departamento-multi-tenant.mdx",
        "trabalho/join4/produto/tarefas/task-005-etl-revisar-tabelas-gold-vazias.mdx"
    ],
    3: [
        "trabalho/triade/briefing-estrategico-posicionamento-e-site.mdx",
        "trabalho/triade/comercial/automacao-google-forms-discovery.mdx",
        "trabalho/triade/comercial/formulario-requisitos-tecnicos-descoberta.mdx",
        "trabalho/triade/comercial/modelo-contrato-prestacao-sustentacao-servicos.mdx",
        "trabalho/triade/comercial/roteiro-discovery-diagnostico-estudios.mdx",
        "trabalho/triade/comercial/termo-de-entrega-e-homologacao.mdx",
        "trabalho/triade/guia-metodologia-projetos-triade.mdx",
        "trabalho/triade/plataforma-interna-gestao-e-documentacao.mdx",
        "trabalho/triade/plataforma-interna/Sprints.mdx",
        "trabalho/triade/projetos/exemplo-projeto-tatuagem/exemplo-projeto-tatuagem.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/especificacao-escopo-eap-plataforma-completa.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/estimativa-horas-e-proposta-orcamentaria.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/guia-atuacao-negocios-po-luciano-bastos.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/planejamento-estrategico-lean-mvp-30-dias.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/proposta-comercial-planos-e-entregaveis-somos1.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/proposta-comercial-unificada-somos1.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/proposta-gestao-financeira-e-negocios-luciano.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/relatorio-diagnostico-as-is-alinhamento-po.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/relatorio-respostas-discovery-somos1.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/relatorio-tecnico-comercial-estimativa-decomposicao-horas-pacotes.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio/roteiro-apresentacao-pitch-deck-somos1.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/03-arquitetura-e-tech/relatorio-auditoria-baseline.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/03-arquitetura-e-tech/relatorio-versao-mobile-indicaai.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/04-prototipos/dossie-visual-baseline.mdx",
        "trabalho/triade/projetos/somos1-tattoo-studio/somos1-tattoo-studio.mdx",
        "trabalho/sites/guia-padrao-criacao-sites.mdx",
        "trabalho/sites/pessoal/cha-casa-nova/cha-casa-nova.mdx",
        "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/01-visao-geral-e-regras-de-negocio.mdx",
        "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/02-design-system-e-ui-ux.mdx",
        "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/03-mecanica-lista-presentes-e-pix.mdx",
        "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/04-arquitetura-tecnica-supabase-e-telegram.mdx",
        "trabalho/sites/pessoal/cha-casa-nova/conhecimentos/05-painel-admin-e-roteiro-de-testes.mdx",
        "trabalho/sites/pessoal/site-portfolio-pessoal/site-portfolio-pessoal.mdx",
        "trabalho/sites/trabalhos/amg/amg.mdx",
        "trabalho/sites/trabalhos/amg/guia-desenvolvimento-ia.mdx",
        "trabalho/sites/trabalhos/site-institucional-cliente/site-institucional-cliente.mdx"
    ],
    4: [
        "00-meta/GUIA_INTEGRACAO_ACP_CODEX.mdx",
        "00-meta/GUIA_STACK_TECNOLOGICA_RECOMENDADA.mdx",
        "00-meta/TEMPLATE_SITE.mdx",
        "pos-ia/00-visao-geral/ementa-e-cronograma.mdx",
        "pos-ia/00-visao-geral/matriz-competencias.mdx",
        "pos-ia/00-visao-geral/repositorios-github-unipds.mdx",
        "pos-ia/blueprints-e-padroes/README.mdx",
        "pos-ia/disciplinas/00-ambientacao/ambientacao-e-diretrizes.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/fundamentos-de-ia-e-llms.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-boas-praticas-arquitetura-modelos.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-kaggle.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-model-training-worker.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-normalizacao-e-pesos.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-teachable-machine.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-tensorflowjs.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/guia-tecnico-visao-computacional-yolo-webai.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/modulo-02-ml-dl-redes-neurais-e-categorizacao-alunos.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/modulo-03-sistemas-de-recomendacao-ecommerce-tensorflowjs.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/modulo-04-web-ml-duckhunt-yolo-selfplay.mdx",
        "pos-ia/disciplinas/01-fundamentos-de-ia-e-llms-para-programadores/modulo-05-inteligencia-artificial-na-web-algoritmos-geneticos-e-llms.mdx",
        "pos-ia/projetos/README.mdx",
        "projetos/automacao-busca-download-fontes.mdx",
        "projetos/automacao-emails-engine.mdx",
        "projetos/automacao-fontes/conhecimentos/arquitetura-pipeline-download-extracao.mdx",
        "projetos/automacao-fontes/conhecimentos/especificacao-cli-rich-typer.mdx",
        "projetos/automacao-fontes/conhecimentos/guia-apis-google-fonts-fontsource.mdx",
        "projetos/automacao-fontes/conhecimentos/guia-fonttools-metadados-opentype.mdx",
        "projetos/automacao-fontes/conhecimentos/guia-scraping-dafont-fontsquirrel.mdx",
        "projetos/automacao-videos-dark.mdx",
        "projetos/comparativo-previsao-renda-videos-dark-vs-depin-robux.mdx",
        "projetos/curriculos/curriculo-pedro-gustavo-analista-automacao-jr.mdx",
        "projetos/curriculos/planejamento-automatizador-vagas-copiloto.mdx",
        "projetos/darkcraft-engine/README.mdx",
        "projetos/darkcraft-engine/conhecimentos/01-arquitetura-e-pipeline.mdx",
        "projetos/darkcraft-engine/conhecimentos/02-sintese-voz-kokoro-tts.mdx",
        "projetos/darkcraft-engine/conhecimentos/03-motor-video-hyperframes.mdx",
        "projetos/darkcraft-engine/conhecimentos/04-roteirizacao-e-optmem.mdx",
        "projetos/darkcraft-engine/conhecimentos/05-mineracao-apify-e-outliers.mdx",
        "projetos/darkcraft-engine/conhecimentos/06-orquestracao-shard-cloud-e-youtube.mdx",
        "projetos/darkcraft-engine/conhecimentos/07-guia-configuracao-e-operacao.mdx",
        "projetos/darkcraft-engine/conhecimentos/08-analise-escopo-e-escala-canal-minecraft.mdx",
        "projetos/darkcraft-engine/conhecimentos/09-plano-de-acao-evolucao-cinematica-e-scraping.mdx",
        "projetos/ferramentas-inteligencia-videos-dark-e-depin.mdx",
        "projetos/gerador-fichas-ordem-2.mdx",
        "projetos/gerador-fichas-ordem-2/conhecimentos/01-anatomia-visual-e-posicionamento-a4.mdx",
        "projetos/gerador-fichas-ordem-2/conhecimentos/02-design-system-cores-fontes-e-fitas.mdx",
        "projetos/gerador-fichas-ordem-2/conhecimentos/03-regras-pericias-e-classes-ordem-2.mdx",
        "projetos/gerador-fichas-ordem-2/conhecimentos/04-json-schema-e-modelo-de-dados.mdx",
        "projetos/gerador-fichas-ordem-2/conhecimentos/05-arquitetura-engine-render-e-exportacao.mdx",
        "projetos/guia-formatacao-e-migracao-pc.mdx",
        "projetos/knowledge-os-v2/README.mdx",
        "projetos/knowledge-studio/especificacao-tecnica-knowledge-studio.mdx",
        "projetos/knowledge-studio/relatorio-conclusao-knowledge-studio.mdx",
        "projetos/maestro-orchestrator.mdx",
        "projetos/monitor-uptime-status.mdx",
        "projetos/monitor-uptime/conhecimentos/arquitetura-worker-retentativas.mdx",
        "projetos/monitor-uptime/conhecimentos/especificacao-status-page-api.mdx",
        "projetos/monitor-uptime/conhecimentos/guia-integracao-telegram-bot-api.mdx",
        "projetos/monitor-uptime/conhecimentos/guia-tecnico-socket-ssl-tls.mdx",
        "projetos/monitor-uptime/prompt-mestre-desenvolvimento-ia.mdx",
        "projetos/novos-escopos-producao-videos-dark-e-depin.mdx",
        "projetos/pesquisas/analise-artcraft-crafting-apps-storytold.mdx",
        "projetos/pesquisas/analise-dbx-database-client-mcp.mdx",
        "projetos/pesquisas/analise-ecossistema-free-for-dev-recursos-gratuitos.mdx",
        "projetos/pesquisas/analise-ferramentas-agentes-ia.mdx",
        "projetos/pesquisas/analise-ferramentas-starred-github.mdx",
        "projetos/pesquisas/analise-plataforma-aikido-security.mdx",
        "projetos/pesquisas/analise-plataforma-shardcloud.mdx",
        "projetos/pesquisas/arquitetura-engine-envio-emails-rubimail.mdx",
        "projetos/pesquisas/auditoria-tecnica-repositorio-e-branch-modernizacao.mdx",
        "projetos/pesquisas/canais-dark-youtube-monetizacao-renda.mdx",
        "projetos/pesquisas/como-o-google-ve-sites-arquitetura-seo.mdx",
        "projetos/pesquisas/comparativo-gemini-4-argon-vs-3-8-flash.mdx",
        "projetos/pesquisas/compra-de-dominios-brasil-com-combr.mdx",
        "projetos/pesquisas/ferramentas-envio-emails-sites-comparativo.mdx",
        "projetos/pesquisas/guia-definitivo-threejs-aplicacoes-limitacoes-mockups.mdx",
        "projetos/pesquisas/guia-depin-banda-ia-monetizacao-robux.mdx",
        "projetos/pesquisas/hospedagem-vps-comparativo.mdx",
        "projetos/pesquisas/ideias-ferramentas-micro-saas-renda-passiva.mdx",
        "projetos/pesquisas/mineracao-criptomoedas-pcs-notebooks.mdx",
        "projetos/pesquisas/pacotes-ia-google-antigravity-armazenamento.mdx",
        "projetos/pesquisas/planos-e-beneficios-github.mdx",
        "projetos/pesquisas/prospeccao-estrategia-hospedagem-freelancer.mdx",
        "projetos/pesquisas/relatorio-auditoria-seguranca-aikido.mdx",
        "projetos/pesquisas/viabilidade-minerador-gamificado-robux.mdx",
        "projetos/planejamento-desenvolvimento-cliente-depin-robux.mdx",
        "projetos/plano-acao-implementacao-stack-homologada.mdx",
        "projetos/plano-acao-integracao-ferramentas-starred.mdx",
        "projetos/plano-diagnostico-reinicializacao-pc.mdx"
    ],
    5: [
        "rpg/mesas/estacao-monte-calvario/ato-00-prologo.mdx",
        "rpg/mesas/estacao-monte-calvario/ato-01-primeiro-boletim.mdx",
        "rpg/mesas/estacao-monte-calvario/ato-02-investigacao-tripla.mdx",
        "rpg/mesas/estacao-monte-calvario/ato-03-terror-psicologico.mdx",
        "rpg/mesas/estacao-monte-calvario/ato-04-transmissao-da-verdade.mdx",
        "rpg/mesas/estacao-monte-calvario/cartas-de-itens-e-icones.mdx",
        "rpg/mesas/estacao-monte-calvario/cartas-para-impressao.mdx",
        "rpg/mesas/estacao-monte-calvario/estacao-monte-calvario-documento-mestre.mdx",
        "rpg/mesas/estacao-monte-calvario/guia-de-eventos-e-morte.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/01-arthur-meireles.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/02-clarice-brandao.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/03-otavio-ramos.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/04-beatriz-lins.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/05-hugo-santana.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/06-monica-viana.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/07-gabriel-rocha.mdx",
        "rpg/mesas/estacao-monte-calvario/personagens/08-helena-duarte.mdx",
        "rpg/mesas/estacao-monte-calvario/prompts-artes-personagens.mdx",
        "rpg/mesas/estacao-monte-calvario/resumo-da-mesa.mdx",
        "rpg/mesas/ordem-2-playtest/ato-1/a-maldicao-do-idolo-de-pedra-ato-1.mdx",
        "rpg/mesas/ordem-2-playtest/ato-2/a-maldicao-do-idolo-de-pedra-ato-2.mdx",
        "rpg/sistemas/ordem-2/criacao-personagem/guia-de-criacao-de-personagem.mdx",
        "rpg/sistemas/ordem-2/criacao-personagem/ocupacoes.mdx",
        "rpg/sistemas/ordem-2/criacao-personagem/perfis.mdx",
        "rpg/sistemas/ordem-2/criacao-personagem/progressao-e-niveis.mdx",
        "rpg/sistemas/ordem-2/documentos/gerador-fichas-e-historicos-design-system.mdx",
        "rpg/sistemas/ordem-2/exemplos/exemplo.mdx",
        "rpg/sistemas/ordem-2/itens-e-equipamentos/armas-e-equipamentos.mdx",
        "rpg/sistemas/ordem-2/itens-e-equipamentos/compendio-da-ordem-cris.mdx",
        "rpg/sistemas/ordem-2/itens-e-equipamentos/ferramentas-da-ordo-realitas.mdx",
        "rpg/sistemas/ordem-2/regras/atributos-e-regras-basicas.mdx",
        "rpg/sistemas/ordem-2/regras/combate-cenas-de-acao-e-perigo.mdx",
        "rpg/sistemas/ordem-paranormal/criacao-personagem/classes-e-trilhas.mdx",
        "rpg/sistemas/ordem-paranormal/criacao-personagem/origens.mdx",
        "rpg/sistemas/ordem-paranormal/habilidades/poderes-de-classe.mdx",
        "rpg/sistemas/ordem-paranormal/habilidades/poderes-paranormais.mdx",
        "rpg/sistemas/ordem-paranormal/habilidades/rituais.mdx",
        "rpg/sistemas/ordem-paranormal/itens-e-equipamentos/armas-e-modificacoes.mdx",
        "rpg/sistemas/ordem-paranormal/itens-e-equipamentos/itens-amaldicoados.mdx",
        "rpg/sistemas/ordem-paranormal/itens-e-equipamentos/patentes-e-inventario.mdx",
        "rpg/sistemas/ordem-paranormal/itens-e-equipamentos/protecoes-e-equipamento-geral.mdx",
        "rpg/sistemas/ordem-paranormal/regras/a-membrana.mdx",
        "rpg/sistemas/ordem-paranormal/regras/atributos-e-regras-basicas.mdx",
        "rpg/sistemas/ordem-paranormal/regras/combate-e-acoes.mdx",
        "rpg/sistemas/ordem-paranormal/regras/condicoes.mdx",
        "rpg/sistemas/ordem-paranormal/regras/elementos-e-afinidade.mdx",
        "rpg/sistemas/ordem-paranormal/regras/ferimentos-cura-e-morte.mdx",
        "rpg/sistemas/ordem-paranormal/regras/interludio-e-descanso.mdx",
        "rpg/sistemas/ordem-paranormal/regras/pericias.mdx",
        "rpg/sistemas/ordem-paranormal/regras/sanidade-e-traumas.mdx"
    ]
}


def main():
    parser = argparse.ArgumentParser(description="Conversor de MDX para Artefatos HTML5")
    parser.add_argument("file", nargs="?", help="Caminho do arquivo .mdx a ser convertido")
    parser.add_argument("--lote", type=int, choices=list(LOTES.keys()), help="Executa a conversão de um lote pré-definido")
    parser.add_argument("--no-backup", action="store_true", help="Não cria arquivo .bak de segurança")

    args = parser.parse_args()

    targets = []
    if args.lote is not None:
        targets = [WORKSPACE_DIR / p for p in LOTES[args.lote]]
        print(f"[LOTE {args.lote}] Iniciando conversão de {len(targets)} arquivos...")
    elif args.file:
        targets = [Path(args.file)]
    else:
        parser.print_help()
        sys.exit(1)

    for target in targets:
        try:
            converter = MDXToHTMLConverter(target, backup=not args.no_backup)
            out_file = converter.convert()
            rel = out_file.relative_to(WORKSPACE_DIR)
            print(f"[OK] Convertido com sucesso: {rel}")
        except Exception as e:
            print(f"[ERRO] Falha ao converter {target}: {e}")


if __name__ == "__main__":
    main()
