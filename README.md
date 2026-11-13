# Agentic Knowledge OS

> **The Professional AI-Augmented Second Brain & Knowledge Operating System.**  
> Built for autonomous pair programming with **Google Antigravity**, **Cursor**, and **Claude Code**, powered by an editorial A4 PDF publishing engine and 20 production-grade Agent Skills.

---

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Playwright-Chromium-green.svg" alt="Playwright" />
  <img src="https://img.shields.io/badge/HTML5-Tailwind%20CSS-blue.svg" alt="HTML5 Standalone" />
  <img src="https://img.shields.io/badge/Mermaid.js-Anti--Distortion-orange.svg" alt="Mermaid" />
  <img src="https://img.shields.io/badge/AI%20Agent-Antigravity%20%7C%20Cursor-black.svg" alt="AI Agent Ready" />
  <img src="https://img.shields.io/badge/License-MIT-brightgreen.svg" alt="License MIT" />
</p>

---

## O que e o Agentic Knowledge OS?

A maioria dos "Second Brains" em Markdown sofre de três problemas graves quando utilizados com agentes de IA:
1. **Proliferação de Arquivos Duplicados**: Agentes criam um arquivo novo a cada prompt, fragmentando o conhecimento.
2. **Diagramas Quebrados e Ilegíveis**: Modelos geram árvores horizontais gigantes que ficam ilegíveis ou quebram páginas ao exportar para PDF.
3. **Falta de Rigor de Engenharia**: Falta de rastreabilidade de tarefas, ausência de testes e alucinações sobre escopo.

O **Agentic Knowledge OS** resolve isso fornecendo um **Harness de Engenharia Completo**:
- **Diretrizes Mestre Anti-Alucinação (`AGENTS.md`)**: Regras inquebráveis de proporção de diagramas Mermaid, estilo profissional, preservação histórica de relatórios e blocos de código cirúrgicos (< 10 linhas).
- **Motor de PDF Editorial A4 (`scripts/gerar_pdf.py`)**: Converte arquivos `.html` e `.md` em PDFs corporativos com capa executiva, rodapés dinâmicos, paginação CSS Paged Media e algoritmos que eliminam quebras órfãs (`anti-orphan page break`).
- **Design System HTML5 Standalone**: Componentes visuais modernos com Tailwind CSS (`Timeline`, `Badge`, `Callout`, `LinkCard`, tabelas de parâmetros e cartões de status).
- **Memória Contínua Ultraleve (OptMem Pattern)**: Persistência episódica de longo prazo em ~426 tokens sem overhead de bancos vetoriais.
- **Hub de 20 Agent Skills**: Extensões operacionais modulares em `.agents/skills/` (arquitetura documental, auditoria de Design Systems, compilação de PDF, banco de dados DBX MCP, memórias e automações).

---

## Arquitetura do Sistema

```mermaid
flowchart TD
    subgraph INPUT["Camada de Entrada (Pair Programming)"]
        A["Engenheiro / Desenvolvedor"] <-->|"Prompts & Discussões"| B["Agente de IA<br/>(Antigravity / Cursor / Claude)"]
    end

    subgraph HARNESS["Governança & Disciplina (Harness)"]
        B <--> C["AGENTS.md<br/>Regras Mestre & Anti-Distorção"]
        B <--> D[".agents/skills/<br/>20 Habilidades Operacionais"]
        B <--> M["MEMORY.md<br/>OptMem Pattern (~426 tokens)"]
    end

    subgraph ENGINE["Motor de Compilação & Qualidade"]
        E["Artefatos HTML5 Standalone<br/>(Tailwind, Badges, Callouts)"]
        F["scripts/gerar_pdf.py<br/>Playwright Chromium Engine"]
        G["scripts/validar_links.py<br/>Auditor de Saúde & Links"]
    end

    subgraph OUTPUT["Entregáveis Corporativos"]
        H["PDFs A4 Editoriais<br/>(Capa, Sem Órfãos, Print Ready)"]
        I["ORGANIZATION.md<br/>Catálogo Vivo Auto-Regenerável"]
    end

    INPUT --> HARNESS
    HARNESS --> ENGINE
    ENGINE --> OUTPUT

    style A fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff
    style B fill:#0f172a,stroke:#8b5cf6,stroke-width:2px,color:#fff
    style C fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#fff
    style F fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#fff
    style H fill:#0f172a,stroke:#ec4899,stroke-width:2px,color:#fff
```

