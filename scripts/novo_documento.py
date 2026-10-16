#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/novo_documento.py — Gerador Paramétrico de Documentos HTML5 para o Agentic Knowledge OS

Gera esqueletos de novos artefatos HTML5 rigorosamente alinhados com o Design System oficial
(templates/artefato_documento.html). Elimina desvios de layout, fundos cinzas e tags fora de conformidade.

Uso:
    python scripts/novo_documento.py --titulo "Nome do Documento" --arquivo "projetos/meu-doc.html" [OPÇÕES]
    python scripts/novo_documento.py -t "Plano de Migração" -o "projetos/migracao.html" --preset plano-acao
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Garantir UTF-8 no stdout/stderr no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT_DIR / "templates" / "artefato_documento.html"

# Mapa de estilos para Status Badges
STATUS_MAP = {
    "ATIVO": {
        "text": "ATIVO",
        "class": "bg-emerald-50 text-emerald-700 border border-emerald-200"
    },
    "PLANEJAMENTO": {
        "text": "PLANEJAMENTO",
        "class": "bg-sky-50 text-sky-700 border border-sky-200"
    },
    "EM PROGRESSO": {
        "text": "EM PROGRESSO",
        "class": "bg-amber-50 text-amber-700 border border-amber-200"
    },
    "CONCLUIDO": {
        "text": "CONCLUÍDO",
        "class": "bg-indigo-50 text-indigo-700 border border-indigo-200"
    },
    "HOMOLOGADO": {
        "text": "HOMOLOGADO",
        "class": "bg-emerald-50 text-emerald-700 border border-emerald-200"
    },
    "ARQUIVADO": {
        "text": "ARQUIVADO",
        "class": "bg-slate-100 text-slate-700 border border-slate-300"
    }
}

# Paleta cíclica para tags
TAG_PALETTES = [
    "bg-blue-50 text-blue-700 border border-blue-200/80",
    "bg-purple-50 text-purple-700 border border-purple-200/80",
    "bg-emerald-50 text-emerald-700 border border-emerald-200/80",
    "bg-amber-50 text-amber-700 border border-amber-200/80",
    "bg-rose-50 text-rose-700 border border-rose-200/80",
    "bg-sky-50 text-sky-700 border border-sky-200/80",
]


def render_tags(tags_list):
    """Renderiza a sequência de badges de tags no topo do main."""
    if not tags_list:
        return ""
    
    html = ['<div class="flex flex-wrap gap-2 my-3">']
    for idx, tag in enumerate(tags_list):
        tag_str = tag.strip()
        if not tag_str:
            continue
        palette = TAG_PALETTES[idx % len(TAG_PALETTES)]
        html.append(f'  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {palette}">{tag_str}</span>')
    html.append('</div>')
    return "\n".join(html)


def build_bloco_resumo(titulo="1. Visão Geral e Objetivo"):
    return f"""      <!-- Seção 1: Resumo Executivo -->
      <section class="mb-10">
        <h2>{titulo}</h2>
        <p>
          Descreva aqui a contextualização geral, problema de negócio e a proposta de valor central desta iniciativa.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
          <div class="card border-l-4 border-l-sky-500">
            <h4 class="font-bold text-slate-900">Objetivo Central</h4>
            <p class="text-xs text-slate-600 mt-1">
              Síntese do que se pretende alcançar com este projeto ou especificação técnica.
            </p>
          </div>
          <div class="card border-l-4 border-l-indigo-500">
            <h4 class="font-bold text-slate-900">Pilar Tecnológico</h4>
            <p class="text-xs text-slate-600 mt-1">
              Arquitetura, linguagens e ferramentas fundamentais adotadas no escopo.
            </p>
          </div>
          <div class="card border-l-4 border-l-emerald-500">
            <h4 class="font-bold text-slate-900">Resultado Esperado</h4>
            <p class="text-xs text-slate-600 mt-1">
              Entregáveis tangíveis e benefícios diretos para a operação ou negócio.
            </p>
          </div>
        </div>
      </section>"""


