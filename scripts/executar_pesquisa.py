#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/executar_pesquisa.py — Motor de Pesquisa Aprofundada & Geração de Dossiês Knowledge OS
Executa ordens de pesquisa criadas via Telegram ou linha de comando, investiga o repositório,
gera o documento oficial HTML via scripts/novo_documento.py e compila o PDF A4 corporativo.
"""

import sys
import re
import json
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

# Forçar encoding UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / "projetos" / "analisador-instagram-telegram" / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("executar_pesquisa")

from google import genai
from google.genai import types

PEDIDOS_DIR = REPO_ROOT / "projetos" / "pesquisas" / "pedidos"
CACHE_DIR = REPO_ROOT / "projetos" / "pesquisas" / "cache_dossies"
TELEGRAM_CONFIG_PATH = REPO_ROOT / "scripts" / "telegram_config.json"


def obter_telegram_token() -> str:
    import os
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token and TELEGRAM_CONFIG_PATH.exists():
        try:
            with open(TELEGRAM_CONFIG_PATH, "r", encoding="utf-8") as f:
                token = json.load(f).get("TELEGRAM_BOT_TOKEN")
        except Exception:
            pass
    return token or ""


def enviar_documento_telegram(chat_id: int, pdf_path: Path, caption: str = "") -> bool:
    """Envia o arquivo PDF gerado para o chat do Telegram do solicitante."""
    token = obter_telegram_token()
    if not token or not pdf_path.exists():
        return False

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with open(pdf_path, "rb") as f:
            files = {"document": (pdf_path.name, f, "application/pdf")}
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
            r = requests.post(url, data=data, files=files, timeout=60)
            if r.status_code == 200:
                logger.info(f"PDF enviado com sucesso para o Telegram (chat {chat_id})!")
                return True
            else:
                logger.warning(f"Falha ao enviar documento no Telegram: {r.text}")
    except Exception as e:
        logger.error(f"Erro no upload do PDF para o Telegram: {e}")
    return False


def obter_readme_github(repo_full_name: str) -> str:
    """Obtém o conteúdo do README oficial do repositório no GitHub."""
    import os
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3.raw", "User-Agent": "Antigravity-Deep-Researcher"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.text[:12000]
    except Exception as e:
        logger.warning(f"Erro ao buscar README de {repo_full_name}: {e}")
    return ""


def pesquisar_e_estruturar_relatorio(pedido: dict) -> dict:
    """
    Utiliza o Gemini para analisar profundamente os dados técnicos e gerar o dossiê executivo.
    Suporta tanto ferramenta unitária quanto toolkit/ecossistema completo com múltiplos repositórios.
    """
    import os
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=gemini_key)
    is_collection = pedido.get("is_collection", False)
    foco = pedido.get("foco_nome", "Geral")
    duvida = pedido.get("duvida_especifica", "Nenhuma dúvida específica.")

    if is_collection:
        # Investigação profunda de Toolkit / Coleção Multi-Repositório (1:N)
        collection_title = pedido.get("collection_title") or pedido.get("tech_name", "Toolkit de Tecnologias")
        collection_overview = pedido.get("collection_overview", "")
        items = pedido.get("items", [])
        
        logger.info(f"Iniciando pesquisa de ecossistema para o toolkit '{collection_title}' com {len(items)} ferramentas...")
        
        readmes_coletados = []
        for it in items[:6]:
            repo = it.get("repo_name", "")
            if repo:
                logger.info(f"Buscando README de {repo} para contextualização do toolkit...")
                txt = obter_readme_github(repo)
                if txt:
                    readmes_coletados.append(f"--- README de {it.get('tech_name')} ({repo}) ---\n{txt[:4000]}")

        readmes_bloco = "\n\n".join(readmes_coletados) if readmes_coletados else "READMEs públicos não disponíveis no momento."

        lista_ferramentas_str = "\n".join([
            f"- {it.get('tech_name')}: {it.get('summary')} | Repo: {it.get('repo_name', 'N/D')} ({it.get('stars_display', 'N/D')} stars) | Comando: {it.get('install_command', 'N/D')}"
            for it in items
        ])

        prompt = f"""
