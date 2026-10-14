"""Script orquestrador para análise de CSS e Design System de sites.

Executa o designsys url, roda a auditoria e gera/atualiza automaticamente
o arquivo de relatório .mdx correspondente em trabalho/sites/relatorios/<slug>/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Diretório raiz do projeto de anotações
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
RELATORIOS_DIR = WORKSPACE_ROOT / "trabalho" / "sites" / "relatorios"


def slugify(text: str) -> str:
    """Gera um slug limpo para nomes de diretórios e arquivos."""
    text = text.lower()
    text = re.sub(r"^https?://", "", text)
    text = re.sub(r"^www\.", "", text)
    text = text.split("/")[0]  # foca no domínio
    text = re.sub(r"[^\w\s-]", "-", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def run_command(cmd: list[str]) -> tuple[int, str]:
    """Executa um comando garantindo UTF-8 no Windows."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(WORKSPACE_ROOT),
    )
    output, _ = process.communicate()
    return process.returncode, output


def extrair_design_system(
    url: str,
    output_dir: Path,
    pages: int = 3,
    login: bool = False,
    user: str | None = None,
    password: str | None = None,
    headed: bool = False,
    no_dark: bool = False,
    no_viewports: bool = False,
) -> bool:
    """Invoca o designsys para extrair o site."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable,
        "-X", "utf8",
        "-m", "designsys",
        "url",
        url,
        "--out", str(output_dir),
        "--pages", str(pages),
    ]
    
    if login:
        cmd.append("--login")
    if user:
        cmd.extend(["--user", user])
    if password:
        cmd.extend(["--pass", password])
    if headed:
        cmd.append("--headed")
    if no_dark:
        cmd.append("--no-dark")
    if no_viewports:
        cmd.append("--no-viewports")
        
    print(f"[*] Iniciando extração do site: {url}")
    print(f"[*] Destino: {output_dir}")
    print(f"[*] Comando: {' '.join(cmd)}")
    
    code, out = run_command(cmd)
    print(out)
    
    if code != 0:
        print(f"[!] Erro durante a extração (código {code})")
        return False

    # Executa o audit na pasta
    audit_cmd = [
        sys.executable,
        "-X", "utf8",
        "-m", "designsys",
        "audit",
        str(output_dir),
    ]
    print("[*] Gerando diagnóstico de auditoria...")
    audit_code, audit_out = run_command(audit_cmd)
    print(audit_out)
    
    return True


def carregar_dados_extracao(output_dir: Path) -> dict:
    """Carrega dados dos arquivos gerados pelo designsys."""
    dados = {
        "tokens": {},
        "raw": {},
        "audit_md": "",
        "design_system_md": "",
        "components": [],
    }
    
    tokens_file = output_dir / "tokens.json"
    if tokens_file.exists():
        try:
            with open(tokens_file, "r", encoding="utf-8") as f:
                dados["tokens"] = json.load(f)
        except Exception as e:
            print(f"[!] Falha ao ler tokens.json: {e}")

    raw_file = output_dir / "raw.json"
    if raw_file.exists():
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                dados["raw"] = json.load(f)
        except Exception as e:
            print(f"[!] Falha ao ler raw.json: {e}")

    audit_file = output_dir / "audit.md"
    if audit_file.exists():
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                dados["audit_md"] = f.read()
        except Exception as e:
            print(f"[!] Falha ao ler audit.md: {e}")

    ds_md_file = output_dir / "DESIGN-SYSTEM.md"
    if ds_md_file.exists():
        try:
            with open(ds_md_file, "r", encoding="utf-8") as f:
                dados["design_system_md"] = f.read()
        except Exception as e:
            print(f"[!] Falha ao ler DESIGN-SYSTEM.md: {e}")

    comp_file = output_dir / "components.json"
    if comp_file.exists():
        try:
            with open(comp_file, "r", encoding="utf-8") as f:
                dados["components"] = json.load(f)
        except Exception as e:
            print(f"[!] Falha ao ler components.json: {e}")

    return dados


def gerar_conteudo_mdx(slug: str, url: str, dados: dict, pages: int) -> str:
    """Gera o documento MDX a partir dos dados extraídos."""
    today = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    tokens = dados.get("tokens", {})
    raw = dados.get("raw", {})
    audit_md = dados.get("audit_md", "")
    
    # Cores
    color_tokens = tokens.get("color", {})
    colors_table_rows = []
    for role, data in color_tokens.items():
        if isinstance(data, dict) and "$value" in data:
            val = data["$value"]
            desc = data.get("$description", "")
            ext = data.get("$extensions", {}).get("designsys", {})
            count = ext.get("usageCount", "-")
            dark_val = ext.get("dark", "-")
            colors_table_rows.append(
                f"| `{role}` | `{val}` | `{dark_val}` | {count} | {desc} |"
            )
    colors_table = "\n".join(colors_table_rows) if colors_table_rows else "| - | - | - | - | - |"

    # Tipografia
    font_family = tokens.get("fontFamily", {})
    font_names = []
    for k, v in font_family.items():
        if isinstance(v, dict) and "$value" in v:
            font_names.append(f"`{k}`: {v['$value']}")
    font_summary = ", ".join(font_names) if font_names else "Fontes do sistema / padrão"

    # Espaçamento
    spacing_tokens = tokens.get("spacing", {})
    spacing_keys = list(spacing_tokens.keys())[:8] if spacing_tokens else []
    spacing_summary = f"Tokens: {', '.join(spacing_keys)}" if spacing_keys else "Padrão detectado"

    # Diagnóstico / Auditoria resumo
    audit_summary = "Auditoria concluída com sucesso."
    if audit_md:
        lines = [l.strip() for l in audit_md.splitlines() if l.strip() and not l.startswith("#")]
        if lines:
            audit_summary = "\n".join(f"> {l}" for l in lines[:5])

    content = f"""---