def build_bloco_arquitetura(titulo="2. Arquitetura e Fluxo do Sistema"):
    return f"""      <!-- Seção 2: Arquitetura & Fluxo -->
      <section class="mb-10">
        <h2>{titulo}</h2>
        <p>
          Visão holística dos componentes de software, microsserviços, fluxos de dados e integrações externas.
        </p>

        <div class="mermaid-wrapper">
          <div class="mermaid">
flowchart LR
  A["Entrada de Dados<br/>(Gatilho / Requisição)"] -->|"Payload JSON"| B["Processamento Central<br/>(Regras de Negócio)"]
  B -->|"Dados Estruturados"| C["Persistência / API<br/>(Banco de Dados)"]
  C -->|"Status / Notificação"| D["Entrega Final<br/>(Usuário / Dashboard)"]
          </div>
        </div>
      </section>"""


def build_bloco_tabela(titulo="3. Parâmetros e Especificações Técnicas"):
    return f"""      <!-- Seção: Tabela Corporativa -->
      <section class="mb-10">
        <h2>{titulo}</h2>
        <p>
          Tabela detalhada com parâmetros de configuração, endpoints ou especificações operacionais:
        </p>

        <table>
          <thead>
            <tr>
              <th>Parâmetro / Componente</th>
              <th>Tipo / Stack</th>
              <th>Valor / Configuração</th>
              <th>Descrição & Regra de Negócio</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-semibold text-slate-900">ENDPOINT_API</td>
              <td><code>string (URL)</code></td>
              <td><code>https://api.exemplo.com/v1</code></td>
              <td>Rota primária para ingestão e consulta de dados assíncronos.</td>
            </tr>
            <tr>
              <td class="font-semibold text-slate-900">TIMEOUT_SEGUNDOS</td>
              <td><code>integer</code></td>
              <td><code>30</code></td>
              <td>Tempo limite de tolerância para requisições externas antes de abortar.</td>
            </tr>
            <tr>
              <td class="font-semibold text-slate-900">RETRY_MAX</td>
              <td><code>integer</code></td>
              <td><code>3</code></td>
              <td>Quantidade máxima de retentativas automáticas com backoff exponencial.</td>
            </tr>
          </tbody>
        </table>
      </section>"""


def build_bloco_callout(tipo="info", titulo="Nota de Governança", texto="Instrução crítica de implementação ou diretriz mandatória."):
    classes = {
        "info": "callout-info",
        "warn": "callout-warn",
        "danger": "callout-danger",
        "success": "callout-success"
    }
    cls = classes.get(tipo.lower(), "callout-info")
    return f"""      <div class="callout {cls}">
        <strong>{titulo}:</strong> {texto}
      </div>"""


def build_bloco_timeline(titulo="Linha do Tempo de Evolução do Documento", data_hoje=None):
    if not data_hoje:
        data_hoje = datetime.now().strftime("%d/%m/%Y")
    else:
        # Converter se vier no formato YYYY-MM-DD
        try:
            d = datetime.strptime(data_hoje, "%Y-%m-%d")
            data_hoje = d.strftime("%d/%m/%Y")
        except ValueError:
            pass

    return f"""      <!-- Seção: Linha do Tempo -->
      <section class="mb-10">
        <h2>{titulo}</h2>
        <div class="timeline">
          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-bold text-slate-900 text-sm">{data_hoje}</span>
              <span class="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Criação Inicial</span>
            </div>
            <p class="text-xs text-slate-600">
              Concepção e estruturação inicial do documento gerado via CLI padronizada (scripts/novo_documento.py).
            </p>
          </div>
        </div>
      </section>"""