Você é um Arquiteto de Software Sênior e Especialista do Knowledge OS.
Sua missão é produzir uma pesquisa técnica aprofundada, altamente estruturada e profissional sobre um TOOLKIT / ECOSSISTEMA de ferramentas integradas:

--- DADOS DO TOOLKIT ---
Título do Toolkit / Coleção: {collection_title}
Visão Geral Preliminar: {collection_overview}
Foco Solicitado pelo Usuário: {foco}
Requisito / Pergunta Específica do Usuário: {duvida}

FERRAMENTAS COMPONENTES IDENTIFICADAS NO VÍDEO:
{lista_ferramentas_str}

DOCUMENTAÇÃO / READMES COLETADOS:
\"\"\"{readmes_bloco}\"\"\"
------------------------

Gere uma estrutura JSON com os seguintes campos em PORTUGUÊS DO BRASIL:
1. "subtitulo": Uma frase de impacto definindo a proposta unificada deste toolkit/stack.
2. "resumo_executivo": 2 parágrafos densos explicando a proposta de valor conjunta do toolkit, o problema que a combinação dessas ferramentas resolve e por que elas operam melhor juntas.
3. "arquitetura_e_funcionamento": Explicação detalhada da arquitetura do ecossistema, fluxo de dados de ponta a ponta (como as ferramentas se encadeiam da concepção à entrega) e interoperabilidade entre elas.
4. "resposta_requisito_usuario": Resposta técnica direta e aprofundada considerando o conjunto de ferramentas para o requisito: "{duvida}".
5. "analise_viabilidade": Análise de viabilidade do stack conjunto: complementaridades, sobreposições/redundâncias, facilidade de manutenção e custos de adoção.
6. "tabela_comparativa_html": Tabela HTML clássica (com <table>, <thead>, <tbody>, classes Tailwind) mapeando as {len(items)} ferramentas do toolkit (Colunas: Ferramenta, Papel no Fluxo, Repositório/Métricas, Alternativa Tradicional).
7. "guia_poc_passo_a_passo": Guia prático de setup unificado, comandos CLI sequenciais para preparar o ambiente e rodar um fluxo integrado usando as ferramentas do toolkit.
8. "veredito_final": Veredito executivo de engenharia sobre a maturidade do toolkit e em quais cenários vale a pena adotá-lo.
"""

    else:
        # Investigação de Ferramenta Única
        tech_name = pedido.get("tech_name", "Tecnologia")
        repo_name = pedido.get("repo_name", "")
        if not repo_name and pedido.get("repo_url"):
            m = re.search(r'github\.com/([^/]+/[^/]+)', pedido.get("repo_url", ""), re.IGNORECASE)
            if m:
                repo_name = m.group(1).rstrip(".git").strip("/")
                pedido["repo_name"] = repo_name

        logger.info(f"Buscando README oficial de {repo_name} no GitHub...")
        readme_text = obter_readme_github(repo_name) if repo_name else ""

        logger.info("Gerando análise técnica e arquitetural com Gemini...")
        prompt = f"""
Você é um Arquiteto de Software Sênior e Especialista do Knowledge OS.
Sua missão é produzir uma pesquisa técnica aprofundada, altamente estruturada e profissional sobre a seguinte tecnologia:

--- DADOS DA INVESTIGAÇÃO ---
Tecnologia: {tech_name}
Repositório GitHub: {repo_name} ({pedido.get('repo_url', '')})
Estrelas / Tração: {pedido.get('stars_display', 'N/D')}
Foco Solicitado pelo Usuário: {foco}
Requisito / Pergunta Específica do Usuário: {duvida}
Resumo Preliminar: {pedido.get('summary', '')}

README DO REPOSITÓRIO GITHUB:
\"\"\"{readme_text if readme_text else 'README não disponível publicamente no momento.'}\"\"\"
-----------------------------