title: "Relatório de Design System: {url}"
category: "trabalho/sites/relatorios"
tags: ["design-system", "css", "tokens", "a11y", "{slug}"]
createdAt: "{today}"
updatedAt: "{today}"
status: "concluido"
---

import {{ Timeline }} from '../../../../components/Timeline.jsx';
import {{ Badge }} from '../../../../components/Badge.jsx';
import {{ Callout }} from '../../../../components/Callout.jsx';
import {{ LinkCard }} from '../../../../components/LinkCard.jsx';

# Relatório de Design System: {url}

<Badge label="Sites" type="trabalho" />
<Badge label="Design System" type="projeto" />
<Badge label="Concluído" type="sucesso" />

## Visão Geral & Resumo

Relatório técnico e mapeamento do Design System extraído do endereço [`{url}`]({url}). A extração analisou a árvore DOM computada, variações de estado (`:hover`, `:focus`, `:active`), hierarquia tipográfica, contraste WCAG 2.2 AA e responsividade.

* **URL Alvo**: `{url}`
* **Data da Extração**: {now_str}
* **Páginas Mapeadas**: {pages}
* **Fontes Identificadas**: {font_summary}
* **Grade de Espaçamento**: {spacing_summary}

---

## 🎨 Paleta de Cores e Papéis Semânticos

As cores foram agrupadas e classificadas conforme o papel semântico inferido pelo algoritmo em espaço perceptual OKLab:

| Papel | Valor Claro | Par Escuro | Ocorrências | Descrição de Uso |
| :--- | :--- | :--- | :--- | :--- |
{colors_table}

---

## 📐 Tipografia e Escalas

* **Famílias Principais**: {font_summary}
* **Tokens de Escala**: Consulte os arquivos `extracao/variables.css` e `extracao/tokens.json` para conferir a escala completa com funções fluídas `clamp()`.

---

## ♿ Diagnóstico de Acessibilidade & Consistência (WCAG 2.2 AA)

{audit_summary}

Consulte o arquivo [`audit.md`](extracao/audit.md) para a lista completa de elementos ofensores e proporção de contraste par a par medidos no DOM real.

---

## 📦 Entregáveis da Extração

Todos os arquivos gerados estão salvos na subpasta [`extracao/`](extracao/):

1. **[`design-system.pdf`](extracao/design-system.pdf)**: Documento diagramado para impressão e apresentação institucional.
2. **[`DESIGN-SYSTEM.md`](extracao/DESIGN-SYSTEM.md)**: Regras diretas e concisas para agentes de IA (Cursor, Copilot, Antigravity) utilizarem no projeto.
3. **[`tokens.json`](extracao/tokens.json)**: Especificação padrão W3C DTCG (`$value` e `$type`).
4. **[`variables.css`](extracao/variables.css)**: CSS Custom Properties com suporte a tema escuro e responsividade fluida.
5. **[`tailwind.config.js`](extracao/tailwind.config.js)**: Bloco `theme.extend` pronto para colar em projetos Tailwind.
6. **[`style-guide.html`](extracao/style-guide.html)**: Guia visual interativo navegável no navegador.
7. **[`components.json`](extracao/components.json)**: Estilos computados detalhados de botões, formulários e cards.
8. **[`audit.md`](extracao/audit.md)**: Diagnóstico detalhado de conformidade e notas.