def build_bloco_relacionados(titulo="Assuntos Relacionados & Links Cruzados"):
    return f"""      <!-- Seção: Assuntos Relacionados -->
      <section class="mb-6">
        <h2>{titulo}</h2>
        <ul class="text-sm">
          <li><a href="../../00-meta/TEMPLATE_NOTA.html">Template Oficial de Notas (HTML5)</a> — Especificação do Design System do Knowledge OS.</li>
          <li><a href="../../ORGANIZATION.md">Catálogo Mestre de Organização</a> — Índice geral de tópicos e pastas.</li>
        </ul>
      </section>"""


def build_preset_plano_acao(data_hoje):
    partes = [
        build_bloco_resumo("1. Visão Geral e Objetivos do Plano"),
        build_bloco_arquitetura("2. Arquitetura e Topologia do Sistema"),
        f"""      <!-- Seção 3: Roteiro e Fases de Implementação -->
      <section class="mb-10">
        <h2>3. Plano de Ação em Fases de Execução</h2>
        <p>
          Detalhamento cronológico das entregas e marcos críticos:
        </p>

        <div class="timeline mt-6">
          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-bold text-slate-900 text-base">Fase 1: Preparação e Fundação</span>
              <span class="px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800">Setup</span>
            </div>
            <p class="text-sm text-slate-600 mb-2">
              Configuração inicial do ambiente, dependências e criação de contratos.
            </p>
            <ul class="text-sm custom-list">
              <li><span class="task-checkbox unchecked">&#9634;</span> Configurar repositório e variáveis de ambiente locais.</li>
              <li><span class="task-checkbox unchecked">&#9634;</span> Implementar prova de conceito (PoC) dos módulos críticos.</li>
            </ul>
          </div>

          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-bold text-slate-900 text-base">Fase 2: Desenvolvimento Central</span>
              <span class="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">Engenharia</span>
            </div>
            <p class="text-sm text-slate-600 mb-2">
              Implementação da lógica de negócio e integração de APIs.
            </p>
            <ul class="text-sm custom-list">
              <li><span class="task-checkbox unchecked">&#9634;</span> Desenvolver rotinas de automação e regras de transformação.</li>
              <li><span class="task-checkbox unchecked">&#9634;</span> Conectar persistência e tratamento de exceções com retentativas.</li>
            </ul>
          </div>

          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-bold text-slate-900 text-base">Fase 3: Homologação e Deploy</span>
              <span class="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Operação</span>
            </div>
            <p class="text-sm text-slate-600 mb-2">
              Bateria de testes fim a fim e publicação em ambiente produtivo.
            </p>
            <ul class="text-sm custom-list">
              <li><span class="task-checkbox unchecked">&#9634;</span> Validar estabilidade e ausência de regressões operacionais.</li>
              <li><span class="task-checkbox unchecked">&#9634;</span> Publicar em produção e documentar instruções de sustentação.</li>
            </ul>
          </div>
        </div>
      </section>""",
        build_bloco_tabela("4. Stack Tecnológica e Parâmetros"),
        build_bloco_timeline("5. Linha do Tempo de Evolução do Documento", data_hoje),
        build_bloco_relacionados("6. Assuntos Relacionados & Links Cruzados")
    ]
    return "\n\n".join(partes)


def build_preset_nota_tecnica(data_hoje):
    partes = [
        build_bloco_resumo("1. Visão Geral e Contexto Técnico"),
        build_bloco_arquitetura("2. Modelagem Conceitual"),
        f"""      <!-- Seção 3: Implementação e Snippets Cirúrgicos -->
      <section class="mb-10">
        <h2>3. Detalhamento de Implementação</h2>
        <p>
          Abaixo estão os blocos essenciais de código e regras de negócio:
        </p>

        <pre class="bg-slate-900 text-slate-100 p-3.5 rounded text-xs overflow-x-auto"><code># Exemplo cirúrgico de implementação
def executar_rotina(payload: dict) -> bool:
    \"\"\"Processa o payload com validação estrita.\"\"\"
    if not payload.get("id"):
        raise ValueError("ID obrigatório")
    return True</code></pre>

        {build_bloco_callout("info", "Padrão de Snippet", "Mantenha snippets cirúrgicos com menos de 15 linhas, focando na regra de negócio e evitando repetições desnecessárias.")}
      </section>""",
        build_bloco_timeline("4. Linha do Tempo de Evolução do Documento", data_hoje),
        build_bloco_relacionados("5. Assuntos Relacionados & Links Cruzados")
    ]
    return "\n\n".join(partes)