---

## Inicio Rapido (Quickstart)

### 1. Clonar o Repositorio
```bash
git clone https://github.com/SEU_USUARIO/agentic-knowledge-os.git
cd agentic-knowledge-os
```

### 2. Rodar a Inicializacao Automatica
```bash
python scripts/setup.py
```
*O script verificará o ambiente, instalará as dependências (`Playwright Chromium`, `requirements.txt`) e personalizará o seu `AGENTS.md`.*

### 3. Compilar seu Primeiro PDF Editorial
```bash
python scripts/gerar_pdf.py exemplos/01-ata-reuniao-arquitetura.html
```
*O PDF será compilado em segundos dentro de `exemplos/pdf/` com alta fidelidade visual A4.*

---

## Comandos do Repositorio (CLI)

| Comando | Descrição |
| :--- | :--- |
| `python scripts/gerar_pdf.py <arquivo.html>` | Compila um artefato `.html` ou nota `.md` individual em PDF corporativo. |
| `python scripts/gerar_pdf.py --dir <pasta>` | Compila em lote todos os documentos de uma pasta. |
| `python scripts/gerar_pdf.py <arquivo.html> --check-only` | Linter rápido: valida regras de diagramas, tags e quebras sem renderizar. |
| `python scripts/validar_frontmatter.py` | Garante que todas as notas possuem metadados válidos. |
| `python scripts/validar_links.py` | Detecta links quebrados ou hiperlinks órfãos em todo o repositório. |
| `python scripts/gerar_organization.py` | Atualiza a matriz de categorias e links rápidos do `ORGANIZATION.md`. |

---

## Componentes Visuais HTML5 Inclusos

O motor renderiza nativamente componentes corporativos modernos direto no PDF e no navegador:
- Linha do tempo visual (`Timeline`) com datas, badges de status e conectores verticais.
- Cards informativos corporativos (`Callouts` de informação, aviso, sucesso e alerta).
- Tags coloridas semânticas (`Badges` de trabalho, projeto, status e contexto).
- Cards de navegação entre documentos (`LinkCards`).
- Diagramas **Mermaid.js** com renderização SVG vetorial em alta resolução e proteção anti-distorção tipográfica.

---

## Hub de Agent Skills Homologadas

Localizadas em `.agents/skills/`, prontas para agentes autônomos invocarem sob demanda:
1. `pdf-generator`: Validação e compilação de documentos HTML5 e Markdown em PDFs A4.
2. `second-brain-doctor`: Auditoria de saúde, validação de frontmatter e auto-catálogo.
3. `anti-rationalization`: Portões de disciplina e tabelas anti-racionalização para IAs.
4. `meeting-to-knowledge`: Transformação de gravações e atas brutas em documentos executivos.
5. `clickup-task-flow`: Orquestração de tarefas, escopo imutável e dossiês de homologação.
6. `optmem-pattern`: Padrão de memória episódica persistente ultracompacta (~426 tokens).
7. `designsys-audit`: Extração de design tokens W3C e auditoria de CSS via `designsys`.
8. `playwright-cli`: Navegação headless e testes E2E com alta economia de tokens.
9. `dbx-mcp`: Conexão universal com 100+ bancos de dados via Model Context Protocol.
10. `hyperframes`: Produção de vídeos programáticos determinísticos em HTML/CSS/GSAP.
11. `document-architect`: Arquiteto da Informação e Designer de Documentos HTML5 corporativos.
12. `weekly-report-generator`: Consolidação e geração automática de Status Reports Executivos.

---

## Como Usar para Seu Portfolio e Manter Anotacoes Privadas

Este repositório foi arquitetado especificamente para permitir que você:
1. Mantenha **este repositório público no GitHub** como uma vitrine do seu nível de maturidade em Engenharia de Software, Agentes de IA e Automação de Documentação.
2. Mantenha seu **repositório pessoal de anotações privado**, configurando este repositório público como `upstream`:
   ```bash
   git remote add upstream https://github.com/SEU_USUARIO/agentic-knowledge-os.git
   ```
   Toda melhoria de motor de PDF ou nova skill que você criar pode ser sincronizada entre ambos via git sem vazar nenhum dado de cliente.

---

## Licenca

Distribuído sob a licença **MIT**. Sinta-se livre para utilizar, customizar e estender para seus próprios projetos e clientes.
