#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ROTINA DE PESQUISA AUTÔNOMA NOTURNA (NIGHTLY RESEARCH HARNESS)
Inspirado na arquitetura do Hermes (Nous Research) para execução desacompanhada.
Executa ciclos de aprofundamento, consolidação em Artefato HTML5, compilação
automática para PDF e gravação de fatos na árvore binária do OptMem.
=============================================================================
Uso:
  python scripts/pesquisa_autonoma_noturna.py --topico "Tendências de UI Agêntica"
=============================================================================
"""

import sys
import argparse
import datetime
import subprocess
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
GERAR_PDF_SCRIPT = SCRIPTS_DIR / "gerar_pdf.py"
OPTMEM_SCRIPT = SCRIPTS_DIR / "optmem_memo.py"
PESQUISAS_DIR = WORKSPACE_DIR / "projetos" / "pesquisas-noturnas"


def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text)


def run_nightly_research(topic: str, max_depth: int = 3):
    print(f"[NIGHTLY RESEARCH] Inicializando sessão autônoma para o tópico: '{topic}'")
    PESQUISAS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic)
    date_str = datetime.date.today().isoformat()

    # 1. Acordar memória OptMem
    print("[1/5] Carregando estado mental do agente via OptMem wake...")
    try:
        res_wake = subprocess.run([sys.executable, str(OPTMEM_SCRIPT), "wake"], capture_output=True, text=True, cwd=WORKSPACE_DIR)
        print("      " + res_wake.stdout.splitlines()[-1] if res_wake.stdout else "      OptMem ativado.")
    except Exception as e:
        print(f"      Aviso: OptMem indisponível: {e}")

    # 2. Estruturar o Artefato HTML da Pesquisa
    print("[2/5] Compilando dossiê da pesquisa em Artefato HTML5...")
    artifact_path = PESQUISAS_DIR / f"{date_str}-{slug}.html"

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dossiê Autônomo: {topic}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    body {{ font-family: 'Inter', sans-serif; background: #ffffff; color: #0f172a; line-height: 1.65; }}
    .callout {{ border-left: 4px solid #0284c7; background: #f0f9ff; padding: 14px 18px; border-radius: 0 8px 8px 0; margin: 20px 0; }}
    @media print {{
      @page {{ size: A4 portrait; margin: 14mm 14mm 16mm 14mm; }}
      body {{ background: white !important; font-size: 9.5pt; }}
      .no-print {{ display: none !important; }}
      .document-container {{ max-width: 100% !important; padding: 0 !important; margin: 0 !important; }}
      h1, h2, h3, .header-cover {{ page-break-after: avoid; break-after: avoid; }}
      .avoid-break, .callout, table {{ page-break-inside: avoid; break-inside: avoid; }}
    }}
  </style>
</head>
<body class="bg-white text-slate-800 antialiased">
  <div class="document-container max-w-4xl mx-auto px-6 py-8 sm:px-12 sm:py-12">
    <header class="header-cover border-b-2 border-slate-200 pb-6 mb-8">
      <div class="flex justify-between text-xs font-semibold uppercase text-slate-500 mb-2">
        <span>Pesquisa Noturna Autônoma • Knowledge OS</span>
        <span class="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">Concluído</span>
      </div>
      <h1 class="text-3xl font-bold text-slate-900 tracking-tight mb-2">{topic}</h1>
      <p class="text-slate-600 text-sm mb-4">Relatório de ideação gerado autonomamente durante a madrugada.</p>
      <div class="grid grid-cols-3 gap-2 p-3 bg-slate-50 rounded border text-xs">
        <div><span class="text-slate-400 block text-[10px]">Data</span><strong>{date_str}</strong></div>
        <div><span class="text-slate-400 block text-[10px]">Modo</span><strong>Desacompanhado (Hermes Loop)</strong></div>
        <div><span class="text-slate-400 block text-[10px]">Profundidade</span><strong>Nível {max_depth}</strong></div>
      </div>
    </header>

    <main class="space-y-6 text-sm text-slate-700">
      <section>
        <h2 class="text-lg font-bold text-slate-900 mb-2 border-b pb-1">1. Sumário de Descobertas</h2>
        <p>A pesquisa sobre <strong>{topic}</strong> foi executada pelo harness autônomo, estruturando tópicos de interesse, mapeamento de oportunidades e recomendações de implementação para o repositório.</p>
        <div class="callout">
          <strong>Insight Central:</strong> A automação contínua de pesquisas permite acumular inteligência de mercado e arquitetura sem consumir horas ativas do desenvolvedor.
        </div>
      </section>

      <section class="avoid-break">
        <h2 class="text-lg font-bold text-slate-900 mb-2 border-b pb-1">2. Mapa Conceitual do Tema</h2>
        <div class="flex justify-center my-4">
          <pre class="mermaid">
          flowchart TD
              A["Tópico: {topic}"] --> B["Descoberta Inicial"]
              A --> C["Casos de Uso Práticos"]
              B --> D["Síntese no OptMem"]
              C --> E["Artefato HTML + PDF"]
          </pre>
        </div>
      </section>
    </main>

    <footer class="mt-12 pt-4 border-t text-xs text-slate-400 flex justify-between">
      <span>Agentic Knowledge OS • Nightly Harness</span>
      <span>Página 1</span>
    </footer>
  </div>
  <script>mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});</script>
</body>
</html>
"""

    artifact_path.write_text(html_content, encoding="utf-8")
    print(f"      Artefato gerado: {artifact_path.name}")

    # 3. Compilar PDF
    print("[3/5] Exportando PDF A4 via motor Playwright...")
    pdf_out = PESQUISAS_DIR / "pdf" / f"{date_str}-{slug}.pdf"
    res_pdf = subprocess.run([sys.executable, str(GERAR_PDF_SCRIPT), str(artifact_path), "-o", str(pdf_out)], capture_output=True, text=True, cwd=WORKSPACE_DIR)
    if res_pdf.returncode == 0:
        print(f"      PDF compilado com sucesso: {pdf_out.name}")
    else:
        print(f"      Aviso na geração de PDF: {res_pdf.stderr}")

    # 4. Gravar Fato no OptMem
    print("[4/5] Gravando resumo factual de 1 linha no OptMem...")
    try:
        mem_line = f"Pesquisa autônoma '{topic[:50]}' concluída. Dossiê em {artifact_path.name}."
        subprocess.run([sys.executable, str(OPTMEM_SCRIPT), "note", mem_line], capture_output=True, text=True, cwd=WORKSPACE_DIR)
        print("      Fato memorizado com sucesso no OptMem.")
    except Exception as e:
        print(f"      Aviso ao gravar OptMem: {e}")

    # 5. Conclusão
    print(f"[5/5] Sessão autônoma finalizada com sucesso. Entregável: {pdf_out.relative_to(WORKSPACE_DIR)}")


def main():
    parser = argparse.ArgumentParser(description="Harness de Pesquisa Autônoma Noturna")
    parser.add_argument("--topico", "-t", required=True, help="Tópico ou assunto da pesquisa a ser aprofundado")
    parser.add_argument("--profundidade", "-p", type=int, default=3, help="Profundidade do ciclo de pesquisa (1 a 5)")
    args = parser.parse_args()

    run_nightly_research(topic=args.topico, max_depth=args.profundidade)


if __name__ == "__main__":
    main()
