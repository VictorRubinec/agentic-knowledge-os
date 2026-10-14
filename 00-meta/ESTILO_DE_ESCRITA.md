# Diretrizes de Estilo de Escrita e Formatação por Pasta

Este documento define o estilo visual e tom de linguagem a ser adotado em cada categoria do repositório.

---

## 1. Pasta `trabalho/` (`join4/` e `sites/`)

- **Tom de Linguagem**: Técnico, direto, objetivo e estruturado.
- **Elementos Recomendados**:
  - Tabelas de requisitos.
  - Callouts de aviso técnico e regras de negócio.
  - Links para documentação externa e repositórios.
  - Linha do tempo focada em versões, entregas e decisões de arquitetura.

## 2. Pasta `rpg/`

- **Tom de Linguagem**: Imersivo, descritivo, criativo e bem categorizado.
- **Elementos Recomendados**:
  - Componentes `<Badge />` identificando NPCs, Locais, Fichas e Lore.
  - Separadores claros de "Informação de Jogador" vs "Informação do Mestre".
  - Linha do tempo por Sessão de Jogo (ex: `Sessão #01`, `Sessão #02`).

## 3. Pasta `studio-kustom/`

- **Tom de Linguagem**: Estratégico, focado em produto, marca, processos e clientes.
- **Elementos Recomendados**:
  - Listas de tarefas e marcos de projeto.
  - Callouts de prioridades e fluxo de caixa / custos se aplicável.
  - Registros cronológicos de contatos e ideias de design.

## 4. Pasta `projetos/`

- **Tom de Linguagem**: Prático, exploratório e flexível.
- **Elementos Recomendados**:
  - Seções de "Próximos Passos".
  - Links cruzados para ideias de trabalho ou RPG caso haja interseção.

---

## Regra Universal de Edição & Diagramação

1. **Diagramas Visuais com Mermaid.js**:
   - Sempre utilize **Mermaid.js** (blocos ```mermaid) para construir fluxogramas, diagramas de sequência, BPMNs e arquiteturas.
   - **PROIBIÇÃO DE TAGS HTML (`<b>`, `<strong>`, `<i>`, `<code>`, `<div>`)**: Nunca utilize tags HTML de negrito dentro de nós ou rótulos do Mermaid, pois são renderizadas literalmente como texto vazado (`<b>...</b>`). Use texto limpo com quebras `<br/>`.
   - **Padrão de Layout e Proporções**:
     - **Cards Amplos de Comparação / Fases**: Ao comparar fases, pacotes (MVP vs Escala) ou estados (As-Is vs To-Be), utilize blocos `flowchart LR` contendo cards ricos formatados:
       ```mermaid
       flowchart LR
           F1["FASE 1: MVP (Mês 1)<br/><br/>• Entregável 1<br/>• Entregável 2"]
           F2["FASE 2: Escala (Meses 2 a 4)<br/><br/>• Entregável 3<br/>• Entregável 4"]
           F1 ==>|"Ganhos Comprovados<br/>& Validação"| F2
           style F1 fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff,text-align:left
           style F2 fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#fff,text-align:left
       ```
     - **Fitas Sequenciais Concisas**: Para jornadas e passos lineares (3 a 4 nós), use `flowchart LR` com nós concisos de 2 linhas (`PASSO["Passo 1<br/>Ação principal"]`).
     - **Evitar Distorções**: Não criar linhas horizontais com mais de 4 subgrafos adjacentes e não empilhar nós verticais excessivamente largos em `flowchart TD` estreito.
2. **Atualização de Metadados**: Sempre que um arquivo `.mdx` for modificado, atualize a propriedade `updatedAt` no frontmatter YAML.
3. **Linha do Tempo**: Adicione a entrada correspondente em `## Linha do Tempo`.
4. **Memória**: Registre a alteração no [`MEMORY.md`](../MEMORY.md).