Gere uma estrutura JSON com os seguintes campos em PORTUGUÊS DO BRASIL:
1. "subtitulo": Uma frase de impacto definindo a tecnologia.
2. "resumo_executivo": 2 parágrafos densos explicando a proposta de valor, como funciona e por que é relevante.
3. "arquitetura_e_funcionamento": Explicação detalhada da arquitetura, stack de linguagens, dependências e fluxo de dados.
4. "resposta_requisito_usuario": Resposta técnica direta e aprofundada para o requisito/pergunta do usuário: "{duvida}".
5. "analise_viabilidade": Pontos fortes, limitações técnicas, requisitos de infraestrutura e custos envolvidos.
6. "tabela_comparativa_html": Tabela HTML clássica (com <table>, <thead>, <tbody>, classes Tailwind) comparando esta tecnologia com 2 ou 3 alternativas conhecidas de mercado.
7. "guia_poc_passo_a_passo": Código e comandos práticos em bash/python para clonar, configurar variáveis de ambiente e rodar um exemplo mínimo funcional (PoC).
8. "veredito_final": Veredito executivo recomendando quando usar e quando evitar.
"""

    modelos = ["gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-3.5-flash"]
    res = None
    for m in modelos:
        try:
            res = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            if res and res.text:
                break
        except Exception as e:
            logger.warning(f"Tentativa com {m} falhou ({e}). Tentando próximo...")

    if not res or not res.text:
        raise RuntimeError("Não foi possível gerar a pesquisa com a IA.")

    return parse_json_resiliente(res.text)


def parse_json_resiliente(raw_text: str) -> dict:
    """
    Faz o parse de JSON de forma ultra-resiliente contra erros de caracteres de controle
    e code fences em strings literais geradas pela IA.
    """
    if not raw_text:
        return {}

    texto = raw_text.strip()
    # Remover markdown code fences
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
        texto = texto.strip()

    # 1. Tentativa com strict=False (tolera caracteres de controle literais)
    try:
        return json.loads(texto, strict=False)
    except Exception as e:
        logger.warning(f"json.loads inicial com strict=False falhou ({e}). Tentando saneamento...")

    # 2. Saneamento de caracteres de controle ASCII inválidos (< 0x20 exceto \r, \n, \t)
    texto_saneado = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', texto)
    try:
        return json.loads(texto_saneado, strict=False)
    except Exception:
        pass

    # 3. Fallback inteligente de extração por regex para recuperar os campos
    campos = [
        "subtitulo",
        "resumo_executivo",
        "arquitetura_e_funcionamento",
        "resposta_requisito_usuario",
        "analise_viabilidade",
        "tabela_comparativa_html",
        "guia_poc_passo_a_passo",
        "veredito_final"
    ]
    dados = {}
    for campo in campos:
        padrao = rf'"{campo}"\s*:\s*("(?:\\.|[^"\\])*"|\{{.*?\}}|\[.*?\])'
        m = re.search(padrao, texto, re.DOTALL)
        if m:
            val_raw = m.group(1).strip()
            if val_raw.startswith('"') and val_raw.endswith('"'):
                dados[campo] = val_raw[1:-1].replace(r'\"', '"').replace(r'\n', '\n')
            else:
                try:
                    dados[campo] = json.loads(val_raw, strict=False)
                except Exception:
                    dados[campo] = val_raw
        else:
            dados[campo] = ""

    if any(dados.values()):
        logger.info("JSON reconstruído com sucesso via regex fallback.")
        return dados

    raise ValueError(f"Não foi possível decodificar a resposta JSON da IA. Detalhe: {texto[:200]}")


def formatar_campo_html(valor) -> str:
    """Converte qualquer tipo gerado pela IA (str, dict, list) para HTML limpo com segurança."""
    if not valor:
        return ""
    if isinstance(valor, str):
        return valor.replace("\n", "<br/><br/>")
    if isinstance(valor, dict):
        partes = []
        for k, v in valor.items():
            label = str(k).replace("_", " ").title()
            partes.append(f"<p class='mb-2'><b>{label}:</b> {formatar_campo_html(v)}</p>")
        return "".join(partes)
    if isinstance(valor, list):
        itens = "".join([f"<li class='mb-1'>{formatar_campo_html(it)}</li>" for it in valor])
        return f"<ul class='list-disc pl-5 my-2 space-y-1'>{itens}</ul>"
    return str(valor)


def formatar_codigo_poc(valor) -> str:
    """Garante que o guia de execução PoC seja formatado com segurança para o bloco <pre>."""
    if not valor:
        return "# Nenhuma instrução adicional necessária."
    if isinstance(valor, str):
        return valor.strip()
    if isinstance(valor, dict):
        linhas = []
        for k, v in valor.items():
            linhas.append(f"# === {str(k).upper()} ===")
            if isinstance(v, (dict, list)):
                linhas.append(json.dumps(v, ensure_ascii=False, indent=2))
            else:
                linhas.append(str(v))
        return "\n\n".join(linhas)
    if isinstance(valor, list):
        return "\n".join([str(it) for it in valor])
    return str(valor)


def construir_documento_html(pedido: dict, dados_ia: dict) -> Path:
    """Cria o documento HTML oficial usando a CLI scripts/novo_documento.py e insere o conteúdo."""
    slug = pedido.get("slug", "tech")
    tech_name = pedido.get("tech_name", "Tecnologia")
    is_col = pedido.get("is_collection", False)
    items = pedido.get("items", [])

    saida_dir = REPO_ROOT / "projetos" / "pesquisas" / slug
    saida_dir.mkdir(parents=True, exist_ok=True)
    arquivo_html = saida_dir / f"pesquisa-{slug}.html"

    if is_col:
        titulo_doc = f"Pesquisa de Ecossistema: {tech_name}"
        tags = f"Pesquisa, Toolkit, Arquitetura, Open-Source, {tech_name}"
    else:
        titulo_doc = f"Pesquisa Técnica: {tech_name}"
        tags = f"Pesquisa, Engenharia, Open-Source, {tech_name}"

    # 1. Executa Scaffolding Oficial do Knowledge OS (Regra 5 do AGENTS.md)
    cmd_scaffold = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "novo_documento.py"),
        "--titulo", titulo_doc,
        "--arquivo", str(arquivo_html),
        "--preset", "pesquisa-tecnica",
        "--tags", tags,
        "--force"
    ]
    logger.info(f"Executando scaffolding oficial para {arquivo_html.name}...")
    subprocess.run(cmd_scaffold, check=True, encoding="utf-8", errors="replace")

    # 2. Injeta o conteúdo estruturado dentro de <main>
    hoje = datetime.now().strftime("%d/%m/%Y")
    
    if is_col:
        links_ferramentas = " | ".join([
            f"<a href=\"{it.get('repo_url') or '#'}\" target=\"_blank\" class=\"underline font-semibold\">{it.get('tech_name')}</a> ({it.get('stars_display', 'N/D')})"
            for it in items
        ])
        bloco_meta_callout = (
            f"<p class=\"text-sky-800 text-xs mt-2\"><b>Foco Solicitado:</b> {pedido.get('foco_nome', 'Geral')} | "
            f"<b>Composição ({len(items)} Ferramentas):</b> {links_ferramentas}</p>"
        )
    else:
        bloco_meta_callout = (
            f"<p class=\"text-sky-800 text-xs mt-2\"><b>Foco Solicitado:</b> {pedido.get('foco_nome', 'Geral')} | "
            f"<b>Repositório:</b> <a href=\"{pedido.get('repo_url', '#')}\" target=\"_blank\" class=\"underline\">{pedido.get('repo_name', tech_name)}</a> ({pedido.get('stars_display', 'N/D')} stars)</p>"
        )

    conteudo_artigo = f"""
    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">1. Resumo Executivo</h2>
      <div class="callout callout-info mb-6">
        <p class="font-semibold text-sky-900 mb-1">🎯 Proposta de Valor & Foco da Investigação</p>
        <p class="text-sky-800 text-sm leading-relaxed">{formatar_campo_html(dados_ia.get('subtitulo', ''))}</p>
        {bloco_meta_callout}
      </div>
      <div class="text-slate-700 leading-relaxed space-y-4">
        {formatar_campo_html(dados_ia.get('resumo_executivo', ''))}
      </div>
    </section>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">2. Arquitetura e Engenharia Reversa</h2>
      <div class="text-slate-700 leading-relaxed mb-6">
        {formatar_campo_html(dados_ia.get('arquitetura_e_funcionamento', ''))}
      </div>
    </section>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">3. Resposta aos Requisitos Específicos</h2>
      <div class="callout callout-warning mb-6">
        <p class="font-semibold text-amber-900 mb-1">💬 Pergunta / Dúvida do Usuário:</p>
        <p class="italic text-amber-800 text-sm mb-3">"{pedido.get('duvida_especifica') or 'Análise geral de aplicabilidade técnica.'}"</p>
        <div class="text-amber-950 text-sm leading-relaxed border-t border-amber-200/60 pt-3">
          {formatar_campo_html(dados_ia.get('resposta_requisito_usuario', ''))}
        </div>
      </div>
    </section>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">4. Análise de Viabilidade & Trade-offs</h2>
      <div class="text-slate-700 leading-relaxed mb-6">
        {formatar_campo_html(dados_ia.get('analise_viabilidade', ''))}
      </div>

      <h3 class="text-lg font-bold text-slate-800 mb-3">Quadro Comparativo com Alternativas de Mercado</h3>
      <div class="overflow-x-auto mb-6">
        {formatar_campo_html(dados_ia.get('tabela_comparativa_html', ''))}
      </div>
    </section>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">5. Guia Prático de Execução & PoC</h2>
      <div class="text-slate-700 leading-relaxed mb-4">
        Instruções cirúrgicas para reproduzir e testar localmente no seu ambiente:
      </div>
      <div class="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-xs overflow-x-auto mb-6">
        <pre>{formatar_codigo_poc(dados_ia.get('guia_poc_passo_a_passo', ''))}</pre>
      </div>
    </section>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">6. Veredito Técnico do Antigravity</h2>
      <div class="callout callout-success">
        <p class="font-semibold text-emerald-900 mb-1">⚖️ Conclusão da Investigação:</p>
        <p class="text-emerald-800 text-sm leading-relaxed">{formatar_campo_html(dados_ia.get('veredito_final', ''))}</p>
      </div>
    </section>

    <section class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">7. Linha do Tempo da Investigação</h2>
      <div class="timeline mt-6">
        <div class="timeline-item">
          <div class="timeline-dot"></div>
          <div class="flex items-center gap-2 mb-1">
            <span class="font-semibold text-slate-800 text-sm">{hoje}</span>
            <span class="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">Captura Inicial</span>
          </div>
          <h4 class="font-semibold text-slate-900 text-base">Reel do Instagram Identificado</h4>
          <p class="text-sm text-slate-600 mt-0.5">
            Vídeo do Instagram capturado e analisado por visão multimodal e áudio via bot Telegram.
          </p>
        </div>
        <div class="timeline-item">
          <div class="timeline-dot"></div>
          <div class="flex items-center gap-2 mb-1">
            <span class="font-semibold text-slate-800 text-sm">{hoje}</span>
            <span class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">Dossiê Aprofundado</span>
          </div>
          <h4 class="font-semibold text-slate-900 text-base">Auditoria e Compilação Oficial</h4>
          <p class="text-sm text-slate-600 mt-0.5">
            Auditoria de repositório, README e compilação do relatório executivo no ecossistema Antigravity Knowledge OS.
          </p>
        </div>
      </div>
    </section>
