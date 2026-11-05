---
name: anti-slop
description: Diretrizes de governança e filtros anti-slop para impedir que agentes de IA gerem código redundante, estética genérica de IA (AI slop) ou componentes inflados desnecessários.
---

# Anti-Slop & Ponytail: Governança de Qualidade Visual e Código Enxuto

Inspirado nos projetos de código aberto **Anti-Slop** (`github.com/miqdadbadjuber/anti-slop`) e **Ponytail** (`github.com/sneakylarper/ponytail`), esta skill estabelece guardrails determinísticos para manter o ecossistema do Knowledge OS limpo, sóbrio, sustentável e focado em padrões nativos da web.

---

## 1. O que é o "Visual Padrão de IA" (AI Slop)

Agentes de IA tendem a convergir para um conjunto repetitivo de padrões decorativos que aumentam o consumo de tokens, prejudicam a densidade de informação e conferem um aspecto amador ou de "mockup rápido":

1. **Gradientes Roxos/Índigo Excessivos**:
   - `linear-gradient(135deg, #6366f1, #a855f7)` colocado em cartões, botões e fundos sem motivo semântico.
2. **Ícones Decorativos Sem Sentido (Sparkles & Stars)**:
   - Uso indiscriminado de emojis ou SVGs de brilho (`✨`, `🌟`, `⚡`) ao lado de títulos técnicos ("AI-Powered", "Smart Summary").
3. **Badges Falsos**:
   - Pílulas decorativas como `BETA`, `AI-DRIVEN`, `V2.0 PRO`, `MAGIC` que não representam estados reais do sistema.
4. **Falsos Terminais Decorativos**:
   - Caixas com 3 botõezinhos coloridos (vermelho, amarelo, verde) apenas para encapsular uma linha simples de texto ou código sem utilidade de shell.
5. **Prolixidade de Preâmbulo ("Caveman Guardrail Violations")**:
   - Agentes escrevendo parágrafos introdutórios vazios ("Com certeza! Vou te ajudar com isso com muito prazer...").

---

## 2. Regras Anti-Slop para HTML5 e CSS no Knowledge OS

Todo documento gerado em `scripts/novo_documento.py` ou editado pelos agentes deve respeitar estritamente:

* **Paleta Neutra e Funcional**: Use a paleta de alta legibilidade corporativa (fundo neutro `#f8fafc` ou `#0f172a`, bordas sutis `#e2e8f0` ou `#1e293b`, acento sóbrio `#2563eb` ou `#0284c7`). Proibido gradientes de múltiplas cores saturadas em blocos de texto.
* **Ícones Semânticos e SVG Limpos**: Use ícones estritamente funcionais (status, download, alerta, link externo). Proibido ícones de "brilho mágico".
* **Densidade de Informação**: Menos cartões vazios flutuantes, mais tabelas estruturadas, diagramas com grid de 4px e listas de especificações diretas.
* **Badges Conectados ao Estado Real**: Badges devem expressar apenas:
  - Status: `PLANEJAMENTO`, `ATIVO`, `HOMOLOGACAO`, `CONCLUIDO`, `ARQUIVADO`.
  - Severidade: `CRITICO`, `ALTO`, `MEDIO`, `BAIXO`.
  - Origem: `OFICIAL`, `HOMEBREW`, `CLIENTE`.

---

## 3. Filosofia Ponytail: Padrões Nativos da Web (Zero Boilerplate)

Antes de escrever um componente complexo com centenas de linhas de JavaScript ou CSS reativo, pergunte: **o navegador já resolve isso nativamente?**

| Necessidade | Slop Comum (Evitar) | Padrão Ponytail (Obrigatório) |
| :--- | :--- | :--- |
| **Seletor de Data** | Pacote React Datepicker (400+ linhas) | `<input type="date" />` nativo |
| **Modal / Diálogo** | Overlay customizado com trap focus manual | `<dialog>` nativo com `.showModal()` |
| **Acordeão / FAQ** | State machine JS para toggle de altura | `<details>` e `<summary>` nativos |
| **Tooltips** | Biblioteca Popper.js / Tippy.js | Atributo `title` ou CSS puro com `@starting-style` |
| **Layouts de Grade** | Frameworks de grid flutuante | `display: grid; grid-template-columns: repeat(...)` |
| **Tabelas Zebradas** | Classes repetitivas em cada `<tr>` | CSS `:nth-child(even)` |

---

## 4. Checklist Rápido de Validação

Ao inspecionar ou redigir documentos técnicos e código:
- [ ] O documento usa a tipografia e tokens oficiais do Knowledge OS?
- [ ] Foram eliminados emojis em títulos e cabeçalhos de seção?
- [ ] Os diagramas possuem grid sóbrio e linhas nítidas de 1px?
- [ ] O código evita abstrações desnecessárias e usa recursos padrão do ambiente?
