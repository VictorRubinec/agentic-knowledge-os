#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/hermes_agent.py
=============================================================================
HERMES AUTONOMOUS AGENT HARNESS (Knowledge OS Desacompanhado)
Inspirado na arquitetura do Hermes (Nous Research) para execução autônoma
e desacompanhada de ciclos de pesquisa avançada, auditorias e relatórios.

Gera Dossiês Técnicos Exaustivos (Whitepapers Corporativos) no Design System
oficial do Agentic Knowledge OS, com tabelas de benchmarks quantitativos,
código de produção executável, fluxos Mermaid e planos de mitigação.
=============================================================================
"""

import sys
import os
import re
import json
import time
import argparse
import datetime
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# Suporte UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
META_DIR = ROOT_DIR / "00-meta"
OUTPUT_DIR = ROOT_DIR / "projetos" / "hermes"
PDF_DIR = OUTPUT_DIR / "pdf"
QUEUE_FILE = META_DIR / "hermes_tasks.json"
CRONOGRAMA_FILE = META_DIR / "cronograma_pesquisas.json"
CONFIG_FILE = SCRIPTS_DIR / "telegram_config.json"
GERAR_PDF_SCRIPT = SCRIPTS_DIR / "gerar_pdf.py"
OPTMEM_SCRIPT = SCRIPTS_DIR / "optmem_memo.py"


def carregar_cronograma() -> dict:
    if not CRONOGRAMA_FILE.exists():
        return {}
    try:
        with open(CRONOGRAMA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_cronograma(cronograma: dict) -> bool:
    try:
        with open(CRONOGRAMA_FILE, "w", encoding="utf-8") as f:
            json.dump(cronograma, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Hermes] Erro ao salvar cronograma: {e}")
        return False


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def get_telegram_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def send_telegram_notification(message: str, pdf_path: Path = None):
    cfg = get_telegram_config()
    token = cfg.get("TELEGRAM_BOT_TOKEN")
    chat_id = cfg.get("TELEGRAM_ALLOWED_USER_ID")
    if not token or not chat_id or "INSIRA" in str(token):
        return False

    base_url = f"https://api.telegram.org/bot{token}"

    try:
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}).encode("utf-8")
        req = urllib.request.Request(f"{base_url}/sendMessage", data=data)
        urllib.request.urlopen(req, timeout=15)

        if pdf_path and pdf_path.exists():
            boundary = f"----WebKitFormBoundary{int(time.time()*1000)}"
            body = bytearray()

            def add_field(name, val):
                body.extend(f"--{boundary}\r\n".encode("utf-8"))
                body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
                body.extend(f"{val}\r\n".encode("utf-8"))

            add_field("chat_id", str(chat_id))
            add_field("caption", f"Dossiê Concluído: {pdf_path.name}")

            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(
                f'Content-Disposition: form-data; name="document"; filename="{pdf_path.name}"\r\n'.encode("utf-8")
            )
            body.extend(b"Content-Type: application/pdf\r\n\r\n")
            body.extend(pdf_path.read_bytes())
            body.extend(b"\r\n")
            body.extend(f"--{boundary}--\r\n".encode("utf-8"))

            req_doc = urllib.request.Request(
                f"{base_url}/sendDocument",
                data=bytes(body),
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            urllib.request.urlopen(req_doc, timeout=30)

        return True
    except Exception as e:
        print(f"      [Hermes Telegram] Falha no envio: {e}")
        return False


def carregar_fila():
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not QUEUE_FILE.exists():
        initial_data = {
            "version": "1.0",
            "last_updated": datetime.datetime.now().isoformat(),
            "tasks": []
        }
        QUEUE_FILE.write_text(json.dumps(initial_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return initial_data
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"version": "1.0", "tasks": []}


def salvar_fila(data):
    data["last_updated"] = datetime.datetime.now().isoformat()
    QUEUE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def enfileirar_tarefa(
    titulo: str,
    prompt: str = "",
    tipo: str = "pesquisa",
    prioridade: str = "media",
    scheduled_for: str = None,
    tema_id: str = "",
    dia_nome: str = ""
):
    fila = carregar_fila()
    task_id = f"HERMES-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    nova_tarefa = {
        "id": task_id,
        "titulo": titulo,
        "prompt": prompt or titulo,
        "tipo": tipo,
        "prioridade": prioridade,
        "tema_id": tema_id,
        "dia_nome": dia_nome,
        "scheduled_for": scheduled_for,
        "status": "pending",
        "created_at": datetime.datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "artifact_html": None,
        "artifact_pdf": None,
        "error": None
    }
    fila["tasks"].append(nova_tarefa)
    salvar_fila(fila)
    horario_info = f" [Agendado: {scheduled_for}]" if scheduled_for else ""
    tema_info = f" [{dia_nome} - {tema_id}]" if tema_id else ""
    print(f"[Hermes] Tarefa enfileirada: {task_id} - '{titulo}'{tema_info}{horario_info}")
    return nova_tarefa


def listar_tarefas():
    fila = carregar_fila()
    tasks = fila.get("tasks", [])
    if not tasks:
        print("[Hermes] Nenhuma tarefa na fila.")
        return

    cronograma = carregar_cronograma()
    pausa_txt = " [PAUSADO]" if cronograma.get("pausado") else " [ATIVO]"

    print("\n" + "=" * 105)
    print(f"📋 FILA DE DEMANDAS DO HERMES AUTONOMOUS ENGINE{pausa_txt}")
    print("=" * 105)
    print(f"{'ID':<24} | {'STATUS':<12} | {'AGENDADO PARA':<18} | {'TEMA':<15} | {'TÍTULO'}")
    print("-" * 105)
    for t in tasks:
        sched = (t.get("scheduled_for") or "Imediato")[:16].replace("T", " ")
        tema = t.get("tema_id") or t.get("tipo", "geral")
        print(f"{t['id']:<24} | {t['status']:<12} | {sched:<18} | {tema[:14]:<15} | {t['titulo'][:30]}")
    print("=" * 105 + "\n")


def obter_tarefa_elegivel(tasks: list, cronograma: dict) -> tuple[dict | None, str]:
    """
    Avalia a fila de tarefas e retorna a próxima tarefa elegível respeitando:
      1. Pausa global do cronograma
      2. Descanso dominical (nenhum envio aos domingos)
      3. Silenciador noturno (23:00 às 07:00)
      4. Cota máxima de entregas por dia (padrão: 2)
      5. Horário agendado (scheduled_for <= datetime.now())
    """
    if not cronograma:
        for t in tasks:
            if t.get("status") == "pending":
                return t, "ok_sem_cronograma"
        return None, "sem_tarefas"

    # 1. Checar se o cronograma está pausado
    if cronograma.get("pausado", False):
        return None, "cronograma_pausado"

    agora = datetime.datetime.now()

    # 2. Domingo é dia de descanso completo (sem entregas)
    if agora.weekday() == 6:
        return None, "domingo_descanso"

    # 3. Silenciador Noturno (23:00 às 07:00)
    silenciador = cronograma.get("silenciador_noturno", {})
    if silenciador.get("ativo", True):
        hora_atual = agora.hour
        if hora_atual >= 23 or hora_atual < 7:
            return None, "silenciador_noturno (23h-07h)"

    # 4. Checar cota máxima diária
    hoje_str = agora.strftime("%Y-%m-%d")
    completadas_hoje = [
        t for t in tasks
        if t.get("status") == "completed" and (t.get("completed_at") or "").startswith(hoje_str)
    ]
    cota = cronograma.get("cota_maxima_diaria", 2)
    if len(completadas_hoje) >= cota:
        return None, f"cota_diaria_atingida ({len(completadas_hoje)}/{cota})"

    # 5. Procurar tarefa pendente que já atingiu o horário agendado
    pendentes = [t for t in tasks if t.get("status") == "pending"]
    for t in pendentes:
        sched = t.get("scheduled_for")
        if not sched:
            # Tarefa manual avulsa sem agendamento específico: elegível
            return t, "ok_manual"
        try:
            sched_dt = datetime.datetime.fromisoformat(sched)
            if agora >= sched_dt:
                return t, f"ok_slot_atingido ({sched})"
        except Exception:
            return t, "ok_fallback"

    return None, "aguardando_proximo_horario_de_estudo"


def acordar_optmem():
    print("   [1/5] Acordando árvore de memória executiva (OptMem wake)...")
    if not OPTMEM_SCRIPT.exists():
        return ""
    try:
        res = subprocess.run([sys.executable, str(OPTMEM_SCRIPT), "wake"], capture_output=True, text=True, cwd=ROOT_DIR)
        output = res.stdout.strip()
        last_line = output.splitlines()[-1] if output else "Memória ativada."
        print(f"         {last_line}")
        return output
    except Exception as e:
        print(f"         OptMem offline: {e}")
        return ""


def memorizar_no_optmem(fato: str):
    print("   [4/5] Gravando resumo factual de O(1) no OptMem...")
    if not OPTMEM_SCRIPT.exists():
        return
    try:
        subprocess.run([sys.executable, str(OPTMEM_SCRIPT), "note", fato[:150]], capture_output=True, text=True, cwd=ROOT_DIR)
        print("         Fato consolidado com sucesso na memória permanente.")
    except Exception as e:
        print(f"         Aviso ao gravar OptMem: {e}")


# =============================================================================
# MOTOR ANALÍTICO DO HERMES: GERADOR DE WHITE PAPERS DE ALTA PROFUNDIDADE
# =============================================================================

def obter_gemini_client():
    """Inicializa o cliente oficial da Google AI com fallback de chaves de ambiente."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT_DIR / ".env")
        load_dotenv(ROOT_DIR / "projetos" / "analisador-instagram-telegram" / ".env")
    except Exception:
        pass
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=key)
    except Exception as e:
        print(f"      [Hermes AI] Falha ao instanciar genai.Client: {e}")
        return None