"""

    html_content = arquivo_html.read_text(encoding="utf-8")
    padrao_main = re.compile(r'(<main[^>]*>)(.*?)(</main>)', re.DOTALL)
    if padrao_main.search(html_content):
        # Escapar barras invertidas no conteudo_artigo antes da substituicao
        escaped_conteudo = conteudo_artigo.replace('\\', '\\\\')
        html_atualizado = padrao_main.sub(rf'\1\n{escaped_conteudo}\n\3', html_content)
        arquivo_html.write_text(html_atualizado, encoding="utf-8")
        logger.info(f"Conteúdo técnico da pesquisa injetado com sucesso em {arquivo_html.name}")
    else:
        logger.error(f"Falha crítica: tag <main> não encontrada em {arquivo_html.name}")

    return arquivo_html


def compilar_pdf(arquivo_html: Path) -> Path:
    """Compila o arquivo HTML em PDF oficial usando o motor scripts/gerar_pdf.py."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "gerar_pdf.py"),
        str(arquivo_html)
    ]
    logger.info(f"Compilando PDF oficial para {arquivo_html.name}...")
    subprocess.run(cmd, check=True, encoding="utf-8", errors="replace")
    
    # O motor de PDF gera na pasta pdf/ ou no mesmo diretório
    pdf_path = arquivo_html.parent / "pdf" / f"{arquivo_html.stem}.pdf"
    if not pdf_path.exists():
        pdf_path = arquivo_html.with_suffix(".pdf")
    return pdf_path


