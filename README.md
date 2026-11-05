# ðŸ§  Agentic Knowledge OS

> **The Professional AI-Augmented Second Brain & Knowledge Operating System.**  
> Built for autonomous pair programming with **Google Antigravity**, **Cursor**, and **Claude Code**, powered by an editorial A4 PDF publishing engine and 10 production-grade Agent Skills.

---

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Playwright-Chromium-green.svg" alt="Playwright" />
  <img src="https://img.shields.io/badge/MDX-React%20Components-purple.svg" alt="MDX" />
  <img src="https://img.shields.io/badge/Mermaid.js-Anti--Distortion-orange.svg" alt="Mermaid" />
  <img src="https://img.shields.io/badge/AI%20Agent-Antigravity%20%7C%20Cursor-black.svg" alt="AI Agent Ready" />
  <img src="https://img.shields.io/badge/License-MIT-brightgreen.svg" alt="License MIT" />
</p>

---

## ðŸŒŸ O que Ã© o Agentic Knowledge OS?

A maioria dos "Second Brains" em Markdown sofre de trÃªs problemas graves quando utilizados com agentes de IA:
1. **ProliferaÃ§Ã£o de Arquivos Duplicados**: Agentes criam um arquivo novo a cada prompt, fragmentando o conhecimento.
2. **Diagramas Quebrados & IlegÃ­veis**: Modelos geram Ã¡rvores horizontais gigantes que ficam ilegÃ­veis ou quebram pÃ¡ginas ao exportar para PDF.
3. **Falta de Rigor de Engenharia**: Falta de rastreabilidade de tarefas, ausÃªncia de testes e alucinaÃ§Ãµes sobre escopo.

O **Agentic Knowledge OS** resolve isso fornecendo um **Harness de Engenharia Completo**:
- ðŸ“ **Diretrizes Mestre Anti-AlucinaÃ§Ã£o (`AGENTS.md`)**: Regras inquebrÃ¡veis de proporÃ§Ã£o de diagramas Mermaid, estilo profissional, preservaÃ§Ã£o histÃ³rica de relatÃ³rios e blocos de cÃ³digo cirÃºrgicos (< 10 linhas).
- ðŸ“‘ **Motor de PDF Editorial A4 (`scripts/gerar_pdf.py`)**: Converte arquivos `.mdx` em PDFs corporativos com capa executiva, rodapÃ©s dinÃ¢micos, paginaÃ§Ã£o CSS Paged Media e algoritmos que eliminam quebras Ã³rfÃ£s (`anti-orphan page break`).
- ðŸ§© **Design System MDX**: Componentes React reutilizÃ¡veis (`<Timeline />`, `<Badge />`, `<Callout />`, `<LinkCard />`, `<ClickUpCard />`).
- ðŸ§  **MemÃ³ria ContÃ­nua Ultraleve (OptMem Pattern)**: PersistÃªncia episÃ³dica de longo prazo em ~426 tokens sem overhead de bancos vetoriais.
- ðŸ§° **Hub de 10 Agent Skills**: ExtensÃµes operacionais modulares em `.agents/skills/` (TDD, auditoria de Design Systems, crawling Apify, banco de dados DBX MCP).

---

## ðŸ›ï¸ Arquitetura do Sistema

