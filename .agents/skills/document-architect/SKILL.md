---
name: document-architect
description: Arquiteto da Informação e Designer de Documentos HTML5 corporativos do Knowledge OS. Use sempre que for criar, redigir, diagramar, reestruturar ou validar novos artefatos HTML5 de documentação técnica, planos de ação, manuais ou relatórios executivos.
---

# Skill: Document Architect (Arquitetura & Design de Documentos HTML5)

Esta skill orienta os agentes de IA a conceberem, estruturarem e diagramarem documentos técnicos e relatórios executivos em **HTML5 Standalone** rigorosamente alinhados ao Design System oficial do **Agentic Knowledge OS**.

---

## 1. Regra de Ouro Inegociável (Proibição de Scaffolding Manual)

- **REGRA SUPREMA**: É estritamente **PROIBIDO escrever a casca externa do HTML do zero** (tags `<html>`, `<head>`, CSS, scripts CDN e `<body>`) via comandos diretos ou `write_to_file`.
- Todo e qualquer novo documento HTML DEVE ser inicializado através da CLI oficial de scaffolding:
  ```bash
  python scripts/novo_documento.py \
    --titulo "Título Oficial do Documento" \
    --arquivo "caminho/do/arquivo.html" \
    --preset plano-acao|nota-tecnica|relatorio-executivo|tarefa \
    --tags "Tag1,Tag2,Tag3"
  ```
- **Fluxo de Trabalho Obrigatório**:
  1. Executar `python scripts/novo_documento.py` para gerar a estrutura base 100% blindada e conforme.
  2. Editar o conteúdo técnico estritamente dentro da tag `<main>` utilizando a ferramenta `replace_file_content`.
  3. Validar a conformidade de DOM e compilar o PDF corporativo:
     ```bash
     python scripts/gerar_pdf.py "caminho/do/arquivo.html"
     ```

---

## 2. Anatomia Canônica do Design System

Todos os documentos no Knowledge OS seguem o princípio de **página contínua fluida corporativa** (formato editorial impresso A4), e **NUNCA** o formato de dashboard ou card flutuante.

| Elemento | Regra Estrita de Conformidade | Padrão Proibido (Anti-Pattern) |
| :--- | :--- | :--- |
| **Fundo da Página (`<body>`)** | `bg-white text-slate-800 antialiased` | `bg-slate-50`, `bg-gray-*` ou fundos escuros. |
| **Container Raiz** | `.document-container max-w-4xl mx-auto px-6 py-8 sm:px-12 sm:py-12` | Caixas com `border`, `rounded-xl` ou `shadow-*` envolvendo a página. |
| **Cabeçalho Corporativo** | `.header-cover` com bolinha azul `bg-brand-500` e badge de status. | Cabeçalhos sem hierarquia ou pílulas soltas. |
| **Grade de Metadados** | Grid em 4 colunas (`.grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200/80 text-xs mt-6`). | Metadados inline em texto monoespaçado puro. |
| **Pílulas de Contexto** | Sequence de badges coloridos no topo de `<main>` gerados via `--tags`. | Tags no fim do documento ou ausência de tags. |

---

## 3. Catálogo de Componentes Semânticos Permitidos

Ao redigir o conteúdo técnico dentro do `<main>`, utilize os seguintes componentes:

### 3.1. Callouts de Destaque
```html
<div class="callout callout-info">
  <strong>Título do Alerta:</strong> Descrição clara e concisa do aviso técnico.
</div>
```
- **Variantes permitidas:** `callout-info` (azul), `callout-warn` (âmbar), `callout-danger` (vermelho), `callout-success` (verde).

### 3.2. Cards de Comparativo e Destaque
```html
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
  <div class="card border-l-4 border-l-sky-500">
    <h4 class="font-bold text-slate-900">Card 1</h4>
    <p class="text-xs text-slate-600 mt-1">Texto breve e direto.</p>
  </div>
</div>
```

### 3.3. Linha do Tempo Cronológica (`.timeline`)
```html
<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-dot"></div>
    <div class="flex items-center gap-2 mb-1">
      <span class="font-bold text-slate-900 text-sm">DD/MM/AAAA</span>
      <span class="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">Status</span>
    </div>
    <p class="text-xs text-slate-600">Descrição dos fatos e decisões tomadas.</p>
  </div>
</div>
```

### 3.4. Tabelas Corporativas
Sempre estruture dados tabulares com `<table>`, `<thead>`, `<tbody>` e linhas zebradas nativas. O design system aplica bordas sutis e fundo `bg-slate-50` no cabeçalho automaticamente.

### 3.5. Diagramas Mermaid.js Anti-Distorção
```html
<div class="mermaid-wrapper">
  <div class="mermaid">
flowchart LR
  A["Passo 1<br/>Entrada"] -->|"Rótulo"| B["Passo 2<br/>Saída"]
  </div>
</div>
```
- **Regras Críticas**:
  1. Envolva sempre rótulos em aspas duplas: `A["Texto"]`.
  2. NUNCA use tags HTML de negrito (`<b>`, `<strong>`) dentro de nós do Mermaid.
  3. Mantenha diagramas contidos (< 280px de altura) e evite ramificações em árvore com 4+ colunas paralelas em `flowchart TD`.

---

## 4. Tabela Anti-Racionalização para Agentes de IA

| Desculpa / Racionalização do Agente | Realidade / Diretriz Rígida |
| :--- | :--- |
| *"É só uma página simples, posso gerar o HTML rápido com write_to_file."* | **PROIBIDO.** O gerador `scripts/novo_documento.py` leva 1 segundo e garante 100% de conformidade de CSS, fontes e metadados. |
| *"Achei que ficava mais moderno colocar um card cinza com rounded-xl ao redor da página."* | **PROIBIDO.** O padrão oficial do Knowledge OS é folha editorial contínua branca. Cards são componentes internos dentro de seções, nunca wrappers externos da página. |
| *"Vou omitir a grade de metadados em 4 colunas porque o documento é curto."* | **PROIBIDO.** Todos os documentos corporativos exigem a grade formal de cabeçalho (`Data`, `Autor`, `Contexto`, `Versão`). |
| *"O PDF compilou sem erro no Playwright, então está aprovado."* | **FALSO.** Compilar o PDF apenas valida sintaxe; a conformidade visual exige o cumprimento estrito do DOM especificado na anatomia do Design System. |

---

## 5. Protocolo de Inspeção e Validação Final

Após criar e redigir o documento:
1. Valide a conformidade estrutural do DOM e quebras de página:
   ```bash
   python scripts/gerar_pdf.py "caminho/do/documento.html" --check-only
   ```
2. Compile o PDF oficial:
   ```bash
   python scripts/gerar_pdf.py "caminho/do/documento.html"
   ```
3. Sincronize o catálogo mestre de organização:
   ```bash
   python scripts/gerar_organization.py --write
   ```