def build_preset_relatorio_executivo(data_hoje):
    partes = [
        f"""      <!-- Seção 1: Sumário Executivo & KPIs -->
      <section class="mb-10">
        <h2>1. Sumário Executivo & Indicadores-Chave (KPIs)</h2>
        <p>
          Relatório consolidado de resultados operacionais, entregas do período e status dos projetos estratégicos:
        </p>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 my-6">
          <div class="card text-center">
            <span class="text-xs uppercase font-bold text-slate-400">Total de Entregas</span>
            <div class="text-2xl font-extrabold text-slate-900 mt-1">12</div>
            <span class="text-[10px] text-emerald-600 font-semibold">&uarr; 100% no prazo</span>
          </div>
          <div class="card text-center">
            <span class="text-xs uppercase font-bold text-slate-400">SLA Médio</span>
            <div class="text-2xl font-extrabold text-slate-900 mt-1">99.8%</div>
            <span class="text-[10px] text-slate-500 font-medium">Meta: &gt; 99.0%</span>
          </div>
          <div class="card text-center">
            <span class="text-xs uppercase font-bold text-slate-400">Bloqueios Críticos</span>
            <div class="text-2xl font-extrabold text-emerald-600 mt-1">0</div>
            <span class="text-[10px] text-emerald-600 font-semibold">Sem pendências</span>
          </div>
          <div class="card text-center">
            <span class="text-xs uppercase font-bold text-slate-400">Economia Gerada</span>
            <div class="text-2xl font-extrabold text-indigo-600 mt-1">R$ 14,5k</div>
            <span class="text-[10px] text-indigo-600 font-semibold">No ciclo atual</span>
          </div>
        </div>
      </section>""",
        build_bloco_tabela("2. Detalhamento de Ações e Entregáveis"),
        build_bloco_timeline("3. Linha do Tempo e Marcos do Ciclo", data_hoje),
        build_bloco_relacionados("4. Assuntos Relacionados & Links Cruzados")
    ]
    return "\n\n".join(partes)


def build_preset_tarefa(data_hoje):
    partes = [
        f"""      <!-- Seção 1: Escopo Inicial Imutável -->
      <section class="mb-10">
        <h2>1. Escopo Inicial Imutável (Baseline Acordado)</h2>
        <p>
          Este escopo define as fronteiras acordadas inicialmente no kickoff da demanda e nunca deve ser alterado:
        </p>
        <ul class="text-sm">
          <li><strong>Demanda Principal:</strong> Implementação do requisito especificado no card de Produto.</li>
          <li><strong>Critérios de Aceite:</strong> Cobertura de testes automatizados, ausência de regressões e validação em homologação.</li>
          <li><strong>Fora de Escopo:</strong> Refatorações em serviços periféricos que não impactem a entrega direta.</li>
        </ul>
      </section>""",
        f"""      <!-- Seção 2: Aditivos de Escopo -->
      <section class="mb-10">
        <h2>2. Aditivos de Escopo e Novos Requisitos</h2>
        <p>
          Modificações solicitadas pelo cliente ou PO durante a execução técnica:
        </p>
        <div class="card border-l-4 border-l-amber-500">
          <h4 class="font-bold text-slate-900">Aditivo #1: Ajuste de Validação</h4>
          <p class="text-xs text-slate-600 mt-1">
            Necessidade de tratamento adicional identificado durante os testes de carga.
          </p>
        </div>
      </section>""",
        f"""      <!-- Seção 3: Checklist de Homologação -->
      <section class="mb-10">
        <h2>3. Checklist de Homologação & DoD</h2>
        <ul class="text-sm custom-list">
          <li><span class="task-checkbox unchecked">&#9634;</span> Código escrito, revisado e aderente ao guia de estilo.</li>
          <li><span class="task-checkbox unchecked">&#9634;</span> Testes unitários e de integração executados com 100% de sucesso.</li>
          <li><span class="task-checkbox unchecked">&#9634;</span> Documentação atualizada e PDF compilado via <code>scripts/gerar_pdf.py</code>.</li>
        </ul>
      </section>""",
        build_bloco_timeline("4. Linha do Tempo da Tarefa", data_hoje),
        build_bloco_relacionados("5. Assuntos Relacionados & Links Cruzados")
    ]
    return "\n\n".join(partes)