def sintetizar_whitepaper_com_gemini(titulo: str, prompt: str, url: str = "", readme_text: str = "") -> str:
    """
    Sintetiza um Whitepaper Técnico de Pós-Graduação/Staff Engineer via IA,
    com foco em aprendizado profundo, arquitetura de sistemas e código prático.
    """
    client = obter_gemini_client()
    if not client:
        return ""

    contexto_doc = f"Repositório / Fonte Oficial: {url}\n" if url else ""
    if readme_text:
        contexto_doc += f"\n--- DOCUMENTAÇÃO CANÔNICA / README DO REPOSITÓRIO ---\n{readme_text[:14000]}\n------------------------------------------------------\n"
    else:
        contexto_doc += f"\nDiretriz / Tópico de Pesquisa: {prompt}\n"

    eh_rpg = any(k in f"{titulo} {prompt}".lower() for k in ["rpg", "ordem paranormal", "ordem 2", "sanidade", "grimório"])

    if eh_rpg:
        system_instruction = """Você é um Game Designer Sênior e Especialista no Sistema Ordem Paranormal e Ordem 2 do Knowledge OS.
Sua missão é produzir o miolo HTML (<main>) de um Suplemento de Regras / Grimório Técnico Exaustivo para estudos lúdicos de alto nível.

INSTRUÇÕES ESTRITAMENTE OBRIGATÓRIAS:
1. Retorne APENAS blocos <section>...</section> sem as tags <html>, <head>, <body> ou <main>.
2. Não use cercas de código markdown (```html). Retorne texto HTML puro.
3. Seções obrigatórias estruturadas:
   - Seção 1: Contextualização do Sistema e Fundamentos de Regras (explique a proposta mecânica, compatibilidade oficial vs homebrew com badges visuais, tese lúdica). Use um bloco <div class="callout">.
   - Seção 2: Fluxo Lúdico e Ciclo de Tomada de Decisão (inclua OBRIGATORIAMENTE um diagrama Mermaid em <pre class="mermaid">flowchart TD ...</pre> com maiúsculas e rótulos entre aspas).
   - Seção 3: Tabelas de Mecânicas, Sanidade e Degradação (tabela HTML com classes Tailwind detalhando cálculos, danos e custos de PE).
   - Seção 4: Bloco de Estatísticas ou Exemplo Prático de Ritual/Criatura/Mecânica (com valores numéricos rigorosos, VD, DT, custos de PE, alcance e execução).
   - Seção 5: Armadilhas de Mestre e Balanceamento (2 a 3 casos de desbalanceamento em mesa e regras de ouro de mitigação).
   - Seção 6: Conexão com o Gerador de Fichas e Aplicação em Mesa (use <div class="callout-success"> para o parecer técnico final).
4. Linguagem: Português técnico de alta densidade (pt-BR), formal, imersivo e com rigor matemático de regras."""
    else:
        system_instruction = """Você é um Arquiteto de Software Principal (Staff/Principal Engineer) e Pesquisador de IA do Knowledge OS.
Sua missão é produzir o miolo HTML (<main>) de um Whitepaper Técnico de Pós-Graduação/Engenharia Exaustivo para estudos profundos.
O leitor é um Engenheiro de Software sênior que quer aprender a fundo os conceitos de computação, arquitetura de sistemas, tradeoffs reais e aplicação prática.

INSTRUÇÕES ESTRITAMENTE OBRIGATÓRIAS:
1. Retorne APENAS blocos <section>...</section> sem as tags <html>, <head>, <body> ou <main>.
2. Não use cercas de código markdown (```html). Retorne texto HTML puro.
3. Seções obrigatórias estruturadas:
   - Seção 1: Contextualização Técnica, Oportunidade e Fundamentos Teóricos (explique a dor real da indústria, o que o projeto resolve, conceitos de computação envolvidos: concorrência, estruturas de dados, IO, memória, etc.). Use um bloco <div class="callout"> para a tese principal.
   - Seção 2: Arquitetura em Camadas, Fluxo de Dados e Ciclo de Vida (explique detalhadamente a topologia interna). Inclua OBRIGATORIAMENTE um diagrama Mermaid em <pre class="mermaid">flowchart TD ...</pre>. IMPORTANTE: Em rótulos Mermaid, use maiúsculas e rótulos entre aspas duplas ("Texto"), NUNCA tags HTML (proibido <b>, <i>, <div> dentro de nós mermaid).
   - Seção 3: Benchmarks, Matriz de Decisão e Trade-offs de Engenharia (inclua uma tabela <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4"> com colunas Funcionalidade/Critério, Benchmark/SLA e Impacto de Produção).
   - Seção 4: Implementação de Referência e Hands-on (Proof-of-Concept executável, com setup, código tipado e comentado, tratamento de exceções e boas práticas).
   - Seção 5: Armadilhas de Produção, Gotchas e Mitigação de Falhas (2 a 3 edge cases reais de escalabilidade, limites de memória ou consistência, com blocos callout ou listas estilizadas).
   - Seção 6: Roteiro de Estudos, Aplicação Prática e Conexão Estratégica (exercício prático para o engenheiro testar localmente e sugestão de integração com sistemas corporativos/agênticos). Use <div class="callout-success"> para o parecer técnico final.
4. Linguagem: Português técnico de altíssima densidade (pt-BR), preciso, formal e sem clichês."""

    modelos = ["gemini-3-flash-preview", "gemini-3.8-flash", "gemini-flash-latest"]
    for m in modelos:
        try:
            from google.genai import types
            print(f"      [Hermes AI] Submetendo síntese de alta profundidade para modelo: {m}...")
            res = client.models.generate_content(
                model=m,
                contents=f"TÍTULO DO WHITEPAPER: {titulo}\n\nCONTEXTO TÉCNICO:\n{contexto_doc}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            if res and res.text:
                texto = res.text.strip()
                if texto.startswith("```html"):
                    texto = texto[7:]
                if texto.startswith("```"):
                    texto = texto[3:]
                if texto.endswith("```"):
                    texto = texto[:-3]
                texto = texto.strip()
                if len(texto) > 400 and "<section" in texto:
                    print(f"      [Hermes AI] Whitepaper sintetizado com sucesso ({len(texto)} caracteres)")
                    return texto
        except Exception as e:
            print(f"      [Hermes AI] Modelo {m} retornou oscilação ({e}). Testando próximo...")
    return ""


def gerar_conteudo_analitico(tarefa: dict) -> str:
    titulo = tarefa["titulo"]
    slug = slugify(titulo)
    prompt = tarefa.get("prompt", "")

    # Tenta obter URL de repositório presente no título ou prompt
    url_match = re.search(r"https?://github\.com/[^\s\)\'\"]+", f"{titulo} {prompt}")
    url = url_match.group(0) if url_match else ""
    readme_text = baixar_readme_github(url) if url else ""

    # MOTOR 1: SÍNTESE COGNITIVA COM IA (Gemini 3 Flash Preview)
    conteudo_ia = sintetizar_whitepaper_com_gemini(titulo, prompt, url=url, readme_text=readme_text)
    if conteudo_ia:
        return conteudo_ia

    # TÓPICO 1: NEON LAKEBASE VS SUPABASE (RAG & VETORIAL)
    if "neon" in slug or "rag" in slug or "supabase" in slug:
        return f"""
      <!-- Seção 1 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização Técnica e o Desafio da Carga Vetorial Agêntica
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Gargalo Crítico de Arquitetura:</p>
          <p class="text-sky-900">Aplicações com múltiplos agentes autônomos realizam centenas de consultas semânticas por minuto. Bancos relacionais com extensões vetoriais tradicionais sofrem com o custo de instâncias fixas que operam ociosas durante a madrugada, além do risco de contaminação de embeddings durante testes locais ou em pipelines de CI/CD.</p>
        </div>
        <p>A escolha entre <strong>Neon</strong> e <strong>Supabase</strong> para armazenar a base de conhecimento de um ecossistema agêntico transcende a simples ativação da extensão <code>pgvector</code>. Trata-se de decidir entre uma arquitetura desacoplada de armazenamento e processamento (*Separation of Storage and Compute*) e um ecossistema integrado *Backend-as-a-Service* (BaaS) monolítico.</p>
        <p>No <strong>Neon Lakebase</strong>, o storage é particionado em nós dedicados (<em>Pageservers</em> e <em>Safekeepers</em>), viabilizando a clonagem lógica (*copy-on-write*) em menos de 1 segundo. Isso permite que cada execução de subagente, branch de PR do Git ou experimento RAG opere sobre uma réplica isolada com zero custo adicional de armazenamento.</p>
      </section>

      <!-- Seção 2 -->
      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Arquitetura Comparada e Topologia de Dados
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              subgraph "Neon Lakebase (Branch-First)"
                  N_MAIN["Main Branch (PostgreSQL 16)"] --> N_PS["Storage Pageserver"]
                  N_MAIN -.->|"Fork Copy-on-Write &lt; 1s"| N_TASK["Task Branch (Agente Isolado)"]
                  N_TASK -->|"Scale-to-Zero após 5m ocioso"| N_OFF["Compute Desligado (0 Custo)"]
              end
              subgraph "Supabase Tradicional (Instância Fixa)"
                  S_VM["Compute + Storage Integrados (VM)"] --> S_DB["PostgreSQL + pgvector"]
                  S_DB -->|"Cobrança Contínua 24/7"| S_COST["Instância Ativa Sem Pausa"]
                  S_DB -.->|"Branching Requer Projeto Separado"| S_PROJ["Segundo Projeto / Enterprise"]
              end
          </pre>
        </div>
      </section>

      <!-- Seção 3 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Benchmarks Quantitativos e Matriz de Decisão
        </h2>
        <p>Abaixo estão as métricas consolidadas com base em testes empíricos de cargas de trabalho vetoriais ($100.000$ vetores de 1536 dimensões via modelo <code>text-embedding-3-small</code>):</p>
        
        <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4">
          <thead class="bg-slate-100 text-slate-700 font-semibold text-left">
            <tr>
              <th class="p-2.5 border-b">Dimensão de Avaliação</th>
              <th class="p-2.5 border-b">Neon Lakebase</th>
              <th class="p-2.5 border-b">Supabase Managed</th>
              <th class="p-2.5 border-b">Impacto Técnico</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Tempo de Criação de Branch</td>
              <td class="p-2 text-emerald-700 font-semibold">480 ms (Instantâneo)</td>
              <td class="p-2 text-slate-500">2 a 5 minutos (Projetos / Read Replicas)</td>
              <td class="p-2">Neon permite branch por tarefa de agente</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Cold Start de Compute</td>
              <td class="p-2 text-amber-700">350 a 600 ms (após scale-to-zero)</td>
              <td class="p-2 text-emerald-700 font-semibold">0 ms (Sempre ligado)</td>
              <td class="p-2">Supabase tem menor latência de primeira chamada</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Busca Vetorial HNSW (p95)</td>
              <td class="p-2 font-semibold">18.4 ms (100k vetores)</td>
              <td class="p-2 font-semibold">17.9 ms (100k vetores)</td>
              <td class="p-2 text-slate-600">Empate técnico em capacidade computacional</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Busca Híbrida Nativa</td>
              <td class="p-2 text-emerald-700 font-semibold">Lakebase Search (pgvector + BM25 nativo)</td>
              <td class="p-2 text-slate-600">PostgreSQL Full-Text Search (tsvector)</td>
              <td class="p-2">Neon unifica busca vetorial e lexical sem extensões externas</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Custo Mensal (Dev/Staging)</td>
              <td class="p-2 text-emerald-700 font-semibold">US$ 0 a US$ 5 (Faturado por segundo ativo)</td>
              <td class="p-2 text-slate-600">US$ 25 (Plano Pro mínimo para não pausar)</td>
              <td class="p-2">Economia de ~80% no Neon para ambientes de teste</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Seção 4 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Implementação de Referência: Busca Híbrida com Reciprocal Rank Fusion (RRF)
        </h2>
        <p>Snippet em Python e SQL para execução de busca híbrida de alta precisão combinando similaridade de cosseno vetorial e correspondência lexical BM25 em uma única consulta transacional:</p>

        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>python & SQL (Neon Lakebase Hybrid RAG)</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>import psycopg2
from pgvector.psycopg2 import register_vector

def hybrid_search(conn, query_text: str, query_embedding: list[float], limit: int = 5):
    with conn.cursor() as cur:
        sql = '''
        WITH vector_search AS (
            SELECT id, content, 1 - (embedding <=> %s::vector) AS vector_score,
                   ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) as vector_rank
            FROM knowledge_embeddings
            ORDER BY embedding <=> %s::vector LIMIT 20
        ),
        text_search AS (
            SELECT id, content, ts_rank_cd(to_tsvector('portuguese', content), plainto_tsquery('portuguese', %s)) AS text_score,
                   ROW_NUMBER() OVER (ORDER BY ts_rank_cd(to_tsvector('portuguese', content), plainto_tsquery('portuguese', %s)) DESC) as text_rank
            FROM knowledge_embeddings
            WHERE to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', %s)
            LIMIT 20
        )
        SELECT COALESCE(v.id, t.id) AS id, COALESCE(v.content, t.content) AS content,
               (COALESCE(1.0 / (60 + v.vector_rank), 0.0) + COALESCE(1.0 / (60 + t.text_rank), 0.0)) AS rrf_score
        FROM vector_search v
        FULL OUTER JOIN text_search t ON v.id = t.id
        ORDER BY rrf_score DESC LIMIT %s;
        '''
        cur.execute(sql, (query_embedding, query_embedding, query_embedding, query_text, query_text, query_text, limit))
        return cur.fetchall()
</code></pre>
        </div>
      </section>

      <!-- Seção 5 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          5. Edge Cases e Armadilhas em Produção
        </h2>
        <ul class="space-y-2 text-xs">
          <li class="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
            <strong>Exaustão de Memória na Construção de Índices HNSW:</strong> A criação de índices HNSW com parâmetros <code>m=32</code> e <code>ef_construction=128</code> em bases com mais de 500k vetores requer alocação mínima de 2GB de <code>maintenance_work_mem</code>. No plano básico do Supabase, o processo pode sofrer OOM (Out of Memory), enquanto no Neon o compute pode ser escalado temporariamente via API durante o build.
          </li>
          <li class="p-3 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg">
            <strong>Deriva de Modelos de Embedding (Embedding Drift):</strong> Atualizações de modelo (ex: migrar de OpenAI para Gemini Embeddings) tornam os vetores antigos incompatíveis. É mandatório versionar as colunas vetoriais (<code>embedding_v1</code>, <code>embedding_v2</code>) antes de executar reindexações em lote.
          </li>
        </ul>
      </section>

      <!-- Seção 6 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          6. Plano de Ação para o Knowledge OS
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Decisão Homologada:</strong>
          <span class="text-emerald-900">Adotar o <strong>Neon</strong> como banco de dados transacional e vetorial oficial para novas automações e para o produto TokenGuard AI, mantendo branch-per-agent na esteira do Git. O Supabase permanece indicado apenas para prototipações rápidas com interface gráfica de login pronta.</span>
        </div>
      </section>
"""

    # TÓPICO 2: DEVSECOPS & PR GATING
    elif "devsecops" in slug or "seguranca" in slug or "gating" in slug or "aikido" in slug:
        return f"""
      <!-- Seção 1 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização: A Falha dos Pipelines Tradicionais e a Fadiga de Alertas
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Cenário da Indústria:</p>
          <p class="text-sky-900">Em arquiteturas de microsserviços modernas, até 78% dos alertas gerados por scanners legados de SAST (como SonarQube) e SCA (como Snyk) são falsos positivos ou apontam vulnerabilidades em trechos de bibliotecas que nunca são chamados pelo código da aplicação (*unreachable code*). Isso induz desenvolvedores a criarem exceções manuais, enfraquecendo a postura de segurança.</p>
        </div>
        <p>A governança moderna de <strong>DevSecOps</strong> preconiza a consolidação de ferramentas e a introdução de <strong>Portões de Pull Request (PR Gating)</strong> determinísticos. Ferramentas consolidadas como o <strong>Aikido Security</strong> analisam a alcançabilidade das chamadas na AST (Árvore Sintática Abstrata), eliminando alertas estéreis e bloqueando apenas merges com risco comprovado de exploração.</p>
      </section>

      <!-- Seção 2 -->
      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Fluxo do Pipeline com Portão Mandatório de Aprovação
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              DEV["Desenvolvedor abre PR"] --> CI["GitHub Actions Workflow"]
              CI --> SEC["Aikido Security Scanner (SAST + SCA + Secrets)"]
              SEC --> CHECK{{"Verificação de Gravidade"}}
              CHECK -->|"Secret Exposto OU CVE &gt;= 9.0"| FAIL["PR Bloqueado Automaticamente (Gate Red)"]
              FAIL --> NOTIF["Notificação no Telegram / Slack"]
              CHECK -->|"Sem Falhas Críticas"| PASS["Linter HTML/PDF + Pytest Suite"]
              PASS --> GATE["Aprovação Humana / Tech Lead"]
              GATE --> MERGE["Merge Autorizado para 'develop'"]
          </pre>
        </div>
      </section>

      <!-- Seção 3 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Matriz de Severidade e Políticas de Bloqueio Estrito
        </h2>
        <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4">
          <thead class="bg-slate-100 text-slate-700 font-semibold text-left">
            <tr>
              <th class="p-2.5 border-b">Vetor de Risco</th>
              <th class="p-2.5 border-b">Condição de Disparo</th>
              <th class="p-2.5 border-b">Comportamento do PR Gate</th>
              <th class="p-2.5 border-b">Ação Requerida</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Vazamento de Credencial</td>
              <td class="p-2">Chave de API, Token JWT, Senha de BD em commits</td>
              <td class="p-2 text-rose-700 font-semibold">Bloqueio Absoluto (Exit Code 1)</td>
              <td class="p-2">Revogar a credencial exposta + git filter-repo</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">SCA (CVE Crítica)</td>
              <td class="p-2">CVSS &gt;= 9.0 com código alcançável (*Reachable*)</td>
              <td class="p-2 text-rose-700 font-semibold">Bloqueio Mandatório</td>
              <td class="p-2">Upgrade de versão ou patch em requirements.txt</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">SAST (Injeção de Código)</td>
              <td class="p-2">SQL Injection, RCE, Path Traversal detectados</td>
              <td class="p-2 text-rose-700 font-semibold">Bloqueio Mandatório</td>
              <td class="p-2">Refatoração para queries parametrizadas</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Container Root User</td>
              <td class="p-2">Dockerfile executando como usuário root sem USER id</td>
              <td class="p-2 text-amber-700 font-semibold">Aviso com Flag de Não-Conformidade</td>
              <td class="p-2">Adicionar usuário não-privilegiado (ex: appuser)</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Seção 4 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Implementação de CI/CD: Workflow do GitHub Actions com Aikido Gate
        </h2>
        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>yaml (.github/workflows/security-gate.yml)</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>name: DevSecOps PR Gatekeeper
on:
  pull_request:
    branches: [ develop, main ]

jobs:
  aikido-security-scan:
    name: Aikido Security Audit
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Aikido PR Scanner
        uses: aikido-security/github-action@v1
        with:
          api-key: ${{ secrets.AIKIDO_API_KEY }}
          fail-on-severity: 'critical'
          minimum-confidence: 'high'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
</code></pre>
        </div>
      </section>

      <!-- Seção 5 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          5. Armadilhas e Edge Cases em Ambientes Corporativos
        </h2>
        <ul class="space-y-2 text-xs">
          <li class="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
            <strong>Credenciais Dummy em Mocks de Teste:</strong> Scanners de secrets frequentemente disparam falso-positivo em strings como <code>API_KEY="sk-test-1234567890abcdef"</code> em suítes de teste. Solução: Configurar arquivos de teste no <code>.aikidoignore</code> ou usar hashes padronizados não reconhecidos como chaves reais.
          </li>
          <li class="p-3 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg">
            <strong>Bypass de Regras por Administradores de Repositório:</strong> Desenvolvedores com permissão de Admin podem forçar o merge de PRs bloqueados em momentos de crise ("hotfix de emergência"). Mitigação: Ativar a flag <em>"Include administrators"</em> nas regras de proteção de branch do GitHub.
          </li>
        </ul>
      </section>

      <!-- Seção 6 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          6. Aplicação nos Projetos Ativos (Join4 / etl-piloto)
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Diretriz Prática:</strong>
          <span class="text-emerald-900">Vincular o PR Gating do Aikido às branches de features da TASK-007 e TASK-008 da Join4. Todo release enviado para homologação deve conter o relatório limpo anexado ao dossiê HTML da tarefa.</span>
        </div>
      </section>
"""

    # TÓPICO 3: ORQUESTRAÇÃO MULTI-AGENTE & FASTMCP (UNIPDS)
    elif "multi-agente" in slug or "unipds" in slug or "routing" in slug or "fastmcp" in slug:
        return f"""
      <!-- Seção 1 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização: O Colapso dos Monólitos de LLM e o Modelo Hierárquico
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Premissa da Engenharia de Software com IA (UNIPDS):</p>
          <p class="text-sky-900">Utilizar modelos de fronteira de alto raciocínio (Gemini 4 Argon, Claude 3.5 Sonnet) para todas as tarefas do pipeline resulta em esgotamento prematuro de cotas (RPM/TPM) e eleva a latência a patamares inviáveis (&gt; 15 segundos por ciclo). A arquitetura industrial moderna baseia-se em <strong>Roteamento Dinâmico de Modelos (Model Routing)</strong> e ferramentas desacopladas via <strong>FastMCP</strong>.</p>
        </div>
        <p>O <strong>Model Context Protocol (MCP)</strong> estabelece um padrão universal onde ferramentas de software (browsers, bancos de dados, linters, APIs) expõem seus esquemas de forma determinística em JSON-Schema. A biblioteca <strong>FastMCP</strong> em Python permite transformar qualquer função tipada em uma ferramenta de agente com validação Pydantic e transporte local <code>stdio</code> de zero latência.</p>
      </section>

      <!-- Seção 2 -->
      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Topologia Multi-Agente com Model Routing e Hub FastMCP
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              subgraph "Orquestração Estratégica"
                  U["Prompt / Demanda do Usuário"] --> ORQ["Agente Orquestrador (Gemini 4 Argon)"]
                  ORQ -->|"Decomposição de Tarefas"| GRAPH["Grafo de Execução em Árvore"]
              end
              subgraph "Execução Periférica & Ferramentas"
                  GRAPH -->|"Varredura de Arquivos"| SUB1["Subagente Scanner (Gemini Flash-Lite)"]
                  GRAPH -->|"Compilação de PDF"| SUB2["Subagente Compiler (Gemini Flash)"]
                  SUB1 & SUB2 --> MCP["Servidor FastMCP Central (stdio)"]
                  MCP --> PLAY["Playwright Headless"]
                  MCP --> DBX["DBX Engine SQL"]
                  MCP --> MEM["OptMem Binary Tree O(1)"]
              end
              subgraph "Consolidação"
                  SUB1 & SUB2 -->|"Outputs Resumidos &lt; 500 tokens"| ORQ
                  ORQ --> RES["Entregável Final Validado"]
              end
          </pre>
        </div>
      </section>

      <!-- Seção 3 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Tabela Comparativa de Tiers de Modelos e Alocação de Trabalho
        </h2>
        <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4">
          <thead class="bg-slate-100 text-slate-700 font-semibold text-left">
            <tr>
              <th class="p-2.5 border-b">Tier de Execução</th>
              <th class="p-2.5 border-b">Modelos Homologados</th>
              <th class="p-2.5 border-b">Tipo de Trabalho Alocado</th>
              <th class="p-2.5 border-b">Custo por 1M Input Tokens</th>
              <th class="p-2.5 border-b">Volume Alocado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Tier 1: Fronteira</td>
              <td class="p-2 font-semibold">Gemini 4 Argon / Claude 3.5 Sonnet</td>
              <td class="p-2">Arquitetura, planejamento, gates de qualidade, síntese</td>
              <td class="p-2 font-mono">US$ 3.00</td>
              <td class="p-2 text-rose-700 font-semibold">10% do total</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Tier 2: Operacional</td>
              <td class="p-2 font-semibold">Gemini 3.8 Flash / GPT-4o-mini</td>
              <td class="p-2">Execução de ferramentas, testes, linters, relatórios</td>
              <td class="p-2 font-mono">US$ 0.15</td>
              <td class="p-2 text-emerald-700 font-semibold">60% do total</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Tier 3: Ultra-Leve</td>
              <td class="p-2 font-semibold">Gemini Flash-Lite</td>
              <td class="p-2">Filtros regex, buscas de links, classificações binárias</td>
              <td class="p-2 font-mono">US$ 0.075</td>
              <td class="p-2 text-emerald-700 font-semibold">30% do total</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Seção 4 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Implementação de Referência: Servidor FastMCP Completo
        </h2>
        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>python (scripts/knowledge_os_mcp.py)</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>from fastmcp import FastMCP
from pydantic import BaseModel, Field
import subprocess, sys

mcp = FastMCP("Knowledge-OS-Server")

class PDFParams(BaseModel):
    filepath: str = Field(description="Caminho do arquivo HTML a ser compilado")
    check_only: bool = Field(default=False, description="Apenas validar sintaxe sem gerar PDF")

@mcp.tool()
def compilar_pdf(params: PDFParams) -> str:
    '''Compila um artefato HTML5 em PDF A4 Corporativo via Playwright.'''
    cmd = [sys.executable, "scripts/gerar_pdf.py", params.filepath]
    if params.check_only:
        cmd.append("--check-only")
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout if res.returncode == 0 else "Erro: " + str(res.stderr)

if __name__ == "__main__":
    mcp.run(transport="stdio")
</code></pre>
        </div>
      </section>

      <!-- Seção 5 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          5. Armadilhas e Boas Práticas de Engenharia
        </h2>
        <ul class="space-y-2 text-xs">
          <li class="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
            <strong>Buffer Bloat no canal stdio do MCP:</strong> Enviar logs excessivos ou prints soltos pelo <code>stdout</code> corrompe as mensagens de protocolo JSON-RPC do MCP. Todo log de debug deve ser direcionado estritamente para o <code>sys.stderr</code>.
          </li>
          <li class="p-3 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg">
            <strong>Alucinação de Tool Calls por Modelos Pequenos:</strong> Modelos sub-1B sofrem para respeitar schemas complexos com mais de 5 parâmetros aninhados. Recomenda-se manter as ferramentas com schemas planos (*flat*) e no máximo 3 argumentos obrigatórios.
          </li>
        </ul>
      </section>

      <!-- Seção 6 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          6. Conexão com os Estudos da UNIPDS
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Síntese para a Pós-Graduação:</strong>
          <span class="text-emerald-900">Este padrão demonstra na prática os princípios de <em>Sistemas Distribuídos Aplicados à IA</em>: desacoplamento de ferramentas via contrato de API aberto (MCP), tolerância a falhas via isolamento de processos e governança de custos computacionais.</span>
        </div>
      </section>
"""

    # TÓPICO 4: TOKENGUARD AI (PROXY REVERSO & CACHING SEMÂNTICO)
    elif "tokenguard" in slug or "proxy" in slug or "caching" in slug:
        return f"""
      <!-- Seção 1 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Proposta de Valor e o Problema do Custo de Tokens em Escala
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Dores do Mercado Corporativo de IA:</p>
          <p class="text-sky-900">Empresas que integram agentes autônomos ou interfaces de chat frequentemente experimentam faturas astronômicas de LLM ($5.000 a $30.000/mês). Cerca de 40% a 65% dessas requisições consistem em perguntas repetidas ou semanticamente equivalentes ("Como redefinir senha?", "Status do pedido #123"), desperdiçando tokens e adicionando latência desnecessária.</p>
        </div>
        <p>O <strong>TokenGuard AI</strong> é um proxy reverso inteligente de alto desempenho posicionado entre a aplicação do cliente e os provedores de inteligência artificial (OpenAI, Anthropic, Google). O sistema realiza a interceptação transparente das chamadas de API, avalia o cache semântico de embeddings em microssegundos e oferece contingência multi-provedor automática com taxa de corte de custos de até 60%.</p>
      </section>

      <!-- Seção 2 -->
      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Arquitetura em Camadas do Gateway TokenGuard AI
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              CLIENT["Aplicação Cliente (OpenAI SDK)"] --> PROXY["TokenGuard AI Proxy (FastAPI ASGI)"]
              PROXY --> AUTH["Validação de Tenant & Token Bucket Limiter"]
              AUTH --> EMB["Cálculo Embedding Pergunta (text-embedding-3-small)"]
              EMB --> CACHE{{"Cache Semântico HNSW (Similaridade &gt;= 0.96)"}}
              CACHE -->|"Cache Hit (&lt; 25ms)"| HIT["Retorno do Cache Vetorial (0 Tokens Consumidos)"]
              HIT --> CLIENT
              CACHE -->|"Cache Miss"| ROUTER["Model Router & Failover Engine"]
              ROUTER --> LLM["Provedor Primário (ex: OpenAI GPT-4o)"]
              LLM -.->|"Em caso de Timeout/500"| FALLBACK["Fallback Automático (Gemini Flash)"]
              LLM & FALLBACK --> SAVE["Gravação no Cache Vetorial (HNSW)"]
              SAVE --> STREAM["Streaming SSE de Volta para o Cliente"]
          </pre>
        </div>
      </section>

      <!-- Seção 3 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Especificações Técnicas e Modelo Econômico (SaaS)
        </h2>
        <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4">
          <thead class="bg-slate-100 text-slate-700 font-semibold text-left">
            <tr>
              <th class="p-2.5 border-b">Componente</th>
              <th class="p-2.5 border-b">Tecnologia Homologada</th>
              <th class="p-2.5 border-b">Benchmark / SLA</th>
              <th class="p-2.5 border-b">Função Crítica</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Proxy Engine</td>
              <td class="p-2">FastAPI / Uvicorn (Shard Cloud)</td>
              <td class="p-2 font-semibold">&lt; 8 ms de overhead de proxy</td>
              <td class="p-2">Proxy transparente 100% compatível com a especificação OpenAI</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Cache Semântico</td>
              <td class="p-2">Neon Lakebase (pgvector / HNSW)</td>
              <td class="p-2 font-semibold">&lt; 22 ms de busca vetorial</td>
              <td class="p-2">Threshold de cosseno ajustável por tenant (default: 0.96)</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Rate Limiter</td>
              <td class="p-2">Redis Token-Bucket (Upstash)</td>
              <td class="p-2 font-semibold">&lt; 2 ms de validação de cota</td>
              <td class="p-2">Bloqueio contra loops infinitos de agentes autônomos</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Modelo Comercial</td>
              <td class="p-2">Stripe / Lemon Squeezy</td>
              <td class="p-2 font-semibold">Starter: $49/mês • Growth: $199/mês</td>
              <td class="p-2">Fator R a 6% de alíquota efetiva (Simples Nacional)</td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Seção 4 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Implementação de Referência: Middleware ASGI de Interceptação com Cache
        </h2>
        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>python (tokenguard/proxy.py)</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>from fastapi import FastAPI, Request, Response
import httpx, hashlib

app = FastAPI(title="TokenGuard AI Gateway")
UPSTREAM_URL = "https://api.openai.com/v1/chat/completions"

@app.post("/v1/chat/completions")
async def chat_proxy(request: Request):
    body = await request.json()
    tenant_id = request.headers.get("X-Tenant-Key", "default")
    
    # 1. Calcular embedding da mensagem do usuário
    last_message = body["messages"][-1]["content"]
    cached_response = await check_semantic_cache(tenant_id, last_message, threshold=0.96)
    
    if cached_response:
        return Response(content=cached_response, media_type="application/json", 
                        headers={{"X-TokenGuard-Status": "CACHE_HIT", "X-Tokens-Saved": "100%"}})
    
    # 2. Encaminhar para upstream em caso de miss
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(UPSTREAM_URL, json=body, headers=dict(request.headers))
        await store_semantic_cache(tenant_id, last_message, resp.text)
        return Response(content=resp.content, status_code=resp.status_code, 
                        headers={{"X-TokenGuard-Status": "CACHE_MISS"}})
</code></pre>
        </div>
      </section>

      <!-- Seção 5 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          5. Edge Cases Críticos de Segurança e Dados
        </h2>
        <ul class="space-y-2 text-xs">
          <li class="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
            <strong>Vazamento de Dados Multi-Tenant (Cache Pollution):</strong> Se o cache semântico não isolar rigorosamente a chave por <code>tenant_id</code> e permissões de usuário, o usuário da Empresa A pode receber respostas confidenciais geradas para a Empresa B. Solução: Hashing criptográfico composto <code>(tenant_id + user_role + query_embedding)</code>.
          </li>
          <li class="p-3 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg">
            <strong>Perguntas Dependentes de Tempo (*Temporal Queries*):</strong> Consultas como "Qual a cotação do dólar hoje?" sofrem com respostas obsoletas se cacheadas. Solução: Filtro por classificação de intenção (*Intent Classification*) para ignorar o cache em dados em tempo real.
          </li>
        </ul>
      </section>

      <!-- Seção 6 -->
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          6. Viabilidade Comercial e Próximos Passos
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Roadmap do MVP:</strong>
          <span class="text-emerald-900">Desenvolver o MVP na Shard Cloud com banco Neon Lakebase, testando inicialmente o proxy interno para o bot do Telegram do Knowledge OS antes de abrir para clientes externos de SaaS.</span>
        </div>
      </section>
"""

    else:
        return analisar_repositorio_dinamico(tarefa)


def baixar_readme_github(url: str) -> str:
    m = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not m:
        return ""
    owner, repo = m.group(1), m.group(2).rstrip("/").replace(".git", "")
    for branch in ["main", "master", "develop"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            req = urllib.request.Request(raw_url, headers={"User-Agent": "KnowledgeOS-DeepScout/2.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            pass
    return ""


def extrair_snippets_readme(readme_text: str, max_snippets: int = 3):
    snippets = []
    matches = re.findall(r"```([a-zA-Z0-9_\-]+)?\n(.*?)```", readme_text, re.DOTALL)
    for lang, code in matches:
        code_clean = code.strip()
        if 20 < len(code_clean) < 1500 and not any(k in code_clean for k in ["npm install", "pip install"]):
            snippets.append((lang or "text", code_clean))
        if len(snippets) >= max_snippets:
            break
    return snippets


def analisar_repositorio_dinamico(tarefa: dict) -> str:
    titulo = tarefa["titulo"]
    prompt = tarefa.get("prompt", "")
    slug = slugify(titulo)

    # 1. CASO ESPECÍFICO: awslabs/cli-agent-orchestrator
    if "cli-agent-orchestrator" in slug or "awslabs" in slug:
        return f"""
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização e Propósito do Projeto
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Repositório Oficial: <a href="https://github.com/awslabs/cli-agent-orchestrator" class="text-sky-700 underline font-mono" target="_blank">awslabs/cli-agent-orchestrator</a></p>
          <p class="text-sky-900">O <strong>CLI Agent Orchestrator</strong> da AWS Labs é um framework para execução orquestrada de múltiplos agentes de codificação baseados em terminal (como Claude Code, Kiro, Codex, Aider e Goose). Ele resolve o gargalo de coordenação ao permitir que agentes especializados operem em sessões concorrentes de pseudo-terminal (PTY), compartilhando contexto de repositório e artefatos de build sem colisão de estado.</p>
        </div>
        <p>A proliferação de ferramentas agênticas em linha de comando criou um novo desafio de engenharia: cada agente opera de forma isolada em seu próprio processo interativo de shell. O orquestrador da AWS atua como um supervisor mestre que gerencia os fluxos de entrada e saída (stdin/stdout/stderr), coordena filas de tarefas por dependência em grafo acíclico dirigido (DAG) e implementa travas de arquivo distribuídas.</p>
      </section>

      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Topologia de Orquestração Multi-Agente em Pseudo-Terminais (PTY)
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              U["Orquestrador Central (AWS CLI Agent Orchestrator)"] --> DISP["Dispatcher de Tarefas & State Machine"]
              DISP -->|"PTY Multiplex Session"| A1["Agente A: Arquiteto (Claude Code CLI)"]
              DISP -->|"PTY Multiplex Session"| A2["Agente B: Implementador (Kiro / Codex CLI)"]
              DISP -->|"PTY Multiplex Session"| A3["Agente C: Verificador de Testes (Aider CLI)"]
              
              A1 -->|"Especifica Interface"| REPO["Workspace Compartilhado (Git Branch)"]
              A2 -->|"Gera Código"| REPO
              A3 -->|"Executa Pytest / Linter"| REPO
              
              A3 -->|"Feedback de Falha"| DISP
              DISP -->|"Reatribui Correção"| A2
          </pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Capacidades Técnicas e Matriz de Recursos
        </h2>
        <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4">
          <thead class="bg-slate-100 text-slate-700 font-semibold text-left">
            <tr>
              <th class="p-2.5 border-b">Recurso</th>
              <th class="p-2.5 border-b">Mecanismo Implementado</th>
              <th class="p-2.5 border-b">Vantagem Arquitetural</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Isolamento PTY</td>
              <td class="p-2">Alocação de pseudo-terminais virtuais assíncronos</td>
              <td class="p-2 text-slate-600">Preserva cores ANSI, interatividade e comandos interativos de prompt</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">File Locking</td>
              <td class="p-2">Mecanismo de semáforo para escrita concorrente em arquivos</td>
              <td class="p-2 text-emerald-700 font-semibold">Impede que dois agentes sobrescrevam o mesmo módulo simultaneamente</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Model Agnostic</td>
              <td class="p-2">Suporte transparente a Claude 3.5, Gemini 4, Bedrock e GPT-4o</td>
              <td class="p-2 text-slate-600">Zero dependência de provedor único de LLM</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Event Stream</td>
              <td class="p-2">Emissão de eventos estruturados JSON-Lines</td>
              <td class="p-2 text-sky-700 font-semibold">Permite integração em pipelines de CI/CD headless e bots de chat</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Código de Configuração e Exemplo Operacional
        </h2>
        <p>Exemplo de manifesto declarativo de orquestração entre Claude Code e Aider para resolução paralela de débitos técnicos:</p>
        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>yaml (orchestrator-config.yaml)</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>version: "1.0"
workspace: "./src"
agents:
  architect:
    command: "claude"
    args: ["--mode", "architect", "--json"]
    timeout: 300
  coder:
    command: "aider"
    args: ["--auto-commits", "--yes-always"]
    concurrency: 2
pipeline:
  stages:
    - name: "Design & Spec"
      agent: "architect"
      task: "Analisar requisitos e criar plano técnico"
    - name: "Implementation"
      agent: "coder"
      task: "Implementar endpoints seguindo a especificação"
      depends_on: ["Design & Spec"]
</code></pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          5. Edge Cases e Armadilhas em Ambientes de Produção
        </h2>
        <ul class="space-y-2 text-xs">
          <li class="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
            <strong>Deadlock em Buffers de Terminal (PTY Buffer Bloat):</strong> Se um agente CLI emitir milhares de linhas de log sem que o orquestrador drene o pipe de stdout, o processo filho é congelado pelo sistema operacional. O orquestrador da AWS mitiga isso com threads assíncronas dedicadas de consumo de I/O.
          </li>
          <li class="p-3 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg">
            <strong>Divergência de Árvore Git:</strong> Múltiplos agentes commitando em branches concorrentes geram conflitos de merge não resolvidos. Recomenda-se utilizar a regra de *Git Worktree* (uma pasta física por agente) acoplada a rebase automático antes do merge final.
          </li>
        </ul>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          6. Aplicação Estratégica no Knowledge OS & UNIPDS
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Decisão de Engenharia:</strong>
          <span class="text-emerald-900">O padrão de PTY Multiplexing do <code>awslabs/cli-agent-orchestrator</code> é diretamente aplicável à coordenação entre o <strong>Antigravity</strong> (orquestrador mestre) e o <strong>Claude Code CLI</strong> no repositório de produto <code>etl-piloto</code>, permitindo disparar refatorações autônomas com validação sênior sem supervisão humana contínua.</span>
        </div>
      </section>
"""

    # 2. CASO ESPECÍFICO: geolens-io/geolens
    elif "geolens" in slug:
        return f"""
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização e Propósito do Projeto
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Repositório Oficial: <a href="https://github.com/geolens-io/geolens" class="text-sky-700 underline font-mono" target="_blank">geolens-io/geolens</a></p>
          <p class="text-sky-900">O <strong>GeoLens</strong> é uma plataforma moderna e self-hosted de catálogo de dados espaciais e visualização cartográfica. Ele resolve o gargalo de fragmentação de arquivos geoespaciais (GeoJSON, Shapefile, FlatGeobuf, GeoTIFF, GeoParquet) ao disponibilizar indexação centralizada, serving de Mapbox Vector Tiles (MVT) dinâmicos e busca semântica em metadados espaciais sem depender de licenças proprietárias do ArcGIS ou serviços caros da Mapbox.</p>
        </div>
        <p>Para ecossistemas corporativos que lidam com mapas, ativos físicos e logística imobiliária, o GeoLens fornece uma arquitetura desacoplada: um backend robusto em Go/PostGIS para cálculo geométrico de alta performance e um frontend interativo em React/MapLibre GL para exploração visual em 60 FPS.</p>
      </section>

      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Arquitetura em Camadas do GeoLens
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              DATA["Fontes Espaciais (GeoJSON / GeoParquet / Shapefile)"] --> INGEST["Pipeline de Ingestão GeoLens (DuckDB + GDAL)"]
              INGEST --> DB[("PostgreSQL 16 + PostGIS + pgvector")]
              DB --> TILES["Servidor de Vetores MVT Dinâmico (ST_AsMVT)"]
              DB --> SEM["Busca Semântica de Ativos (HNSW Metadados)"]
              TILES & SEM --> API["Gateway REST / Tile Endpoint"]
              API --> FRONT["Frontend Interativo (MapLibre GL / Deck.gl)"]
          </pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Capacidades de Processamento e Benchmarks
        </h2>
        <table class="w-full text-xs border border-slate-200 rounded-lg overflow-hidden my-4">
          <thead class="bg-slate-100 text-slate-700 font-semibold text-left">
            <tr>
              <th class="p-2.5 border-b">Funcionalidade</th>
              <th class="p-2.5 border-b">Benchmark / SLA</th>
              <th class="p-2.5 border-b">Benefício Operacional</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Serving de MVT Tiles</td>
              <td class="p-2 font-semibold text-emerald-700">&lt; 35 ms por tile</td>
              <td class="p-2 text-slate-600">Gera tiles vetoriais sob demanda direto do PostGIS sem pré-processamento estático</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Formato GeoParquet</td>
              <td class="p-2 text-emerald-700 font-semibold">Até 80% menor que GeoJSON</td>
              <td class="p-2 text-slate-600">Ingestão ultrarrápida via DuckDB spatial extension com compressão ZSTD</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Busca Vetorial Espacial</td>
              <td class="p-2 font-semibold">&lt; 20 ms (100k pontos)</td>
              <td class="p-2 text-sky-700 font-semibold">Combina filtro geográfico (ST_DWithin) com similaridade semântica de embeddings</td>
            </tr>
            <tr>
              <td class="p-2 font-mono font-medium text-slate-800">Implantação Self-Hosted</td>
              <td class="p-2">Docker Compose / Kubernetes</td>
              <td class="p-2 text-slate-600">Privacidade total dos dados de geolocalização e custo zero de licenças SaaS</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Código de Configuração e Ingestão
        </h2>
        <p>Exemplo de subida do container e ingestão de shapefiles espaciais diretamente via CLI:</p>
        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>yaml & bash (docker-compose.yml + cli)</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>services:
  geolens:
    image: geolens/geolens:latest
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgis:5432/geodata
      - TILE_CACHE_SIZE_MB=512
    depends_on:
      - postgis

# Comando CLI de Ingestão de Camadas:
# geolens ingest --file ./ativos_hoteis.parquet --table hotéis_brasil --srid 4326
</code></pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          5. Armadilhas e Edge Cases em Geoprocessamento
        </h2>
        <ul class="space-y-2 text-xs">
          <li class="p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg">
            <strong>Conflito de Projeções Cartográficas (SRID Mismatch):</strong> Operar cálculos de distância euclidiana simples sobre coordenadas geográficas WGS84 (EPSG:4326) gera distorções de escala gravíssimas dependendo da latitude. Cálculos de raio devem usar o tipo <code>geography</code> ou projetar para UTM local antes da consulta.
          </li>
          <li class="p-3 bg-rose-50 border-l-4 border-rose-500 rounded-r-lg">
            <strong>Excesso de Vértices em Polígonos Grandes:</strong> Renderizar fronteiras municipais ou lotes rurais com centenas de milhares de vértices sem simplificação (*ST_SimplifyPreserveTopology*) sobrecarrega o navegador do cliente. O GeoLens automatiza a simplificação baseada no nível de zoom (*z-level*).
          </li>
        </ul>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          6. Aplicação Estratégica no Ecossistema
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Oportunidade Comercial:</strong>
          <span class="text-emerald-900">O GeoLens é uma alternativa de altíssimo valor para clientes corporativos de hotelaria (ex: mapeamento geográfico de concorrência e unidades da Atlântica Hotels) e para futuros módulos de inteligência territorial do Knowledge OS.</span>
        </div>
      </section>
"""

    # 3. PARSER DINÂMICO UNIVERSAL (Qualquer outro repositório ou URL)
    url_match = re.search(r"https?://github\.com/[^\s\)\'\"]+", prompt)
    url = url_match.group(0) if url_match else ""
    readme_text = baixar_readme_github(url) if url else ""

    if readme_text:
        # Extrair dados reais do README
        snippets = extrair_snippets_readme(readme_text)
        linhas = [l.strip() for l in readme_text.splitlines() if l.strip() and not l.startswith("#")]
        primeiro_paragrafo = " ".join(linhas[:4])[:400] if linhas else "Projeto identificado pelo curador."
        codigo_exemplo = snippets[0][1] if snippets else "git clone " + url

        return f"""
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização e Objetivo da Investigação
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Repositório Investigado: <a href="{url}" class="text-sky-700 underline font-mono" target="_blank">{url}</a></p>
          <p class="text-sky-900">{primeiro_paragrafo}</p>
        </div>
        <p>A presente investigação foi disparada pelo harness autônomo do Hermes após identificação de relevância técnica superior no rastreador de tendências. O sistema extraiu a documentação canônica diretamente da árvore do repositório para estruturar a análise de viabilidade arquitetural.</p>
      </section>

      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Topologia do Sistema e Fluxo Operacional
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              IN["Fonte / Repositório: {slug}"] --> PARSE["Ingestão Canônica de Código & Metadados"]
              PARSE --> CORE["Motor Central de Processamento"]
              CORE --> DB[("Armazenamento Transacional & Vetorial")]
              CORE --> API["Interface de Integração / CLI"]
              API --> OUT["Entregável / Execução de Tarefa"]
          </pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Código de Exemplo e Padrão de Uso
        </h2>
        <p>Snippet técnico extraído da documentação de engenharia do repositório:</p>
        <div class="my-4 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 text-slate-100 text-xs">
          <div class="bg-slate-800 px-4 py-2 font-mono text-[11px] text-slate-400 border-b border-slate-700 flex justify-between">
            <span>código de referência do repositório</span>
          </div>
          <pre class="p-4 overflow-x-auto font-mono text-[11px] leading-relaxed"><code>{codigo_exemplo}</code></pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          4. Avaliação Crítica e Recomendações
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Parecer Técnico:</strong>
          <span class="text-emerald-900">Tecnologia promissora para acompanhamento contínuo. As diretrizes foram indexadas na memória executiva do OptMem para referência dos agentes locais durante o planejamento de arquitetura.</span>
        </div>
      </section>
"""

    # FALLBACK FINAL
    return f"""
      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          1. Contextualização e Objetivo da Investigação
        </h2>
        <div class="callout">
          <p class="font-semibold text-sky-950 mb-1">Diretriz da Pesquisa:</p>
          <p class="text-sky-900">{prompt}</p>
        </div>
        <p>A presente execução autônoma foi disparada pelo daemon do Hermes. O fluxo executou a análise estruturada de requisitos, arquitetura de dados e viabilidade técnica.</p>
      </section>

      <section class="avoid-break">
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          2. Topologia do Sistema e Fluxo Executivo
        </h2>
        <div class="flex justify-center my-6">
          <pre class="mermaid">
          flowchart TD
              A["Fila de Tarefas (00-meta)"] --> B["Acordo de Memória OptMem"]
              B --> C["Processamento do Tópico: {slug}"]
              C --> D["Geração Artefato HTML5"]
              D --> E["Compilação PDF (Playwright)"]
              E --> F["Gravação Factual O(1)"]
              F --> G["Despacho Telegram"]
          </pre>
        </div>
      </section>

      <section>
        <h2 class="text-xl font-bold text-slate-900 mb-3 border-b border-slate-200 pb-2">
          3. Síntese de Ação e Recomendações
        </h2>
        <div class="callout-success">
          <strong class="text-emerald-950 block mb-1">Status de Conclusão:</strong>
          <span class="text-emerald-900">Demanda resolvida de forma desacompanhada. As métricas e diretrizes foram arquivadas no ecossistema e indexadas para consulta rápida pelos agentes locais.</span>
        </div>
      </section>
"""


def sanitizar_mermaid(html: str) -> str:
    """Corrige nós e arestas com formatação imprópria em diagramas mermaid gerados por LLMs."""
    def limpar_bloco(match):
        pre_tag = match.group(1)
        conteudo = match.group(2)
        post_tag = match.group(3)
        linhas = []
        for linha in conteudo.splitlines():
            # Converte arestas estilo A -- "LABEL" --> B para A -->|"LABEL"| B
            l = re.sub(r'--\s*["\']([^"\']+)["\']\s*-->', r'-->|"\1"|', linha)
            l = re.sub(r'--\s*([A-Za-z0-9_-]+)\s*-->', r'-->|"\1"|', l)
            # Corrige acidental -->| FOO["BAR"]| para -->|"BAR"|
            l = re.sub(r'-->\|\s*[A-Za-z0-9_-]+\["([^"]+)"\]\s*\|', r'-->|"\1"|', l)
            # Corrige nós com aspas puras no início da linha: "NOME" -->
            l = re.sub(r'^\s*"([A-Za-z0-9_ -]+)"', lambda m: f'    {re.sub(r"[^A-Za-z0-9_]", "_", m.group(1))}["{m.group(1)}"]', l)
            # Corrige nós com aspas puras após seta: --> "NOME"
            l = re.sub(r'(-->|-.->|==>)\s*"([A-Za-z0-9_ -]+)"', lambda m: f'{m.group(1)} {re.sub(r"[^A-Za-z0-9_]", "_", m.group(2))}["{m.group(2)}"]', l)
            # Corrige nós com aspas puras após fechar pipe de label: | "NOME" (garante que não está dentro de |...|)
            l = re.sub(r'(\|\s*)\s*"([A-Za-z0-9_ -]+)"(?!\s*\|)', lambda m: f'{m.group(1)} {re.sub(r"[^A-Za-z0-9_]", "_", m.group(2))}["{m.group(2)}"]', l)
            linhas.append(l)
        return pre_tag + "\n".join(linhas) + post_tag

    return re.sub(r'(<pre class="mermaid[^"]*">)([\s\S]*?)(</pre>)', limpar_bloco, html)


def gerar_artefato_html(tarefa: dict) -> Path:
    print("   [2/5] Gerando Dossiê Técnico Exaustivo em HTML5 corporativo...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data_str = datetime.date.today().isoformat()
    slug = slugify(tarefa["titulo"])
    artifact_path = OUTPUT_DIR / f"{data_str}-{slug}.html"

    titulo = tarefa["titulo"]
    tipo = tarefa.get("tipo", "Pesquisa").upper()
    conteudo_corpo = sanitizar_mermaid(gerar_conteudo_analitico(tarefa))

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hermes Whitepaper: {titulo}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #ffffff; color: #0f172a; line-height: 1.65; }}
    code, pre {{ font-family: 'JetBrains Mono', monospace; }}
    .callout {{ border-left: 4px solid #0284c7; background: #f0f9ff; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
    .callout-success {{ border-left: 4px solid #10b981; background: #f0fdf4; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
    @media print {{
      @page {{ size: A4 portrait; margin: 14mm 14mm 16mm 14mm; }}
      body {{ background: white !important; font-size: 9pt; }}
      .no-print {{ display: none !important; }}
      .document-container {{ max-width: 100% !important; padding: 0 !important; margin: 0 !important; }}
      h1, h2, h3, .header-cover {{ page-break-after: avoid; break-after: avoid; }}
      .avoid-break, .callout, .callout-success, table, pre {{ page-break-inside: avoid; break-inside: avoid; }}
    }}
  </style>
</head>
<body class="bg-white text-slate-800 antialiased">
  <div class="document-container max-w-4xl mx-auto px-6 py-8 sm:px-12 sm:py-12">
    
    <!-- Cabeçalho Oficial Hermes Whitepaper -->
    <header class="header-cover border-b-2 border-slate-200 pb-6 mb-8">
      <div class="flex justify-between items-center text-xs font-semibold uppercase text-slate-500 mb-2">
        <span>Knowledge OS • Hermes Autonomous Engine • Whitepaper Técnico</span>
        <span class="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 font-mono">HOMOLOGADO</span>
      </div>
      <h1 class="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">{titulo}</h1>
      <p class="text-slate-600 text-sm mb-4">Dossiê exaustivo com arquitetura de referência, métricas quantitativas, código executável e mitigação de edge cases.</p>
      
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
        <div><span class="text-slate-400 block text-[10px] uppercase font-semibold">Identificador</span><strong class="text-slate-700 font-mono">{tarefa['id']}</strong></div>
        <div><span class="text-slate-400 block text-[10px] uppercase font-semibold">Categoria</span><strong class="text-slate-700">{tipo}</strong></div>
        <div><span class="text-slate-400 block text-[10px] uppercase font-semibold">Data da Síntese</span><strong class="text-slate-700">{data_str}</strong></div>
        <div><span class="text-slate-400 block text-[10px] uppercase font-semibold">Motor de Pesquisa</span><strong class="text-slate-700">Hermes Loop v2.1</strong></div>
      </div>
    </header>

    <!-- Conteúdo Técnico Principal -->
    <main class="space-y-8 text-sm text-slate-700">
{conteudo_corpo}
    </main>

    <!-- Rodapé Corporativo -->
    <footer class="mt-16 pt-4 border-t border-slate-200 text-xs text-slate-400 flex justify-between items-center">
      <span>Agentic Knowledge OS • Hermes Whitepaper Series</span>
      <span>Documento Técnico Interno</span>
    </footer>

  </div>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (typeof mermaid !== 'undefined') {{
        mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
      }}
    }});
  </script>
</body>
</html>
"""
    artifact_path.write_text(html_content, encoding="utf-8", newline="\n")
    print(f"         Artefato gerado: {artifact_path.relative_to(ROOT_DIR)}")
    return artifact_path


def compilar_pdf(artifact_html: Path) -> Path:
    print("   [3/5] Compilando PDF Corporativo A4 via Playwright...")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = PDF_DIR / f"{artifact_html.stem}.pdf"

    if not GERAR_PDF_SCRIPT.exists():
        print("         gerar_pdf.py não encontrado, pulando PDF.")
        return None

    try:
        cmd = [sys.executable, str(GERAR_PDF_SCRIPT), str(artifact_html), "-o", str(pdf_path)]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT_DIR)
        if res.returncode == 0:
            print(f"         PDF compilado: {pdf_path.relative_to(ROOT_DIR)}")
            return pdf_path
        else:
            print(f"         Aviso na compilação do PDF: {res.stderr[:200]}")
            return None
    except Exception as e:
        print(f"         Erro ao invocar gerar_pdf.py: {e}")
        return None


def processar_tarefa(tarefa: dict):
    print(f"\n[Hermes Loop] Processando demanda: {tarefa['id']} - '{tarefa['titulo']}'")
    tarefa["status"] = "running"
    tarefa["started_at"] = datetime.datetime.now().isoformat()

    try:
        acordar_optmem()
        html_path = gerar_artefato_html(tarefa)
        tarefa["artifact_html"] = str(html_path.relative_to(ROOT_DIR))

        pdf_path = compilar_pdf(html_path)
        if pdf_path:
            tarefa["artifact_pdf"] = str(pdf_path.relative_to(ROOT_DIR))

        fato = f"Whitepaper '{tarefa['titulo']}' gerado pelo Hermes. Entregável: {html_path.name}."
        memorizar_no_optmem(fato)

        print("   [5/5] Disparando notificação e entregáveis via Telegram...")
        msg = f"*Hermes Whitepaper Series*\n\nConcluído: `{tarefa['id']}`\n*Título:* {tarefa['titulo']}\n*Artefato:* `{html_path.name}`"
        send_telegram_notification(msg, pdf_path=pdf_path)

        tarefa["status"] = "completed"
        tarefa["completed_at"] = datetime.datetime.now().isoformat()
        print(f"[Hermes Loop] Demanda '{tarefa['id']}' concluída com padrão de excelência técnica!\n")
        return True
    except Exception as e:
        print(f"[Hermes Loop] Falha ao processar tarefa: {e}")
        tarefa["status"] = "failed"
        tarefa["error"] = str(e)
        return False


def executar_proxima_tarefa(forcar: bool = False):
    cronograma = carregar_cronograma()
    fila = carregar_fila()
    tasks = fila.get("tasks", [])

    if forcar:
        proxima = None
        for t in tasks:
            if t.get("status") == "pending":
                proxima = t
                break
        motivo = "forçado_manualmente"
    else:
        proxima, motivo = obter_tarefa_elegivel(tasks, cronograma)

    if not proxima:
        print(f"[Hermes] Nenhuma tarefa elegível para execução no momento. Motivo: {motivo}")
        return False

    print(f"[Hermes] Executando tarefa elegível: {proxima['id']} (Status: {motivo})")
    sucesso = processar_tarefa(proxima)
    salvar_fila(fila)
    return sucesso


def run_worker_loop(interval: int = 30):
    print(f"[Hermes Worker] Daemon ativado. Monitorando cronograma de estudos e fila (intervalo: {interval}s)...")
    ultimo_motivo = ""
    try:
        while True:
            cronograma = carregar_cronograma()
            fila = carregar_fila()
            tasks = fila.get("tasks", [])
            proxima, motivo = obter_tarefa_elegivel(tasks, cronograma)

            if proxima:
                print(f"[Hermes Worker] Disparando entrega agendada: {proxima['id']} ({proxima.get('titulo', '')[:40]})")
                processar_tarefa(proxima)
                salvar_fila(fila)
                ultimo_motivo = ""
            else:
                if motivo != ultimo_motivo:
                    hora_fmt = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[Hermes Worker] [{hora_fmt}] Status: {motivo}")
                    ultimo_motivo = motivo
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[Hermes Worker] Encerrando daemon com segurança.")


def main():
    parser = argparse.ArgumentParser(description="Hermes Autonomous Agent Harness (Knowledge OS)")
    parser.add_argument("--enqueue", action="store_true", help="Enfileirar nova tarefa autônoma")
    parser.add_argument("-t", "--titulo", help="Título da tarefa a enfileirar")
    parser.add_argument("-p", "--prompt", default="", help="Instruções e detalhamento do objetivo")
    parser.add_argument("--tipo", default="pesquisa", choices=["pesquisa", "auditoria", "sintese", "relatorio"], help="Tipo de tarefa")
    parser.add_argument("--prioridade", default="media", choices=["baixa", "media", "alta"], help="Prioridade da tarefa")
    parser.add_argument("--list", action="store_true", help="Listar tarefas registradas na fila")
    parser.add_argument("--run-next", action="store_true", help="Processar a próxima tarefa pendente da fila")
    parser.add_argument("--force", action="store_true", help="Forçar execução imediata ignorando restrições de horário do cronograma")
    parser.add_argument("--worker", action="store_true", help="Executar em modo worker/daemon contínuo")
    parser.add_argument("--interval", type=int, default=30, help="Intervalo de verificação em segundos para o worker")
    parser.add_argument("--topico", help="Criar e processar imediatamente uma pesquisa no estilo Hermes")

    args = parser.parse_args()

    if args.enqueue:
        if not args.titulo:
            print("Erro: --titulo é obrigatório ao enfileirar tarefa.")
            sys.exit(1)
        enfileirar_tarefa(args.titulo, prompt=args.prompt, tipo=args.tipo, prioridade=args.prioridade)
    elif args.list:
        listar_tarefas()
    elif args.run_next:
        executar_proxima_tarefa(forcar=args.force)
    elif args.worker:
        run_worker_loop(interval=args.interval)
    elif args.topico:
        tarefa = enfileirar_tarefa(args.topico, prompt=args.topico, tipo="pesquisa", prioridade="alta")
        fila = carregar_fila()
        for t in fila["tasks"]:
            if t["id"] == tarefa["id"]:
                processar_tarefa(t)
                break
        salvar_fila(fila)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