---

## 📜 Linha do Tempo

> **Nota para IAs**: Nunca crie um novo arquivo para atualizar este mesmo assunto em datas diferentes. Adicione novos blocos cronológicos abaixo nesta seção.

<Timeline items={[
  {{
    date: "{today}",
    title: "Extração Inicial do Design System",
    content: "Mapeamento completo realizado via designsys cobrindo {pages} páginas, tokens W3C, CSS vars e auditoria de acessibilidade.",
    status: "Concluído"
  }}
]} />

---

## 🔗 Assuntos Relacionados

- [`Guia Padrão de Criação de Sites`](../../guia-padrao-criacao-sites.mdx) — Metodologia mestre e diretrizes de desenvolvimento web.
"""
    return content


def atualizar_ou_criar_mdx(slug: str, url: str, dados: dict, pages: int, mdx_file: Path) -> None:
    """Cria o MDX ou atualiza a linha do tempo se já existir."""
    today = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    
    if not mdx_file.exists():
        content = gerar_conteudo_mdx(slug, url, dados, pages)
        mdx_file.write_text(content, encoding="utf-8")
        print(f"[+] Relatório MDX criado com sucesso: {mdx_file}")
        return

    print(f"[*] Relatório existente encontrado: {mdx_file}. Atualizando Linha do Tempo...")
    old_content = mdx_file.read_text(encoding="utf-8")
    
    old_content = re.sub(r'updatedAt:\s*".*?"', f'updatedAt: "{today}"', old_content)
    
    nova_entrada = f"""  {{
    date: "{today}",
    title: "Reanálise e Auditoria de CSS ({now_str})",
    content: "Nova extração realizada cobrindo {pages} páginas. Tokens e diagnósticos atualizados na pasta extracao/.",
    status: "Atualizado"
  }},"""
    
    if "<Timeline items={[" in old_content:
        subst = "<Timeline items={[\n" + nova_entrada
        old_content = old_content.replace("<Timeline items={[", subst)
    
    mdx_file.write_text(old_content, encoding="utf-8")
    print(f"[+] Relatório MDX atualizado com sucesso: {mdx_file}")


def main():
    parser = argparse.ArgumentParser(description="Orquestrador de Análise de CSS e Design System.")
    parser.add_argument("url", help="URL do site a analisar (ex: https://stripe.com)")
    parser.add_argument("--pages", "-p", type=int, default=3, help="Número de páginas internas a visitar (padrão: 3)")
    parser.add_argument("--login", action="store_true", help="Ativa fluxo de login para sites autenticados")
    parser.add_argument("--user", help="E-mail ou usuário para login")
    parser.add_argument("--pass", dest="password", help="Senha para login")
    parser.add_argument("--headed", action="store_true", help="Abre o navegador visível")
    parser.add_argument("--no-dark", action="store_true", help="Pula detecção de tema escuro")
    parser.add_argument("--no-viewports", action="store_true", help="Pula viewports mobile/tablet")
    parser.add_argument("--slug", help="Slug personalizado para o diretório de relatório")

    args = parser.parse_args()

    url = args.url
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    slug = args.slug or slugify(url)
    report_dir = RELATORIOS_DIR / slug
    extraction_dir = report_dir / "extracao"
    mdx_file = report_dir / f"relatorio-{slug}.mdx"

    print(f"============================================================")
    print(f" Análise de CSS & Design System: {url}")
    print(f" Pasta de Relatório: {report_dir}")
    print(f"============================================================")

    sucesso = extrair_design_system(
        url=url,
        output_dir=extraction_dir,
        pages=args.pages,
        login=args.login,
        user=args.user,
        password=args.password,
        headed=args.headed,
        no_dark=args.no_dark,
        no_viewports=args.no_viewports,
    )

    if not sucesso:
        print("[!] Falha na extração. O relatório MDX não pôde ser completamente gerado.")
        sys.exit(1)

    dados = carregar_dados_extracao(extraction_dir)
    atualizar_ou_criar_mdx(slug, url, dados, args.pages, mdx_file)
    print(f"\n[✓] Concluído! Relatório disponível em: {mdx_file}")


if __name__ == "__main__":
    main()