def gerar_documento(args):
    """Gera o arquivo HTML a partir do template e dos argumentos."""
    if not TEMPLATE_PATH.exists():
        print(f"❌ Erro fatal: Template base não encontrado em: {TEMPLATE_PATH}")
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Resolver dados do cabeçalho
    data_hoje_iso = args.data if args.data else datetime.now().strftime("%Y-%m-%d")
    status_key = args.status.upper().strip()
    status_info = STATUS_MAP.get(status_key, STATUS_MAP["ATIVO"])

    # Processar Tags
    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    tags_html = render_tags(tags_list)

    # Construir Conteúdo Principal
    blocos_conteudo = []
    if tags_html:
        blocos_conteudo.append(tags_html)

    # Preset selecionado
    if args.preset == "plano-acao":
        blocos_conteudo.append(build_preset_plano_acao(data_hoje_iso))
    elif args.preset == "nota-tecnica":
        blocos_conteudo.append(build_preset_nota_tecnica(data_hoje_iso))
    elif args.preset == "relatorio-executivo":
        blocos_conteudo.append(build_preset_relatorio_executivo(data_hoje_iso))
    elif args.preset == "tarefa":
        blocos_conteudo.append(build_preset_tarefa(data_hoje_iso))
    else:
        # Modo modular via flags individuais
        if args.com_resumo:
            blocos_conteudo.append(build_bloco_resumo())
        if args.com_arquitetura:
            blocos_conteudo.append(build_bloco_arquitetura())
        if args.com_tabela:
            blocos_conteudo.append(build_bloco_tabela())
        if args.com_callout:
            blocos_conteudo.append(build_bloco_callout(tipo=args.com_callout))
        if args.com_timeline or not (args.com_resumo or args.com_arquitetura):
            blocos_conteudo.append(build_bloco_timeline(data_hoje=data_hoje_iso))
        if args.com_relacionados or not (args.com_resumo or args.com_arquitetura):
            blocos_conteudo.append(build_bloco_relacionados())

    content_str = "\n\n".join(blocos_conteudo)

    # Substituição de Placeholders Oficiais
    doc = template_content
    doc = doc.replace("{{TITLE}}", args.titulo)
    doc = doc.replace("{{CATEGORY_DISPLAY}}", args.categoria)
    doc = doc.replace("{{STATUS}}", status_info["text"])
    doc = doc.replace("{{STATUS_BADGE_CLASS}}", status_info["class"])
    doc = doc.replace("{{UPDATED_AT}}", data_hoje_iso)
    doc = doc.replace("{{AUTHOR}}", args.autor)
    doc = doc.replace("{{CLIENT}}", args.contexto)
    doc = doc.replace("{{VERSION}}", args.versao)
    doc = doc.replace("{{CONTENT}}", content_str)

    # Tratar caminho de saída
    out_path = Path(args.arquivo)
    if not out_path.is_absolute():
        out_path = ROOT_DIR / out_path

    # Criar diretórios pais se não existirem
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not args.force:
        print(f"⚠️  Aviso: O arquivo já existe em: {out_path}")
        print("    Para sobrescrever, use a flag --force.")
        sys.exit(1)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)

    rel_path = out_path.relative_to(ROOT_DIR) if out_path.is_relative_to(ROOT_DIR) else out_path
    print("=" * 70)
    print("[SUCESSO] Artefato HTML5 gerado conforme o Design System!")
    print(f"  - Arquivo: {rel_path}")
    print(f"  - Titulo:  {args.titulo}")
    print(f"  - Tags:    {', '.join(tags_list) if tags_list else 'Nenhuma'}")
    print(f"  - Preset:  {args.preset or 'Modular'}")
    print("=" * 70)
    print("Dicas de continuidade:")
    print("  1. Edite as secoes tecnicas dentro da tag <main>.")
    print("  2. Valide e gere o PDF com o motor oficial:")
    print(f'     python scripts/gerar_pdf.py "{rel_path}"')
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Gerador Paramétrico de Documentos HTML5 para o Agentic Knowledge OS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemplos:
  python scripts/novo_documento.py -t "Plano de Migração Cloud" -o "projetos/migracao.html" --preset plano-acao
  python scripts/novo_documento.py -t "TASK-006: Pipeline CI/CD" -o "trabalho/join4/tarefas/task-006.html" --preset tarefa
  python scripts/novo_documento.py -t "Nota de Arquitetura" -o "projetos/nota.html" --com-resumo --com-arquitetura
        """
    )

    # Parâmetros Obrigatórios e Metadados
    parser.add_argument("--titulo", "-t", required=True, help="Título oficial do documento")
    parser.add_argument("--arquivo", "-o", required=True, help="Caminho do arquivo de saída (.html)")
    parser.add_argument("--categoria", "-c", default="Projetos • Automação & IA", help="Categoria no cabeçalho")
    parser.add_argument("--status", "-s", default="ATIVO", help="Status: ATIVO, PLANEJAMENTO, CONCLUIDO, ARQUIVADO")
    parser.add_argument("--autor", "-a", default="Victor Rubinec", help="Autor / Responsável pelo documento")
    parser.add_argument("--contexto", "-k", default="Knowledge OS", help="Cliente ou Contexto da demanda")
    parser.add_argument("--versao", "-v", default="v1.0", help="Versão semântica (default: v1.0)")
    parser.add_argument("--data", "-d", help="Data no formato YYYY-MM-DD (default: data de hoje)")
    parser.add_argument("--tags", help="Tags separadas por vírgula (ex: 'Python,IA,Telegram')")

    # Presets Estruturais
    parser.add_argument("--preset", choices=["plano-acao", "nota-tecnica", "relatorio-executivo", "tarefa"],
                        help="Estrutura completa pré-configurada de seções")

    # Injetores Modulares de Blocos Semânticos
    parser.add_argument("--com-resumo", action="store_true", help="Inclui Seção 1 com 3 cards de destaque")
    parser.add_argument("--com-arquitetura", action="store_true", help="Inclui Seção com diagrama Mermaid")
    parser.add_argument("--com-tabela", action="store_true", help="Inclui tabela corporativa zebrada")
    parser.add_argument("--com-callout", choices=["info", "warn", "danger", "success"], help="Inclui bloco de callout")
    parser.add_argument("--com-timeline", action="store_true", help="Inclui Seção de Linha do Tempo")
    parser.add_argument("--com-relacionados", action="store_true", help="Inclui Seção de Assuntos Relacionados")

    # Controle
    parser.add_argument("--force", "-f", action="store_true", help="Sobrescrever arquivo se já existir")

    args = parser.parse_args()
    gerar_documento(args)


if __name__ == "__main__":
    main()