```mermaid
flowchart TD
    subgraph INPUT["Camada de Entrada (Pair Programming)"]
        A["Engenheiro / Desenvolvedor"] <-->|"Prompts & DiscussÃµes"| B["Agente de IA<br/>(Antigravity / Cursor / Claude)"]
    end

    subgraph HARNESS["GovernanÃ§a & Disciplina (Harness)"]
        B <--> C["AGENTS.md<br/>Regras Mestre & Anti-DistorÃ§Ã£o"]
        B <--> D[".agents/skills/<br/>10 Habilidades Operacionais"]
        B <--> M["MEMORY.md<br/>OptMem Pattern (~426 tokens)"]
    end

    subgraph ENGINE["Motor de CompilaÃ§Ã£o & Qualidade"]
        E["Arquivos MDX Ricos<br/>(Timeline, Badge, Callout)"]
        F["scripts/gerar_pdf.py<br/>Playwright Chromium Engine"]
        G["scripts/validar_links.py<br/>Auditor de SaÃºde & Links"]
    end

    subgraph OUTPUT["EntregÃ¡veis Corporativos"]
        H["PDFs A4 Editoriais<br/>(Capa, Sem Ã“rfÃ£os, Print Ready)"]
        I["ORGANIZATION.md<br/>CatÃ¡logo Vivo Auto-RegenerÃ¡vel"]
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

## ðŸš€ InÃ­cio RÃ¡pido (Quickstart)

### 1. Clonar o RepositÃ³rio
```bash
git clone https://github.com/SEU_USUARIO/agentic-knowledge-os.git
cd agentic-knowledge-os
```

### 2. Rodar a InicializaÃ§Ã£o AutomÃ¡tica
```bash
python scripts/setup.py
```
*O script verificarÃ¡ o ambiente, instalarÃ¡ as dependÃªncias (`Playwright Chromium`, `requirements.txt`) e personalizarÃ¡ o seu `AGENTS.md`.*

### 3. Compilar seu Primeiro PDF Editorial
```bash
python scripts/gerar_pdf.py exemplos/01-ata-reuniao-arquitetura.mdx
```
*O PDF serÃ¡ compilado em segundos dentro de `exemplos/pdf/` com alta fidelidade visual A4.*

---

## ðŸ“‹ Comandos do RepositÃ³rio (CLI)

| Comando | DescriÃ§Ã£o |
| :--- | :--- |
| `python scripts/gerar_pdf.py <arquivo.mdx>` | Compila um arquivo `.mdx` individual em PDF corporativo. |
| `python scripts/gerar_pdf.py --dir <pasta>` | Compila em lote todos os arquivos `.mdx` de uma pasta. |
| `python scripts/gerar_pdf.py <arquivo.mdx> --check-only` | Linter rÃ¡pido: valida regras de diagramas, moedas e quebras sem renderizar. |
| `python scripts/validar_frontmatter.py` | Garante que todas as notas possuem metadados vÃ¡lidos. |
| `python scripts/validar_links.py` | Detecta links quebrados ou hiperlinks Ã³rfÃ£os em todo o repositÃ³rio. |
| `python scripts/gerar_organization.py` | Atualiza a matriz de categorias e links rÃ¡pidos do `ORGANIZATION.md`. |

---

## ðŸ§© Componentes Visuais MDX Inclusos

O motor renderiza nativamente componentes modernos direto no PDF e no navegador:
- `<Timeline items={[...]} />`: Linha do tempo visual com datas, badges de status e conectores verticais.
- `<Callout title="..." type="info|warning|success|danger">`: Cards informativos corporativos.
- `<Badge label="..." type="trabalho|projeto|ideia" />`: Tags coloridas semÃ¢nticas.
- `<LinkCard title="..." href="..." />`: Cards de navegaÃ§Ã£o entre documentos.
- Diagramas **Mermaid.js** com renderizaÃ§Ã£o SVG em alta resoluÃ§Ã£o (300 DPI) e proteÃ§Ã£o anti-distorÃ§Ã£o tipogrÃ¡fica.

---

## ðŸ› ï¸ Hub de 10 Agent Skills Homologadas

Localizadas em `.agents/skills/`, prontas para agentes autÃ´nomos invocarem sob demanda:
1. `pdf-generator`: ValidaÃ§Ã£o e compilaÃ§Ã£o de documentos MDX em PDFs A4.
2. `second-brain-doctor`: Auditoria de saÃºde, validaÃ§Ã£o de frontmatter e auto-catÃ¡logo.
3. `anti-rationalization`: PortÃµes de disciplina e tabelas anti-racionalizaÃ§Ã£o para IAs.
4. `meeting-to-knowledge`: TransformaÃ§Ã£o de gravaÃ§Ãµes e atas brutas em documentos executivos.
5. `clickup-task-flow`: OrquestraÃ§Ã£o de tarefas, escopo imutÃ¡vel e dossiÃªs de homologaÃ§Ã£o.
6. `optmem-pattern`: PadrÃ£o de memÃ³ria episÃ³dica persistente ultracompacta (~426 tokens).
7. `designsys-audit`: ExtraÃ§Ã£o de design tokens W3C e auditoria de CSS via `designsys`.
8. `playwright-cli`: NavegaÃ§Ã£o headless e testes E2E com alta economia de tokens.
9. `dbx-mcp`: ConexÃ£o universal com 100+ bancos de dados via Model Context Protocol.
10. `hyperframes`: ProduÃ§Ã£o de vÃ­deos programÃ¡ticos determinÃ­sticos em HTML/CSS/GSAP.

---

## ðŸ”’ Como Usar para Seu PortfÃ³lio & Manter AnotaÃ§Ãµes Privadas

Este repositÃ³rio foi arquitetado especificamente para permitir que vocÃª:
1. Mantenha **este repositÃ³rio pÃºblico no GitHub** como uma vitrine do seu nÃ­vel de maturidade em Engenharia de Software, Agentes de IA e AutomaÃ§Ã£o de DocumentaÃ§Ã£o.
2. Mantenha seu **repositÃ³rio pessoal de anotaÃ§Ãµes privado**, configurando este repositÃ³rio pÃºblico como `upstream`:
   ```bash
   git remote add upstream https://github.com/SEU_USUARIO/agentic-knowledge-os.git
   ```
   Toda melhoria de motor de PDF ou nova skill que vocÃª criar pode ser sincronizada entre ambos via git sem vazar nenhum dado de cliente!

---

## ðŸ“„ LicenÃ§a

DistribuÃ­do sob a licenÃ§a **MIT**. Sinta-se livre para utilizar, customizar e estender para seus prÃ³prios projetos e clientes.
