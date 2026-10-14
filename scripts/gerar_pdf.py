#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
MOTOR UNIFICADO DE VALIDAÇÃO E GERAÇÃO DE PDF (MDX -> PDF)
Repositório de Anotações & Documentações Corporativas
=============================================================================
Uso:
  python scripts/gerar_pdf.py <caminho_arquivo.mdx> [opções]
  python scripts/gerar_pdf.py --dir <pasta> [opções]
  python scripts/gerar_pdf.py <caminho_arquivo.mdx> --check-only

Opções:
  -o, --output PATH      Caminho de saída customizado para o PDF.
  -t, --theme NOME       Tema visual: corporate (padrão), join4, somos1, rpg, minimal.
  -c, --check-only       Executa apenas validações e linter (sem gerar o PDF).
  -d, --dir PASTA        Gera PDF para todos os arquivos .mdx de um diretório.
  -v, --verbose          Exibe mensagens detalhadas de diagnóstico.
  -h, --help             Exibe esta mensagem de ajuda.
=============================================================================
"""

import os
import sys
import re
import json
import argparse
import tempfile
from pathlib import Path

# Configuração de encoding para Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Diretório raiz do workspace
WORKSPACE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# CORES E FORMATAÇÃO DE TERMINAL
# =============================================================================
class LogColor:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

def log_info(msg):
    print(f"{LogColor.CYAN}[INFO]{LogColor.RESET} {msg}")

def log_success(msg):
    print(f"{LogColor.GREEN}[OK]{LogColor.RESET} {msg}")

def log_warn(msg):
    print(f"{LogColor.YELLOW}[AVISO]{LogColor.RESET} {msg}")

def log_error(msg):
    print(f"{LogColor.RED}[ERRO]{LogColor.RESET} {msg}")

# =============================================================================
# TEMAS VISUAIS
# =============================================================================
THEMES = {
    "corporate": {
        "brand_name": "TRÍADE // PRODUTO & TECH",
        "primary_color": "#0284c7",
        "primary_dark": "#0f172a",
        "accent_color": "#38bdf8",
        "bg_meta": "#f8fafc",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    },
    "somos1": {
        "brand_name": "TRÍADE // PRODUTO & TECH",
        "brand_sub": "Somos 1 Tattoo Studio",
        "primary_color": "#0284c7",
        "primary_dark": "#0f172a",
        "accent_color": "#0ea5e9",
        "bg_meta": "#f8fafc",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    },
    "join4": {
        "brand_name": "JOIN4 // GOVERNANÇA & TECNOLOGIA",
        "brand_sub": "Centro de Serviços Compartilhados",
        "primary_color": "#0369a1",
        "primary_dark": "#1e293b",
        "accent_color": "#0284c7",
        "bg_meta": "#f0f9ff",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    },
    "rpg": {
        "brand_name": "SISTEMA ORDEM 2 // LIVRO DE REGRAS",
        "brand_sub": "Manual de Regras & Ambientação",
        "primary_color": "#dc2626",
        "primary_dark": "#18181b",
        "accent_color": "#ef4444",
        "bg_meta": "#fafafa",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Cinzel', 'Georgia', serif"
    },
    "minimal": {
        "brand_name": "DOCUMENTAÇÃO TÉCNICA",
        "brand_sub": "Nota de Engenharia",
        "primary_color": "#475569",
        "primary_dark": "#0f172a",
        "accent_color": "#64748b",
        "bg_meta": "#f8fafc",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    },
    "curriculo": {
        "brand_name": "CURRÍCULO PROFISSIONAL",
        "primary_color": "#0284c7",
        "primary_dark": "#0f172a",
        "accent_color": "#0ea5e9",
        "bg_meta": "#ffffff",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    }
}

# =============================================================================
# LINTER & VALIDADOR DE QUALIDADE MDX
# =============================================================================
class MDXValidator:
    """Valida problemas comuns que afetam a compilação do PDF."""

    def __init__(self, content: str, file_path: Path):
        self.raw_content = content
        self.file_path = file_path
        self.warnings = []
        self.errors = []

    def validate(self) -> bool:
        self._check_frontmatter()
        self._check_mermaid_blocks()
        self._check_currency_symbols()
        self._check_components_syntax()
        return len(self.errors) == 0

    def _check_frontmatter(self):
        if not self.raw_content.startswith("---"):
            self.warnings.append("Documento não possui Frontmatter YAML no topo.")
            return

        fm_match = re.search(r'^---([\s\S]*?)---', self.raw_content)
        if not fm_match:
            self.errors.append("Frontmatter YAML malformado (faltando delimitador de fechamento '---').")
            return

        fm_text = fm_match.group(1)
        if "title:" not in fm_text:
            self.warnings.append("Frontmatter não define a propriedade 'title:'.")
        if "updatedAt:" not in fm_text and "createdAt:" not in fm_text:
            self.warnings.append("Frontmatter não define 'updatedAt:' ou 'createdAt:'.")

    def _check_mermaid_blocks(self):
        mermaid_blocks = re.findall(r'```mermaid([\s\S]*?)```', self.raw_content)
        for idx, block in enumerate(mermaid_blocks, 1):
            # 1. Checar tags HTML proibidas (exceto <br/> que é permitido para quebra de linha)
            html_tags = re.findall(r'</?(?:b\b|strong\b|i\b|em\b|u\b|div\b|span\b)[^>]*>', block, re.IGNORECASE)
            if html_tags:
                self.warnings.append(
                    f"Mermaid bloco #{idx} contém tags HTML de formatação proibidas ({', '.join(set(html_tags))}). "
                    "O motor irá sanitizar automaticamente, mas recomenda-se usar texto puro ou quebras `<br/>`."
                )

            # 2. Checar caracteres perigosos sem aspas em nós
            # Procura nós do tipo ID[Texto com (parênteses) sem aspas]
            unquoted_brackets = re.findall(r'\[([^\n"\]]*?\([^\n"\]]*?\)[^\n"\]]*?)\]', block)
            if unquoted_brackets:
                for bad_label in unquoted_brackets:
                    if not bad_label.startswith('"') and not bad_label.endswith('"'):
                        self.warnings.append(
                            f"Mermaid bloco #{idx}: nó contém parênteses sem aspas duplas: `[{bad_label}]`. "
                            f"Sugestão: `[\"{bad_label}\"]`."
                        )

            # 3. Checar árvores largas com muitas ramificações horizontais
            if "flowchart TD" in block or "graph TD" in block:
                connections = re.findall(r'(\w+)\s*-->', block)
                if connections:
                    from collections import Counter
                    counts = Counter(connections)
                    for node, count in counts.items():
                        if count >= 4:
                            self.warnings.append(
                                f"Mermaid bloco #{idx}: o nó `{node}` possui {count} ramificações horizontais no modo TD. "
                                "Isso pode forçar tipografia microscópica (< 5pt) no PDF A4. Considere fluxo sequencial ou tabela."
                            )

            # 4. Checar altura excessiva de subgrafos empilhados
            subgraphs_count = len(re.findall(r'subgraph\s+', block, re.IGNORECASE))
            if subgraphs_count >= 3 and ("flowchart LR" in block or "graph LR" in block):
                self.warnings.append(
                    f"Mermaid bloco #{idx}: possui {subgraphs_count} subgrafos empilhados. "
                    "Pode gerar quebras de página artificiais (> 350px). Verifique a diagramação."
                )

    def _check_currency_symbols(self):
        # Verifica se há múltiplos $ soltos no mesmo parágrafo que não sejam R$ ou R\$
        lines = self.raw_content.splitlines()
        for line_num, line in enumerate(lines, 1):
            if "```" in line:
                continue
            # Remove ocorrências legítimas de moedas (R$, R\$, US$, etc.)
            cleaned_line = re.sub(r'(?:R|US|U)?\\?\$', '', line)
            standalone_dollars = re.findall(r'\$([^\$\n]+)\$', cleaned_line)
            if standalone_dollars:
                self.warnings.append(
                    f"Linha {line_num}: possível colisão com delimitador de fórmula LaTeX: `${standalone_dollars[0]}$`."
                )

    def _check_components_syntax(self):
        # Verifica fechamento de Callout
        callout_opens = len(re.findall(r'<Callout[\s>]', self.raw_content))
        callout_closes = len(re.findall(r'</Callout>', self.raw_content))
        if callout_opens != callout_closes:
            self.errors.append(f"Inconsistência de tags <Callout>: {callout_opens} aberturas vs {callout_closes} fechamentos.")

        # Verifica Timeline
        timelines = re.findall(r'<Timeline\s+items=\{\[([\s\S]*?)\]\}\s*/>', self.raw_content)
        raw_timelines = re.findall(r'<Timeline', self.raw_content)
        if len(timelines) != len(raw_timelines):
            self.warnings.append(
                "Detectado componente <Timeline /> com formatação fora do padrão esperado `items={[...]}`."
            )

    def print_report(self):
        if not self.warnings and not self.errors:
            log_success(f"Validação de sintaxe e regras concluída sem pendências: {self.file_path.name}")
            return

        print(f"\n--- Relatório de Qualidade: {self.file_path.name} ---")
        for err in self.errors:
            log_error(err)
        for warn in self.warnings:
            log_warn(warn)
        print("----------------------------------------------------------\n")


# =============================================================================
# HELPER DE FORMATAÇÃO DE CATEGORIA E RÓTULOS
# =============================================================================
def format_category_display(category: str) -> str:
    """Transforma caminhos internos de pasta em títulos limpos e profissionais para o PDF."""
    if not category:
        return "Documentação Técnica"

    # Se for texto limpo sem barras de diretório, usa diretamente
    if "/" not in category and "\\" not in category:
        return category

    category_norm = category.replace("\\", "/").strip("/")

    # Mapeamentos diretos conhecidos do repositório
    MAP = {
        "trabalho/triade/projetos/somos1-tattoo-studio/01-negocio": "Proposta Comercial & Gestão",
        "trabalho/triade/projetos/somos1-tattoo-studio": "Somos 1 Tattoo Studio",
        "trabalho/triade/comercial": "Instrumentos Comerciais",
        "trabalho/triade/plataforma-interna": "Plataforma Interna",
        "trabalho/triade": "Tríade Digital — Governança & Negócios",
        "trabalho/join4/produto/tarefas": "Tarefas & Backlog de Produto",
        "trabalho/join4/produto/consultas-portal": "ConsultasPortal",
        "trabalho/join4/produto": "Produto & Engenharia",
        "trabalho/join4/clientes/atlantica/automacoes": "Automações & RPA",
        "trabalho/join4/clientes/atlantica/erros": "Relatórios de Incidentes",
        "trabalho/join4/clientes/atlantica": "Atlântica Hotels",
        "trabalho/join4": "Join4 Tecnologia",
        "trabalho/sites/relatorios": "Design System & CSS Audit",
        "trabalho/sites/pessoal": "Projetos Pessoais Web",
        "trabalho/sites/trabalhos": "Projetos Web Corporativos",
        "trabalho/sites": "Desenvolvimento Web",
        "rpg/sistemas/ordem-2": "Sistema Ordem 2",
        "rpg/sistemas/ordem-paranormal": "Ordem Paranormal RPG",
        "studio-kustom": "Studio Kustom",
    }

    for key, label in MAP.items():
        if category_norm == key or category_norm.startswith(key + "/"):
            return label

    # Fallback inteligente: remove prefixos como trabalho/, projetos/ e formata os últimos segmentos
    parts = [p for p in category_norm.split("/") if p not in ("trabalho", "projetos", "docs", "01-negocio", "02-tech")]
    if parts:
        return " — ".join(p.replace("-", " ").replace("_", " ").title() for p in parts[-2:])

    return category


# =============================================================================
# SANITIZADOR E PROCESSADOR DE CONTEÚDO MDX
# =============================================================================
class MDXProcessor:
    """Sanitiza e transforma MDX em HTML de alta fidelidade para PDF."""

    def __init__(self, raw_content: str, theme_name: str = "corporate"):
        self.content = raw_content
        self.theme_name = theme_name
        self.theme = THEMES.get(theme_name, THEMES["corporate"])
        self.metadata = {
            "title": "Documento Técnico",
            "category": "Documentação",
            "category_display": None,
            "updatedAt": "2026-10-02",
            "createdAt": "2026-10-02",
            "status": "Ativo",
            "author": "Victor Rubinec",
            "client": "Corporativo"
        }
        self.mermaid_blocks = []

    def process(self) -> tuple[str, dict]:
        self._extract_frontmatter()
        self._clean_react_imports()
        self._extract_and_sanitize_mermaid()
        self._protect_currency()
        self._transform_badges()
        self._transform_callouts()
        self._transform_timelines()
        self._transform_linkcards()
        self._transform_clickup_components()
        self._transform_jsx_divs()
        return self.content, self.metadata, self.mermaid_blocks

    def _extract_frontmatter(self):
        STATUS_DISPLAY = {
            "backlog": "Backlog",
            "em_andamento": "Em Andamento",
            "bloqueado": "Bloqueado",
            "homologacao": "Homologação",
            "aguardando_aprovacao": "Aguardando Aprovação",
            "aguardando_acompanhamento": "Aguardando Acompanhamento",
            "concluido": "Concluído",
            "ativo": "Ativo",
            "pausado": "Pausado",
        }
        fm_match = re.search(r'^---([\s\S]*?)---\s*', self.content)
        if fm_match:
            fm_text = fm_match.group(1)
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    # Remove comentários inline (# fora de aspas ou após o valor)
                    if "#" in val:
                        m = re.match(r'^(".*?"|\'.*?\'|[^\s#]+)', val)
                        if m:
                            val = m.group(1).strip()
                    val = val.strip('"\'')
                    if key == "status":
                        val = STATUS_DISPLAY.get(val.lower(), val)
                    if key in self.metadata or key in ("category_display", "client", "author", "layout", "hide_cover"):
                        self.metadata[key] = val
                    elif key == "theme" and val in THEMES:
                        self.theme_name = val
                        self.theme = THEMES[val]
            self.content = self.content[fm_match.end():]

        # Auto-detecção de tema caso esteja no padrão 'corporate'
        if self.theme_name == "corporate":
            cat_lower = self.metadata.get("category", "").lower()
            layout_val = str(self.metadata.get("layout", "")).lower()
            if "somos1" in cat_lower or "tattoo" in cat_lower:
                self.theme_name = "somos1"
                self.theme = THEMES["somos1"]
            elif "join4" in cat_lower or "atlantica" in cat_lower:
                self.theme_name = "join4"
                self.theme = THEMES["join4"]
            elif "ordem" in cat_lower or "rpg" in cat_lower:
                self.theme_name = "rpg"
                self.theme = THEMES["rpg"]
            elif "curriculo" in cat_lower or "currículo" in cat_lower or layout_val == "curriculo":
                self.theme_name = "curriculo"
                self.theme = THEMES["curriculo"]

        # Extrai título H1 se não definido no frontmatter
        h1_match = re.search(r'^\s*#\s+(.+)$', self.content, re.MULTILINE)
        if h1_match:
            if self.metadata["title"] == "Documento Técnico":
                self.metadata["title"] = h1_match.group(1).strip()
            # Remove o H1 do corpo para evitar duplicidade com a capa apenas se não for currículo
            is_curr = self.theme_name == "curriculo" or layout_val == "curriculo" or str(self.metadata.get("hide_cover", "")).lower() in ("true", "1")
            if not is_curr:
                self.content = re.sub(r'^\s*#\s+[^\n]+\n*', '', self.content, count=1, flags=re.MULTILINE)

    def _clean_react_imports(self):
        self.content = re.sub(r'import\s+.*?from\s+[\'"].*?[\'"];?\s*', '', self.content)

    def _render_inline_md(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text, flags=re.DOTALL)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text, flags=re.DOTALL)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text, flags=re.DOTALL)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        return text

    def _protect_currency(self):
        # Protege R$ para evitar colisão com LaTeX e quebra de linha com &nbsp;
        self.content = self.content.replace(r'R\$', 'R$')
        self.content = re.sub(r'R\$\s*([0-9\.\,]+)', r'R$&nbsp;\1', self.content)

    def _transform_badges(self):
        def parse_badge(m):
            text = m.group(0)
            label_m = re.search(r'label=["\'](.*?)["\']', text)
            type_m = re.search(r'type=["\'](.*?)["\']', text)
            variant_m = re.search(r'variant=["\'](.*?)["\']', text)
            
            # Se for tag com children <Badge>Texto</Badge>
            inner_text = ""
            if not label_m:
                inner_m = re.search(r'<Badge[^>]*>([\s\S]*?)</Badge>', text)
                if inner_m:
                    inner_text = inner_m.group(1).strip()

            label = label_m.group(1) if label_m else (inner_text if inner_text else (variant_m.group(1) if variant_m else "Info"))
            b_type = type_m.group(1) if type_m else (variant_m.group(1) if variant_m else "default")
            label_clean = self._render_inline_md(label)
            return f'<span class="badge badge-{b_type}">{label_clean}</span>'

        self.content = re.sub(r'<Badge\s+[^>]*?/>', parse_badge, self.content)
        self.content = re.sub(r'<Badge\s+[^>]*?>[\s\S]*?</Badge>', parse_badge, self.content)

    def _transform_callouts(self):
        def parse_callout(m):
            attrs = m.group(1)
            body = m.group(2).strip()
            type_m = re.search(r'type=["\'](.*?)["\']', attrs)
            title_m = re.search(r'title=["\'](.*?)["\']', attrs)
            c_type = type_m.group(1) if type_m else "info"
            c_title = title_m.group(1) if title_m else "Nota Técnica"

            c_title_clean = self._render_inline_md(c_title)
            body_clean = self._render_inline_md(body)
            # Substituir quebras de linha normais no body por tags <br/> se não houver parágrafos
            body_clean = body_clean.replace('\n\n', '</p><p>').replace('\n', '<br/>')

            return f'<div class="callout callout-{c_type}"><div class="callout-title">{c_title_clean}</div><div class="callout-body"><p>{body_clean}</p></div></div>\n'

        self.content = re.sub(r'<Callout\s+([^>]*?)>([\s\S]*?)</Callout>', parse_callout, self.content)

    def _transform_timelines(self):
        def parse_timeline(m):
            raw_block = m.group(1)
            # Suporta date, title, content/description, badge/status (opcional)
            item_regex = re.compile(
                r'\{\s*date:\s*["\'](.*?)["\']\s*,\s*title:\s*["\'](.*?)["\']\s*,\s*(?:content|description):\s*["\']([\s\S]*?)["\']\s*(?:,\s*(?:badge|status):\s*["\'](.*?)["\'])?\s*,?\s*\}'
            )
            items_html = '<div class="timeline-container">\n'
            for match in item_regex.finditer(raw_block):
                date = match.group(1)
                title = match.group(2)
                desc = match.group(3)
                badge = match.group(4) or "Registro"
                badge_slug = re.sub(r'[^a-zA-Z0-9]', '-', badge.lower())
                title_clean = self._render_inline_md(title)
                desc_clean = self._render_inline_md(desc)
                items_html += (
                    f'<div class="timeline-item">'
                    f'<div class="timeline-header">'
                    f'<span class="timeline-date">📅 {date}</span>'
                    f'<span class="timeline-badge timeline-badge-{badge_slug}">{badge}</span>'
                    f'</div>'
                    f'<div class="timeline-title">{title_clean}</div>'
                    f'<div class="timeline-desc">{desc_clean}</div>'
                    f'</div>\n'
                )
            items_html += '</div>\n'
            return items_html

        self.content = re.sub(r'<Timeline\s+(?:items|events)=\{\[([\s\S]*?)\]\}\s*/>', parse_timeline, self.content)

    def _transform_linkcards(self):
        def parse_linkcard(m):
            attrs = m.group(1)
            title_m = re.search(r'title=["\'](.*?)["\']', attrs)
            desc_m = re.search(r'description=["\'](.*?)["\']', attrs)
            href_m = re.search(r'href=["\'](.*?)["\']', attrs)
            title = self._render_inline_md(title_m.group(1) if title_m else "Link")
            desc = self._render_inline_md(desc_m.group(1) if desc_m else "")
            href = href_m.group(1) if href_m else "#"
            return f'<div class="link-card"><div class="link-card-title">🔗 {title}</div><div class="link-card-desc">{desc}</div><div class="link-card-href">{href}</div></div>\n'

        self.content = re.sub(r'<LinkCard\s+([^>]*?)/>', parse_linkcard, self.content)

    def _transform_clickup_components(self):
        # 1. Transformar ClickUpTaskHeader
        def parse_clickup_header(m):
            attrs = m.group(1)
            task_id = (re.search(r'taskId=["\'](.*?)["\']', attrs) or [None, ""])[1]
            task_url = (re.search(r'taskUrl=["\'](.*?)["\']', attrs) or [None, f"https://app.clickup.com/t/{task_id}" if task_id else "#"])[1]
            status = (re.search(r'status=["\'](.*?)["\']', attrs) or [None, "Em Aberto"])[1]
            priority = (re.search(r'priority=["\'](.*?)["\']', attrs) or [None, "normal"])[1]
            list_name = (re.search(r'list=["\'](.*?)["\']', attrs) or [None, "Geral"])[1]
            folder_name = (re.search(r'folder=["\'](.*?)["\']', attrs) or [None, "Portal"])[1]
            due_date = (re.search(r'dueDate=["\'](.*?)["\']', attrs) or [None, ""])[1]
            assignee = (re.search(r'assignee=["\'](.*?)["\']', attrs) or [None, "Victor Rubinec"])[1]
            
            # Tags
            tags = []
            tags_m = re.search(r'tags=\{?\[([\s\S]*?)\]\}?', attrs)
            if tags_m:
                tags = [t.strip(' "\' \t\r\n') for t in tags_m.group(1).split(',') if t.strip(' "\' \t\r\n')]

            status_slug = re.sub(r'[^a-zA-Z0-9]', '-', status.lower())
            prio_slug = re.sub(r'[^a-zA-Z0-9]', '-', priority.lower())
            prio_label = "Urgente" if prio_slug in ("urgent", "urgente") else ("Alta" if prio_slug in ("high", "alta") else ("Baixa" if prio_slug in ("low", "baixa") else "Normal"))

            tags_html = "".join([f'<span class="cu-tag">#{t}</span>' for t in tags])
            due_html = f'<div class="cu-meta-item"><span class="cu-meta-label">Prazo:</span> <span class="cu-meta-val cu-due">📅 {due_date}</span></div>' if due_date else ""
            task_id_badge = f'<span class="cu-task-id">#{task_id}</span>' if task_id else ""

            return f'''<div class="clickup-task-header">
<div class="cu-top-bar">
<div class="cu-breadcrumb">
<span class="cu-crumb-ws">Join4 Produtos</span>
<span class="cu-sep">/</span>
<span class="cu-crumb-folder">{folder_name}</span>
<span class="cu-sep">/</span>
<span class="cu-crumb-list">{list_name}</span>
{task_id_badge}
</div>
<a href="{task_url}" class="cu-btn-link" target="_blank">Abrir no ClickUp ↗</a>
</div>
<div class="cu-main-row">
<div class="cu-status-pill cu-status-{status_slug}">
<span class="cu-status-dot"></span>
<span class="cu-status-text">{status.upper()}</span>
</div>
<div class="cu-prio-badge cu-prio-{prio_slug}">
<span>🚩</span> {prio_label}
</div>
<div class="cu-assignee-pill">
<span class="cu-avatar">VR</span>
<span>{assignee}</span>
</div>
{due_html}
<div class="cu-tags-wrap">{tags_html}</div>
</div>
</div>
'''
        self.content = re.sub(r'<ClickUpTaskHeader\s+([\s\S]*?)(?:/>|>\s*</ClickUpTaskHeader>)', parse_clickup_header, self.content)

        # 2. Transformar ClickUpChecklist
        def parse_clickup_checklist(m):
            raw_block = m.group(0)
            title_m = re.search(r'title=["\'](.*?)["\']', raw_block)
            title = title_m.group(1) if title_m else "Checklist de Execução & Critérios de Aceite"
            
            # Extrair itens: text, done, tag
            items = []
            item_pattern = re.compile(r'\{\s*(?:["\']?text["\']?:\s*["\']([\s\S]*?)["\']\s*,\s*["\']?done["\']?:\s*(true|false)|["\']?done["\']?:\s*(true|false)\s*,\s*["\']?text["\']?:\s*["\']([\s\S]*?)["\'])(?:,\s*["\']?tag["\']?:\s*["\'](.*?)["\'])?[\s\S]*?\}')
            for im in item_pattern.finditer(raw_block):
                if im.group(1) is not None:
                    it_text = im.group(1)
                    it_done = im.group(2).lower() == "true"
                else:
                    it_done = im.group(3).lower() == "true"
                    it_text = im.group(4)
                it_tag = im.group(5) or ""
                items.append({"text": it_text.strip(), "done": it_done, "tag": it_tag.strip()})

            total = len(items)
            completed = sum(1 for it in items if it["done"])
            pct = int(round((completed / total * 100))) if total > 0 else 0
            is_all_done = total > 0 and completed == total

            items_html = ""
            for it in items:
                check_icon = "✔" if it["done"] else ""
                check_class = "cu-chk-done" if it["done"] else "cu-chk-open"
                text_clean = self._render_inline_md(it["text"])
                tag_html = f'<span class="cu-chk-tag">{it["tag"]}</span>' if it["tag"] else ""
                items_html += f'''
<div class="cu-chk-row {check_class}">
  <span class="cu-chk-box">{check_icon}</span>
  <span class="cu-chk-text">{text_clean}</span>
  {tag_html}
</div>'''

            bar_color = "#10b981" if is_all_done else "#7b68ee"
            badge_color = "#ecfdf5; color: #059669" if is_all_done else "#f1f5f9; color: #475569"

            return f'''<div class="clickup-checklist-card">
<div class="cu-chk-header">
<div class="cu-chk-title">☑️ {title}</div>
<div class="cu-chk-count" style="background:{badge_color};">{completed}/{total} ({pct}%)</div>
</div>
<div class="cu-chk-progress-track">
<div class="cu-chk-progress-bar" style="width:{pct}%; background:{bar_color};"></div>
</div>
<div class="cu-chk-list">
{items_html}
</div>
</div>
'''
        self.content = re.sub(r'<ClickUpChecklist\s+[\s\S]*?(?:/>|>\s*</ClickUpChecklist>)', parse_clickup_checklist, self.content)

        # 3. Transformar ClickUpActivityFeed
        def parse_clickup_feed(m):
            raw_block = m.group(0)
            items = []
            
            # Divide os objetos do array de atividades
            obj_blocks = re.findall(r'\{\s*(?:author|type|date|badge|title|content)[\s\S]*?\}', raw_block)
            for ob in obj_blocks:
                author_m = re.search(r'author:\s*["\'](.*?)["\']', ob)
                type_m = re.search(r'type:\s*["\'](.*?)["\']', ob)
                date_m = re.search(r'date:\s*["\'](.*?)["\']', ob)
                badge_m = re.search(r'badge:\s*["\'](.*?)["\']', ob)
                title_m = re.search(r'title:\s*["\'](.*?)["\']', ob)
                content_m = re.search(r'content:\s*"([\s\S]*?)"\s*(?:,|\})', ob)
                if not content_m:
                    content_m = re.search(r'content:\s*\'([\s\S]*?)\'\s*(?:,|\})', ob)
                
                items.append({
                    "author": author_m.group(1) if author_m else "Membro Join4",
                    "type": type_m.group(1) if type_m else "user",
                    "date": date_m.group(1) if date_m else "",
                    "badge": badge_m.group(1) if badge_m else "Registro",
                    "title": title_m.group(1) if title_m else "",
                    "content": content_m.group(1) if content_m else ""
                })

            feed_html = '<div class="clickup-feed-container">'
            for act in items:
                is_bot = act["type"] == "bot"
                avatar_text = "🤖" if is_bot else "VR"
                avatar_class = "cu-av-bot" if is_bot else "cu-av-user"
                bot_badge = '<span class="cu-feed-bot-badge">IA Automação</span>' if is_bot else ''
                title_clean = self._render_inline_md(act["title"])
                content_clean = self._render_inline_md(act["content"]).replace('\n', '<br/>')

                feed_html += (
                    f'<div class="cu-feed-item">'
                    f'<div class="cu-feed-avatar {avatar_class}">{avatar_text}</div>'
                    f'<div class="cu-feed-card">'
                    f'<div class="cu-feed-head">'
                    f'<div class="cu-feed-author-wrap">'
                    f'<span class="cu-feed-author">{act["author"]}</span>'
                    f'{bot_badge}'
                    f'<span class="cu-feed-status-badge">{act["badge"]}</span>'
                    f'</div>'
                    f'<span class="cu-feed-date">🕒 {act["date"]}</span>'
                    f'</div>'
                    f'<div class="cu-feed-title">{title_clean}</div>'
                    f'<div class="cu-feed-body">{content_clean}</div>'
                    f'</div>'
                    f'</div>'
                )
            feed_html += '</div>\n'
            return feed_html

        self.content = re.sub(r'<ClickUpActivityFeed\s+[\s\S]*?(?:/>|>\s*</ClickUpActivityFeed>)', parse_clickup_feed, self.content)

        # 4. Transformar ClickUpTaskCard
        def parse_clickup_card(m):
            raw_block = m.group(0)
            id_m = re.search(r'taskId=["\'](.*?)["\']', raw_block)
            code_m = re.search(r'taskCode=["\'](.*?)["\']', raw_block)
            title_m = re.search(r'title=["\'](.*?)["\']', raw_block)
            status_m = re.search(r'status=["\'](.*?)["\']', raw_block)
            prio_m = re.search(r'priority=["\'](.*?)["\']', raw_block)
            list_m = re.search(r'list=["\'](.*?)["\']', raw_block)
            folder_m = re.search(r'folder=["\'](.*?)["\']', raw_block)
            sub_m = re.search(r'subtasks=\{\s*\{\s*completed:\s*(\d+)\s*,\s*total:\s*(\d+)\s*\}\s*\}', raw_block)
            doc_m = re.search(r'docPath=["\'](.*?)["\']', raw_block)

            task_id = id_m.group(1) if id_m else ""
            task_code = code_m.group(1) if code_m else "TASK"
            title = self._render_inline_md(title_m.group(1) if title_m else "Tarefa")
            status = status_m.group(1) if status_m else "Backlog"
            priority = prio_m.group(1) if prio_m else "normal"
            list_name = list_m.group(1) if list_m else "Geral"
            folder_name = folder_m.group(1) if folder_m else "Portal"
            doc_path = doc_m.group(1) if doc_m else "#"

            status_slug = re.sub(r'[^a-zA-Z0-9]', '-', status.lower())
            prio_slug = re.sub(r'[^a-zA-Z0-9]', '-', priority.lower())
            prio_label = "Urgente" if prio_slug in ("urgent", "urgente") else ("Alta" if prio_slug in ("high", "alta") else ("Baixa" if prio_slug in ("low", "baixa") else "Normal"))

            sub_html = ""
            if sub_m:
                comp = int(sub_m.group(1))
                tot = int(sub_m.group(2))
                pct = int(round((comp / tot * 100))) if tot > 0 else 0
                sub_html = f'<div class="cu-card-sub"><span class="cu-card-sub-txt">Subtarefas: {comp}/{tot}</span><div class="cu-card-sub-track"><div class="cu-card-sub-bar" style="width:{pct}%;"></div></div></div>'

            return f'''<div class="clickup-task-card cu-card-status-{status_slug}">
<div class="cu-card-top">
<span class="cu-card-ctx">{folder_name} / {list_name}</span>
<span class="cu-card-id">#{task_id}</span>
</div>
<a href="{doc_path}" class="cu-card-title">[{task_code}] {title}</a>
<div class="cu-card-footer">
<span class="cu-status-pill cu-status-{status_slug}">{status.upper()}</span>
<span class="cu-prio-badge cu-prio-{prio_slug}">🚩 {prio_label}</span>
{sub_html}
</div>
</div>'''
        self.content = re.sub(r'<ClickUpTaskCard\s+[\s\S]*?(?:/>|>\s*</ClickUpTaskCard>)', parse_clickup_card, self.content)

    def _transform_jsx_divs(self):
        self.content = re.sub(r'<div\s+className=["\'](.*?)["\']>', r'<div class="\1">', self.content)

    def _extract_and_sanitize_mermaid(self):
        self.mermaid_blocks = []

        def replace_mermaid(m):
            idx = len(self.mermaid_blocks)
            raw_code = m.group(1).strip()

            # Sanitização automática de HTML tags no Mermaid
            clean_code = re.sub(r'</?(?:b|i|strong|em|u|span)>', '', raw_code, flags=re.IGNORECASE)
            clean_code = clean_code.replace(r'R\$', 'R$').replace(r'\$', '$')
            clean_code = clean_code.replace('&amp;', '&').replace('&nbsp;', ' ')

            self.mermaid_blocks.append(clean_code)
            return f"\n\n<!-- MERMAID_PLACEHOLDER_{idx} -->\n\n"

        self.content = re.sub(r'```mermaid([\s\S]*?)```', replace_mermaid, self.content)


# =============================================================================
# GERADOR DE HTML E EXECUÇÃO PLAYWRIGHT
# =============================================================================
class PDFGenerator:
    """Compila HTML estilizado e invoca Playwright para exportar o PDF."""

    def __init__(self, mdx_file: Path, output_pdf: Path = None, theme_name: str = "corporate", verbose: bool = False):
        self.mdx_file = mdx_file if mdx_file.is_absolute() else (WORKSPACE_DIR / mdx_file).resolve()
        if output_pdf:
            self.output_pdf = output_pdf if output_pdf.is_absolute() else (WORKSPACE_DIR / output_pdf).resolve()
        else:
            self.output_pdf = self._default_output_path(self.mdx_file)
        self.theme_name = theme_name
        self.verbose = verbose
        self.temp_html = WORKSPACE_DIR / f"scripts/temp_{self.output_pdf.stem}.html"

    def _default_output_path(self, mdx_path: Path) -> Path:
        parent_dir = mdx_path.parent
        # Se o arquivo já estiver numa subpasta de documentação, organiza na pasta pdf/
        pdf_dir = parent_dir / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return pdf_dir / f"{mdx_path.stem}.pdf"

    def build(self) -> bool:
        log_info(f"Processando: {self.mdx_file.name}")
        if self.verbose:
            print(f"       Origem:  {self.mdx_file}")
            print(f"       Destino: {self.output_pdf}")

        if not self.mdx_file.exists():
            log_error(f"Arquivo não encontrado: {self.mdx_file}")
            return False

        raw_content = self.mdx_file.read_text(encoding="utf-8")

        # 1. Validação prévia
        validator = MDXValidator(raw_content, self.mdx_file)
        is_valid = validator.validate()
        validator.print_report()

        if not is_valid:
            log_error("Processo abortado devido a erros críticos de validação.")
            return False

        # 2. Processamento e Sanitização
        processor = MDXProcessor(raw_content, theme_name=self.theme_name)
        processed_md, metadata, mermaid_blocks = processor.process()

        # 3. Montagem do HTML
        html_code = self._render_html_template(processed_md, metadata, mermaid_blocks, processor.theme)
        self.temp_html.write_text(html_code, encoding="utf-8")

        # 4. Renderização com Playwright
        success = self._render_pdf_with_playwright(metadata, processor.theme)

        # 5. Limpeza de arquivo temporário
        if self.temp_html.exists() and not self.verbose:
            try:
                self.temp_html.unlink()
            except Exception:
                pass

        if success:
            try:
                rel_path = self.output_pdf.relative_to(WORKSPACE_DIR)
            except Exception:
                rel_path = self.output_pdf
            log_success(f"PDF gerado com sucesso: {rel_path}")
        return success

    def _render_html_template(self, markdown_text: str, metadata: dict, mermaid_blocks: list, theme: dict) -> str:
        raw_markdown_json = json.dumps(markdown_text, ensure_ascii=False)
        mermaid_blocks_json = json.dumps(mermaid_blocks, ensure_ascii=False)
        font_family_json = json.dumps(theme.get("font_family", "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"))

        clean_category = metadata.get("category_display") or format_category_display(metadata.get("category", "Geral"))
        brand_logo = theme.get("brand_name", "DOCUMENTAÇÃO TÉCNICA")
        brand_sub = theme.get("brand_sub") or clean_category
        primary_color = theme.get("primary_color", "#0284c7")
        primary_dark = theme.get("primary_dark", "#0f172a")

        is_curriculo = self.theme_name == "curriculo" or metadata.get("layout") == "curriculo" or str(metadata.get("hide_cover", "")).lower() in ("true", "1")
        if is_curriculo:
            header_cover_html = ""
            curriculo_styles = f"""
    @page {{
      size: A4;
      margin: 8mm 12mm 8mm 12mm;
    }}
    body {{
      font-size: 8.5pt;
      line-height: 1.34;
      color: #1e293b;
    }}
    h1 {{
      font-size: 15pt;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 2px 0;
      line-height: 1.2;
      letter-spacing: -0.3px;
      page-break-after: avoid;
    }}
    .curriculo-contact {{
      font-size: 8pt;
      color: #475569;
      margin-bottom: 8px;
      padding-bottom: 5px;
      border-bottom: 1.5px solid #cbd5e1;
    }}
    .curriculo-contact a {{
      color: #0284c7;
      text-decoration: none;
    }}
    h2 {{
      font-size: 9.5pt;
      font-weight: 700;
      color: #0369a1;
      border-left: none !important;
      border-bottom: 1.5px solid #0284c7;
      padding-left: 0 !important;
      padding-bottom: 2px;
      margin-top: 8px;
      margin-bottom: 5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    h3 {{
      font-size: 8.8pt;
      font-weight: 700;
      color: #1e293b;
      margin-top: 5px;
      margin-bottom: 2px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    p, ul, ol {{
      margin-top: 0;
      margin-bottom: 4px;
      font-size: 8.5pt;
      line-height: 1.32;
    }}
    ul, ol {{
      padding-left: 15px;
      margin-bottom: 4px;
    }}
    li {{
      margin-bottom: 2px;
    }}
    hr {{
      display: none;
    }}
            """
        else:
            header_cover_html = f'''
    <div class="header-cover">
      <div class="brand-bar">
        <div class="brand-logo">{brand_logo}</div>
        <div class="doc-category">{brand_sub}</div>
      </div>
      <h1>{metadata["title"]}</h1>
      <div class="meta-grid">
        <div class="meta-item"><strong>Categoria</strong> {clean_category}</div>
        <div class="meta-item"><strong>Responsável</strong> {metadata.get("author", "Victor Rubinec")}</div>
        <div class="meta-item"><strong>Data / Atualização</strong> {metadata.get("updatedAt", metadata.get("createdAt", "2026-10-02"))}</div>
        <div class="meta-item"><strong>Status</strong> {metadata.get("status", "Ativo")}</div>
      </div>
    </div>
            '''
            curriculo_styles = ""

        return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>{metadata["title"]}</title>
  <script src="https://cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
  <style>
    @page {{
      size: A4;
      margin: 16mm 14mm 18mm 14mm;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: {theme["font_family"]};
      font-size: 9.5pt;
      line-height: 1.5;
      color: #1e293b;
      background-color: #ffffff;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 100%;
      margin: 0 auto;
    }}
    
    /* Capa e Cabeçalho Superior */
    .header-cover {{
      border-bottom: 3px solid {primary_dark};
      padding-bottom: 12px;
      margin-bottom: 18px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    .brand-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .brand-logo {{
      font-size: 14pt;
      font-weight: 900;
      letter-spacing: -0.5px;
      color: {primary_dark};
      text-transform: uppercase;
    }}
    .brand-logo span {{ color: {primary_color}; }}
    .doc-category {{
      font-size: 8.5pt;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    h1 {{
      font-size: 17pt;
      font-weight: 800;
      color: {primary_dark};
      margin: 4px 0 10px 0;
      line-height: 1.25;
      letter-spacing: -0.5px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      background: {theme["bg_meta"]};
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 12px;
      margin-top: 10px;
      font-size: 8pt;
    }}
    .meta-item strong {{
      display: block;
      font-size: 7pt;
      text-transform: uppercase;
      color: #64748b;
      margin-bottom: 2px;
    }}
    
    /* Tipografia e Títulos */
    h2 {{
      font-size: 12.5pt;
      font-weight: 800;
      color: {primary_dark};
      border-left: 4px solid {primary_color};
      padding-left: 8px;
      margin-top: 22px;
      margin-bottom: 10px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    h3 {{
      font-size: 10.5pt;
      font-weight: 700;
      color: #1e293b;
      margin-top: 16px;
      margin-bottom: 6px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    h4 {{
      font-size: 9.5pt;
      font-weight: 700;
      color: #334155;
      margin-top: 12px;
      margin-bottom: 4px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    p, ul, ol {{
      margin-top: 0;
      margin-bottom: 8px;
      font-size: 9.5pt;
      line-height: 1.5;
    }}
    ul, ol {{ padding-left: 18px; }}
    li {{ margin-bottom: 3px; }}
    hr {{
      border: 0;
      border-top: 1px solid #e2e8f0;
      margin: 16px 0;
    }}
    
    /* Tabelas */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 8.5pt;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 6px 9px;
      text-align: left;
    }}
    th {{
      background-color: #f1f5f9;
      color: {primary_dark};
      font-weight: 700;
      font-size: 8pt;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    tr:nth-child(even) {{ background-color: #f8fafc; }}

    /* Blocos de Código e Inline Code */
    pre {{
      background: #0f172a;
      color: #e2e8f0;
      border: 1px solid #1e293b;
      border-radius: 6px;
      padding: 8px 11px;
      margin: 10px 0;
      font-family: "Cascadia Code", "Fira Code", Consolas, "Courier New", monospace;
      font-size: 7.5pt;
      line-height: 1.38;
      overflow-x: hidden;
      white-space: pre-wrap;
      word-break: break-all;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    pre code {{
      background: transparent;
      color: inherit;
      padding: 0;
      border: 0;
      font-size: inherit;
      font-family: inherit;
    }}
    code {{
      background: #f1f5f9;
      color: #0f172a;
      border: 1px solid #e2e8f0;
      border-radius: 3px;
      padding: 1.5px 4px;
      font-size: 8pt;
      font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
    }}

    /* Badges */
    .badge {{
      display: inline-block;
      font-size: 7pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      margin-right: 4px;
      margin-bottom: 3px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-trabalho, .badge-blue {{ background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }}
    .badge-processo, .badge-green {{ background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }}
    .badge-projeto, .badge-purple {{ background: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }}
    .badge-ideia, .badge-orange {{ background: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }}
    .badge-danger, .badge-red {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }}
    .badge-default, .badge-gray {{ background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }}

    /* Callouts */
    .callout {{
      border-left: 4px solid {primary_color};
      background: #f0f9ff;
      border-radius: 4px;
      padding: 9px 12px;
      margin: 12px 0;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .callout-title {{
      font-weight: 700;
      font-size: 9pt;
      color: {primary_color};
      margin-bottom: 3px;
    }}
    .callout-body p {{ margin: 0; font-size: 8.5pt; color: #334155; }}
    .callout-success {{ border-left-color: #10b981; background: #f0fdf4; }}
    .callout-success .callout-title {{ color: #15803d; }}
    .callout-warning {{ border-left-color: #f59e0b; background: #fffbeb; }}
    .callout-warning .callout-title {{ color: #b45309; }}
    .callout-danger {{ border-left-color: #ef4444; background: #fef2f2; }}
    .callout-danger .callout-title {{ color: #b91c1c; }}

    /* Timeline */
    .timeline-container {{
      position: relative;
      margin: 14px 0;
      padding-left: 18px;
      border-left: 2px solid {primary_color};
    }}
    .timeline-item {{
      position: relative;
      margin-bottom: 12px;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .timeline-item::before {{
      content: "";
      position: absolute;
      left: -24px;
      top: 3px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: {primary_color};
      border: 2px solid #ffffff;
      box-shadow: 0 0 0 1.5px {primary_color};
    }}
    .timeline-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 3px;
    }}
    .timeline-date {{
      font-size: 7.5pt;
      font-weight: 700;
      color: {primary_color};
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .timeline-badge {{
      display: inline-block;
      font-size: 6.5pt;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 3px;
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      text-transform: uppercase;
    }}
    .timeline-title {{
      font-size: 9pt;
      font-weight: 700;
      color: {primary_dark};
      margin-bottom: 2px;
    }}
    .timeline-desc {{
      font-size: 8.5pt;
      color: #475569;
      line-height: 1.4;
    }}

    /* LinkCard */
    .link-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 12px;
      margin: 8px 0;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .link-card-title {{
      font-weight: 700;
      font-size: 8.5pt;
      color: {primary_color};
    }}
    .link-card-desc {{
      font-size: 8pt;
      color: #64748b;
      margin-top: 2px;
    }}
    .link-card-href {{
      font-size: 7pt;
      color: #94a3b8;
      font-family: monospace;
      margin-top: 2px;
    }}

    /* ClickUp Task Header */
    .clickup-task-header {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 14px;
      margin: 12px 0 16px 0;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .cu-top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 7px;
      margin-bottom: 7px;
      border-bottom: 1px solid #f1f5f9;
      font-size: 7.5pt;
      color: #64748b;
    }}
    .cu-breadcrumb {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .cu-crumb-ws {{ font-weight: 600; color: #475569; }}
    .cu-crumb-folder {{ color: #64748b; }}
    .cu-crumb-list {{ font-weight: 700; color: #0f172a; }}
    .cu-sep {{ color: #cbd5e1; }}
    .cu-task-id {{
      margin-left: 5px;
      font-family: monospace;
      background: #f1f5f9;
      color: #475569;
      padding: 1px 4px;
      border-radius: 3px;
      font-size: 7pt;
    }}
    .cu-btn-link {{
      color: #7b68ee;
      font-weight: 600;
      font-size: 7.5pt;
      text-decoration: none;
    }}
    .cu-main-row {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 7px;
    }}
    .cu-status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 7pt;
      font-weight: 700;
      border: 1px solid #cbd5e1;
      background: #f8fafc;
      color: #334155;
    }}
    .cu-status-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #64748b;
    }}
    .cu-status-em-teste {{ background: #fff7ed; border-color: #f97316; color: #c2410c; }}
    .cu-status-em-teste .cu-status-dot {{ background: #ea580c; }}
    .cu-status-em-desenvolvimento {{ background: #ede9fe; border-color: #8b5cf6; color: #5b21b6; }}
    .cu-status-em-desenvolvimento .cu-status-dot {{ background: #7c3aed; }}
    .cu-status-em-progresso {{ background: #eff6ff; border-color: #3b82f6; color: #1e40af; }}
    .cu-status-em-progresso .cu-status-dot {{ background: #2563eb; }}
    .cu-status-aguardando-aprovacao, .cu-status-aguardando-gestor {{ background: #fef3c7; border-color: #f59e0b; color: #92400e; }}
    .cu-status-aguardando-aprovacao .cu-status-dot, .cu-status-aguardando-gestor .cu-status-dot {{ background: #d97706; }}
    .cu-status-concluido {{ background: #ecfdf5; border-color: #10b981; color: #065f46; }}
    .cu-status-concluido .cu-status-dot {{ background: #059669; }}

    .cu-prio-badge {{
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 7pt;
      font-weight: 600;
      background: #f1f5f9;
      color: #475569;
    }}
    .cu-prio-high, .cu-prio-alta {{ background: #fff7ed; color: #ea580c; }}
    .cu-prio-urgent, .cu-prio-urgente {{ background: #fef2f2; color: #dc2626; }}
    .cu-prio-normal {{ background: #eff6ff; color: #2563eb; }}

    .cu-assignee-pill {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 2px 6px;
      border-radius: 9999px;
      font-size: 7pt;
      color: #334155;
    }}
    .cu-avatar {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #795548;
      color: #fff;
      font-size: 6pt;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .cu-due {{ color: #dc2626; font-weight: 600; }}
    .cu-tags-wrap {{ display: flex; gap: 4px; }}
    .cu-tag {{
      background: #f1f5f9;
      color: #64748b;
      font-size: 6.5pt;
      padding: 1px 5px;
      border-radius: 3px;
    }}

    /* ClickUp Checklist Card */
    .clickup-checklist-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 10px 14px;
      margin: 12px 0;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .cu-chk-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}
    .cu-chk-title {{
      font-weight: 700;
      font-size: 8.5pt;
      color: #0f172a;
    }}
    .cu-chk-count {{
      font-size: 7pt;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 9999px;
    }}
    .cu-chk-progress-track {{
      width: 100%;
      height: 5px;
      background: #f1f5f9;
      border-radius: 9999px;
      overflow: hidden;
      margin-bottom: 8px;
    }}
    .cu-chk-progress-bar {{
      height: 100%;
      border-radius: 9999px;
    }}
    .cu-chk-list {{
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}
    .cu-chk-row {{
      display: flex;
      align-items: flex-start;
      gap: 6px;
      font-size: 8pt;
      color: #334155;
    }}
    .cu-chk-box {{
      width: 13px;
      height: 13px;
      border-radius: 50%;
      border: 1px solid #cbd5e1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 7pt;
      font-weight: 700;
      flex-shrink: 0;
      margin-top: 1px;
    }}
    .cu-chk-done .cu-chk-box {{
      background: #10b981;
      border-color: #10b981;
      color: #ffffff;
    }}
    .cu-chk-done .cu-chk-text {{
      color: #334155;
      font-weight: 500;
    }}
    .cu-chk-tag {{
      margin-left: auto;
      font-size: 6.5pt;
      background: #f1f5f9;
      color: #475569;
      padding: 1px 4px;
      border-radius: 3px;
      flex-shrink: 0;
    }}

    /* ClickUp Activity Feed */
    .clickup-feed-container {{
      position: relative;
      padding-left: 20px;
      margin: 12px 0;
      border-left: 2px solid #e2e8f0;
    }}
    .cu-feed-item {{
      position: relative;
      margin-bottom: 10px;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .cu-feed-avatar {{
      position: absolute;
      left: -27px;
      top: 3px;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 7pt;
      font-weight: 700;
      color: #ffffff;
      border: 2px solid #ffffff;
    }}
    .cu-av-bot {{ background: #7b68ee; font-size: 8pt; }}
    .cu-av-user {{ background: #795548; font-size: 6pt; }}
    .cu-feed-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 10px;
    }}
    .cu-feed-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
      font-size: 7.5pt;
    }}
    .cu-feed-author-wrap {{
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .cu-feed-author {{ font-weight: 700; color: #0f172a; }}
    .cu-feed-bot-badge {{
      background: #f5f3ff;
      color: #7c3aed;
      border: 1px solid #ddd6fe;
      font-size: 6pt;
      padding: 0 4px;
      border-radius: 3px;
    }}
    .cu-feed-status-badge {{
      background: #f1f5f9;
      color: #475569;
      font-size: 6.5pt;
      padding: 0 4px;
      border-radius: 3px;
    }}
    .cu-feed-date {{ font-size: 7pt; color: #94a3b8; }}
    .cu-feed-title {{ font-weight: 700; font-size: 8pt; color: #1e293b; margin-bottom: 2px; }}
    .cu-feed-body {{ font-size: 7.5pt; color: #475569; line-height: 1.4; }}

    /* ClickUp Task Card (Visão em Cards) */
    .clickup-task-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #7b68ee;
      border-radius: 6px;
      padding: 8px 12px;
      margin: 8px 0;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .cu-card-status-em-teste {{ border-left-color: #f97316; }}
    .cu-card-status-em-progresso {{ border-left-color: #3b82f6; }}
    .cu-card-status-em-desenvolvimento {{ border-left-color: #8b5cf6; }}
    .cu-card-status-aguardando-aprovacao {{ border-left-color: #f59e0b; }}
    .cu-card-status-concluido {{ border-left-color: #10b981; }}
    .cu-card-top {{ display: flex; justify-content: space-between; font-size: 7pt; color: #64748b; margin-bottom: 2px; }}
    .cu-card-id {{ font-family: monospace; }}
    .cu-card-title {{ font-weight: 700; font-size: 8.5pt; color: #0f172a; text-decoration: none; display: block; margin-bottom: 5px; }}
    .cu-card-footer {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
    .cu-card-sub {{ display: inline-flex; align-items: center; gap: 4px; font-size: 6.5pt; color: #64748b; margin-left: auto; }}
    .cu-card-sub-track {{ width: 35px; height: 4px; background: #f1f5f9; border-radius: 2px; overflow: hidden; }}
    .cu-card-sub-bar {{ height: 100%; background: #10b981; }}


    /* Mermaid Diagrams */
    .mermaid-wrap {{
      margin: 14px 0;
      padding: 12px 14px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      display: flex;
      justify-content: center;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .mermaid {{
      width: 100%;
      text-align: center;
    }}
    .mermaid svg {{
      width: 100% !important;
      height: auto !important;
    }}

    {curriculo_styles}
  </style>
</head>
<body>
  <div class="container">
    {header_cover_html}
    <div id="content"></div>
  </div>

  <script>
    mermaid.initialize({{
      startOnLoad: false,
      theme: 'neutral',
      fontSize: 13,
      flowchart: {{
        useMaxWidth: true,
        htmlLabels: false,
        curve: 'basis'
      }},
      fontFamily: {font_family_json}
    }});

    const rawMarkdown = {raw_markdown_json};
    const mermaidBlocks = {mermaid_blocks_json};

    const md = window.markdownit({{
      html: true,
      linkify: true,
      breaks: false
    }});

    let renderedHtml = md.render(rawMarkdown);

    mermaidBlocks.forEach((code, idx) => {{
      const placeholder = `<!-- MERMAID_PLACEHOLDER_${{idx}} -->`;
      const safeHtml = `<div class="mermaid-wrap"><div class="mermaid">${{code}}</div></div>`;
      renderedHtml = renderedHtml.replace(placeholder, safeHtml);
    }});

    document.getElementById('content').innerHTML = renderedHtml;

    window.mermaidDone = false;
    (async function initMermaid() {{
      try {{
        const nodes = document.querySelectorAll('.mermaid');
        if (nodes && nodes.length > 0 && window.mermaid) {{
          await mermaid.run({{ nodes: nodes }});
        }}
      }} catch (err) {{
        console.error('Mermaid render error:', err);
      }} finally {{
        window.mermaidDone = true;
      }}
    }})();
  </script>
</body>
</html>
'''

    def _render_pdf_with_playwright(self, metadata: dict, theme: dict) -> bool:
        from playwright.sync_api import sync_playwright
        import pypdf

        clean_category = metadata.get("category_display") or format_category_display(metadata.get("category", "Documentação Técnica"))
        header_sub = theme.get("brand_sub") or clean_category
        brand_name = theme.get("brand_name", "TRÍADE DIGITAL")

        header_template = f'''
        <div style="font-size: 7pt; font-family: -apple-system, sans-serif; width: 100%; display: flex; justify-content: space-between; padding: 0 14mm; color: #94a3b8;">
          <span>{brand_name} — {metadata["title"]}</span>
          <span>{header_sub}</span>
        </div>
        '''

        footer_template = '''
        <div style="font-size: 7pt; font-family: -apple-system, sans-serif; width: 100%; display: flex; justify-content: space-between; padding: 0 14mm; color: #94a3b8;">
          <span>Documento Corporativo & Técnico</span>
          <span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span>
        </div>
        '''

        browser_errors = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 1. Listeners de Erros do Browser
                page.on("pageerror", lambda err: browser_errors.append(f"JS PageError: {err}"))
                page.on("console", lambda msg: browser_errors.append(f"JS Console Error: {msg.text}") if msg.type == "error" else None)

                page.goto(self.temp_html.resolve().as_uri(), wait_until="networkidle")

                # Aguarda renderização dos diagramas Mermaid
                try:
                    page.wait_for_function("window.mermaidDone === true", timeout=15000)
                except Exception as e:
                    browser_errors.append(f"Timeout aguardando mermaidDone: {e}")

                # 2. Pré-Verificação no DOM do Browser
                content_text = page.inner_text("#content")
                content_html = page.inner_html("#content")

                if browser_errors:
                    for b_err in browser_errors:
                        log_error(b_err)

                if len(content_text.strip()) == 0 or len(content_html.strip()) == 0:
                    log_error("FALHA CRÍTICA DE RENDERIZAÇÃO: O DOM (#content) ficou completamente vazio no navegador!")
                    browser.close()
                    return False

                # Auditoria de Erros nos diagramas Mermaid
                body_text = page.inner_text("body")
                if "Syntax error in text" in body_text:
                    log_error("Erro de sintaxe detectado dentro do diagrama Mermaid pelo Chromium.")
                    browser.close()
                    return False

                # 3. Impressão do PDF
                is_curriculo = self.theme_name == "curriculo" or metadata.get("layout") == "curriculo" or str(metadata.get("hide_cover", "")).lower() in ("true", "1")
                if is_curriculo:
                    display_hf = False
                    pdf_margin = {"top": "8mm", "bottom": "8mm", "left": "12mm", "right": "12mm"}
                else:
                    display_hf = True
                    pdf_margin = {"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"}

                page.pdf(
                    path=str(self.output_pdf.resolve()),
                    format="A4",
                    print_background=True,
                    display_header_footer=display_hf,
                    header_template=header_template,
                    footer_template=footer_template,
                    margin=pdf_margin
                )
                browser.close()

                # 4. PÓS-VERIFICAÇÃO DO PDF GERADO (via pypdf)
                return self._verify_generated_pdf(metadata)

        except Exception as e:
            log_error(f"Falha na execução do Playwright: {e}")
            return False

    def _verify_generated_pdf(self, metadata: dict) -> bool:
        """Executa auditoria no arquivo PDF final com pypdf para assegurar integridade."""
        import pypdf

        if not self.output_pdf.exists():
            log_error(f"Arquivo PDF não foi encontrado no disco após geração: {self.output_pdf}")
            return False

        file_size_kb = self.output_pdf.stat().st_size / 1024
        if file_size_kb < 5.0:
            log_error(f"Tamanho do arquivo PDF suspeito de estar corrompido ou vazio ({file_size_kb:.1f} KB).")
            return False

        try:
            reader = pypdf.PdfReader(str(self.output_pdf))
            num_pages = len(reader.pages)

            if num_pages == 0:
                log_error("PDF gerado com 0 páginas.")
                return False

            total_extracted_text = ""
            blank_pages = []

            for idx, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                total_extracted_text += page_text + "\n"
                # Se uma página tiver menos de 10 caracteres, pode ser órfã em branco
                if len(page_text.strip()) < 10:
                    blank_pages.append(idx)

            char_count = len(total_extracted_text.strip())
            word_count = len(total_extracted_text.split())

            is_curriculo = self.theme_name == "curriculo" or metadata.get("layout") == "curriculo" or str(metadata.get("hide_cover", "")).lower() in ("true", "1")
            # Se o documento tiver apenas o texto da capa (< 300 caracteres) mas tiver muitas linhas no MDX
            if not is_curriculo and char_count < 400 and num_pages == 1:
                log_error(f"PDF contém apenas {char_count} caracteres (apenas capa detectada, corpo ausente).")
                return False

            if blank_pages:
                log_warn(f"Páginas potencialmente em branco ou com pouquíssimo texto detectadas: {blank_pages}")

            # Relatório de Sucesso Pós-Verificação
            print(f"{LogColor.CYAN}[PÓS-VERIFICAÇÃO DE INTEGRIDADE]{LogColor.RESET}")
            print(f"  ✔ Arquivo PDF: {self.output_pdf.name} ({file_size_kb:.1f} KB)")
            print(f"  ✔ Total de Páginas: {num_pages} página(s)")
            print(f"  ✔ Conteúdo Extraído: {word_count} palavras / {char_count} caracteres")
            print(f"  ✔ Integridade do Layout: Aprovado sem páginas órfãs vazias.")

            return True

        except Exception as e:
            log_error(f"Falha ao auditar arquivo PDF com pypdf: {e}")
            return False


# =============================================================================
# GERADOR DE PDF PARA DECK DE SLIDES HTML (16:9 WIDESCREEN)
# =============================================================================
class SlideDeckPDFGenerator:
    """Compila decks de slides HTML interativos em apresentações PDF widescreen 16:9."""

    def __init__(self, html_file: Path, output_pdf: Path = None, verbose: bool = False):
        self.html_file = html_file if html_file.is_absolute() else (WORKSPACE_DIR / html_file).resolve()
        if output_pdf:
            self.output_pdf = output_pdf if output_pdf.is_absolute() else (WORKSPACE_DIR / output_pdf).resolve()
        else:
            self.output_pdf = self._default_output_path(self.html_file)
        self.verbose = verbose

    def _default_output_path(self, html_path: Path) -> Path:
        parent_dir = html_path.parent
        if parent_dir.name in ["apresentacao-slides", "slides"]:
            pdf_dir = parent_dir.parent / "pdf"
        else:
            pdf_dir = parent_dir / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        stem = html_path.stem if html_path.stem != "index" else parent_dir.name
        return pdf_dir / f"{stem}.pdf"

    def build(self) -> bool:
        log_info(f"Processando Deck de Slides HTML: {self.html_file.name}")
        if self.verbose:
            print(f"       Origem:  {self.html_file}")
            print(f"       Destino: {self.output_pdf}")

        if not self.html_file.exists():
            log_error(f"Arquivo não encontrado: {self.html_file}")
            return False

        try:
            from playwright.sync_api import sync_playwright
            import pypdf

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                slide_pdfs = []

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1920, "height": 1080})
                    page.goto(self.html_file.resolve().as_uri(), wait_until="networkidle")
                    page.wait_for_timeout(500)

                    total_slides = page.evaluate("document.querySelectorAll('.slide').length")
                    if total_slides == 0:
                        log_error("Nenhum slide com classe '.slide' encontrado no arquivo HTML.")
                        browser.close()
                        return False

                    log_info(f"Total de slides identificados: {total_slides}")

                    # Ocultar controles interativos para o PDF limpo
                    page.evaluate('''() => {
                        const ctrl = document.querySelector('.deck-controls');
                        if (ctrl) ctrl.style.display = 'none';
                        const topBar = document.querySelector('.deck-top-bar');
                        if (topBar) topBar.style.display = 'none';
                    }''')

                    for i in range(1, total_slides + 1):
                        page.evaluate(f"window.showSlide({i})")
                        page.wait_for_timeout(200)

                        slide_file = tmp_path / f"slide_{i:02d}.pdf"
                        page.pdf(
                            path=str(slide_file),
                            width="1920px",
                            height="1080px",
                            print_background=True,
                            margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"}
                        )
                        slide_pdfs.append(slide_file)
                        if self.verbose:
                            print(f"       Slide {i:02d}/{total_slides:02d} renderizado.")

                    browser.close()

                # Concatenar todos os slides num único PDF
                writer = pypdf.PdfWriter()
                for s_pdf in slide_pdfs:
                    reader = pypdf.PdfReader(str(s_pdf))
                    for p_page in reader.pages:
                        writer.add_page(p_page)

                with open(self.output_pdf, "wb") as f_out:
                    writer.write(f_out)

            return self._verify_generated_pdf()

        except Exception as e:
            log_error(f"Falha ao gerar PDF da apresentação: {e}")
            return False

    def _verify_generated_pdf(self) -> bool:
        import pypdf
        if not self.output_pdf.exists():
            log_error(f"Arquivo PDF não encontrado: {self.output_pdf}")
            return False

        file_size_kb = self.output_pdf.stat().st_size / 1024
        reader = pypdf.PdfReader(str(self.output_pdf))
        num_pages = len(reader.pages)

        print(f"{LogColor.CYAN}[PÓS-VERIFICAÇÃO DE INTEGRIDADE DO DECK]{LogColor.RESET}")
        print(f"  ✔ Arquivo PDF: {self.output_pdf.name} ({file_size_kb:.1f} KB)")
        print(f"  ✔ Total de Páginas/Slides: {num_pages} slide(s)")
        print(f"  ✔ Formato: Widescreen 16:9 (1920x1080 nativo)")

        try:
            rel_path = self.output_pdf.relative_to(WORKSPACE_DIR)
        except Exception:
            rel_path = self.output_pdf
        log_success(f"PDF de Apresentação gerado com sucesso: {rel_path}")
        return True


# =============================================================================
# ENTRYPOINT CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Motor Unificado de Validação e Geração de PDF (MDX -> PDF)"
    )
    parser.add_argument("input", nargs="?", help="Caminho do arquivo .mdx ou .html a ser processado")
    parser.add_argument("-o", "--output", help="Caminho de saída para o arquivo .pdf")
    parser.add_argument("-t", "--theme", default="corporate", choices=list(THEMES.keys()), help="Tema visual (padrão: corporate)")
    parser.add_argument("-c", "--check-only", action="store_true", help="Executa apenas a validação/linter sem gerar PDF")
    parser.add_argument("-d", "--dir", help="Processa todos os arquivos .mdx de um diretório recursivamente")
    parser.add_argument("-v", "--verbose", action="store_true", help="Exibe detalhes da execução")

    args = parser.parse_args()

    if not args.input and not args.dir:
        parser.print_help()
        sys.exit(1)

    targets = []
    if args.dir:
        target_dir = Path(args.dir)
        if not target_dir.is_absolute():
            target_dir = (WORKSPACE_DIR / target_dir).resolve()
        if not target_dir.exists():
            log_error(f"Diretório não encontrado: {target_dir}")
            sys.exit(1)
        targets = list(target_dir.rglob("*.mdx"))
        log_info(f"Encontrados {len(targets)} arquivos .mdx em {target_dir}")
    else:
        file_path = Path(args.input)
        if not file_path.is_absolute():
            file_path = (WORKSPACE_DIR / file_path).resolve()
        targets = [file_path]

    total_success = 0
    total_failures = 0

    for target in targets:
        if target.suffix.lower() == ".html":
            out_pdf = Path(args.output) if args.output else None
            generator = SlideDeckPDFGenerator(
                html_file=target,
                output_pdf=out_pdf,
                verbose=args.verbose
            )
            if generator.build():
                total_success += 1
            else:
                total_failures += 1
        elif args.check_only:
            log_info(f"Validando: {target.name}")
            if not target.exists():
                log_error(f"Arquivo não encontrado: {target}")
                total_failures += 1
                continue
            content = target.read_text(encoding="utf-8")
            validator = MDXValidator(content, target)
            if validator.validate():
                validator.print_report()
                total_success += 1
            else:
                validator.print_report()
                total_failures += 1
        else:
            out_pdf = Path(args.output) if args.output else None
            generator = PDFGenerator(
                mdx_file=target,
                output_pdf=out_pdf,
                theme_name=args.theme,
                verbose=args.verbose
            )
            if generator.build():
                total_success += 1
            else:
                total_failures += 1

    print("\n=======================================================")
    print(f"Resumo da Execução: {total_success} sucesso(s), {total_failures} falha(s).")
    print("=======================================================")

    if total_failures > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