def executar_pedido(pedido_id_ou_caminho: str):
    """Executa um pedido completo de pesquisa de ponta a ponta."""
    pedido_path = None
    if Path(pedido_id_ou_caminho).exists():
        pedido_path = Path(pedido_id_ou_caminho)
    else:
        # Busca por ID ou padrão
        candidatos = list(PEDIDOS_DIR.glob(f"*{pedido_id_ou_caminho}*.json"))
        if candidatos:
            pedido_path = candidatos[0]

    if not pedido_path or not pedido_path.exists():
        logger.error(f"Pedido não encontrado: {pedido_id_ou_caminho}")
        sys.exit(1)

    with open(pedido_path, "r", encoding="utf-8") as f:
        pedido = json.load(f)

    logger.info(f"=== Iniciando Pesquisa Aprofundada para {pedido.get('tech_name')} ===")
    logger.info(f"Foco: {pedido.get('foco_nome')}")
    logger.info(f"Requisito: {pedido.get('duvida_especifica') or 'Geral'}")

    # 1. Análise com IA e extração de dados
    dados_ia = pesquisar_e_estruturar_relatorio(pedido)

    # 2. Criação do HTML com Scaffolding Knowledge OS
    html_path = construir_documento_html(pedido, dados_ia)

    # 3. Compilação do PDF Oficial
    pdf_path = compilar_pdf(html_path)

    # 4. Atualização do status do pedido
    pedido["status"] = "concluido"
    pedido["concluido_em"] = datetime.now().isoformat()
    pedido["arquivo_html"] = str(html_path)
    pedido["arquivo_pdf"] = str(pdf_path)
    with open(pedido_path, "w", encoding="utf-8") as f:
        json.dump(pedido, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ Pesquisa concluída com sucesso!")
    logger.info(f"📄 HTML: {html_path}")
    logger.info(f"📑 PDF: {pdf_path}")

    # 5. Envio automático para o Telegram se o chat_id estiver cadastrado
    chat_id = pedido.get("chat_id")
    if chat_id:
        caption = (
            f"📑 <b>Pesquisa Concluída: {pedido.get('tech_name')}</b>\n\n"
            f"🎯 <b>Foco:</b> {pedido.get('foco_nome')}\n"
            f"⚖️ <b>Veredito:</b> <i>{dados_ia.get('veredito_final', '')[:200]}...</i>\n\n"
            "<i>Arquivo PDF corporativo compilado pelo Antigravity Knowledge OS.</i>"
        )
        enviar_documento_telegram(int(chat_id), pdf_path, caption)


def main():
    parser = argparse.ArgumentParser(description="Motor de Pesquisa Aprofundada Antigravity")
    parser.add_argument("--listar", action="store_true", help="Lista todos os pedidos de pesquisa pendentes")
    parser.add_argument("--pedido", type=str, help="ID ou caminho do arquivo do pedido a executar")
    parser.add_argument("--ultimo", action="store_true", help="Executa o pedido mais recente da fila")

    args = parser.parse_args()

    if args.listar:
        pedidos = sorted(PEDIDOS_DIR.glob("PESQ-*.json"), reverse=True)
        if not pedidos:
            print("Nenhum pedido de pesquisa encontrado.")
            return
        print(f"\n📋 Pedidos de Pesquisa ({len(pedidos)} encontrados):")
        for p in pedidos:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    status_emoji = "✅" if d.get("status") == "concluido" else "⏳"
                    print(f" {status_emoji} [{d.get('id')}] {d.get('tech_name')} ({d.get('foco_nome')}) - Status: {d.get('status')}")
            except Exception:
                continue
        return

    if args.ultimo:
        pedidos = sorted(PEDIDOS_DIR.glob("PESQ-*.json"), reverse=True)
        if not pedidos:
            print("Nenhum pedido disponível na fila.")
            return
        executar_pedido(str(pedidos[0]))
        return

    if args.pedido:
        executar_pedido(args.pedido)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
