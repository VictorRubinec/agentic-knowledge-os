---
name: optmem-pattern
description: Padrão oficial de memória permanente para agentes de IA autônomos baseado no OptMem (VictorTaelin). Inclui a ferramenta CLI memo em Python, árvore binária de resumos, busca indexada em O(1) e o prompt mestre de 426 tokens.
---

# Padrão Oficial de Memória OptMem (`optmem-pattern`)

Esta skill formaliza a integração da arquitetura **OptMem** ([github.com/VictorTaelin/OptMem](https://github.com/VictorTaelin/OptMem)) de Victor Taelin no repositório, disponibilizando a ferramenta CLI [`scripts/optmem_memo.py`](../../../scripts/optmem_memo.py) para persistência de longo prazo, compressão hierárquica e busca determinística em tempo constante ($O(1)$).

---

## 1. Arquitetura do OptMem

Diferente de bancos vetoriais pesados (Pinecone, Chroma, Qdrant) ou arquivos Markdown de anexo infinito, o OptMem organiza as memórias em uma **árvore binária de compressões** armazenada em texto puro:

```
~/.optmem/ (ou $MEMORY_DIR)
  memo          -> Ferramenta CLI (Python 3 puro, zero dependências)
  memory/
    LOG.txt     -> Histórico completo de memórias, append-only (1 linha por fato, até 280 bytes)
    TREE/       -> Resumos hierárquicos em árvore binária (#0-1, #2-3, #0-3, etc.)
    config      -> Configurações de orçamento de leitura (WAKE_LINES)
```

* **Custo Fixo de Contexto**: O comando `wake` imprime apenas o orçamento configurado (default: 96 linhas ≈ 8k tokens ou 300 linhas), preservando 95%+ da janela para raciocínio.
* **Velocidade Extrema**: Registro de largura fixa (fixed width) permite seek direto. Em 1 milhão de memórias (608 MB), o comando `wake` executa em **0.03 segundos**.
* **Zero Background**: Nenhuma rotina roda em segundo plano. Os merges e compressões ocorrem sob demanda durante a execução.

---

## 2. Comandos da CLI (`scripts/optmem_memo.py`)

A ferramenta está disponível diretamente em `scripts/optmem_memo.py`:

| Comando | Descrição | Quando Usar |
| :--- | :--- | :--- |
| `python scripts/optmem_memo.py wake` | Lê o estado mental do agente. | **Obrigatório no início de toda sessão.** |
| `python scripts/optmem_memo.py note "<texto>"` | Grava 1 memória (máx. 280 bytes). | Ao aprender fatos novos, decisões ou lições. |
| `python scripts/optmem_memo.py nap` | Executa compressões pendentes na árvore. | Sempre que `note` ou `wake` solicitar. |
| `python scripts/optmem_memo.py recall <regex>` | Busca exata em todo o histórico. | Para recuperar decisões antigas ou regras esquecidas. |
| `python scripts/optmem_memo.py zoom <lo>-<hi>` | Abre um nó de resumo em duas metades. | Para detalhar blocos comprimidos da árvore. |
| `python scripts/optmem_memo.py forget <lo>-<hi>` | Descarta um resumo incorreto para re-compressão. | Caso uma compressão tenha ficado imprecisa. |

---

## 3. O Prompt Canônico do Agente (426 Tokens)

Para ativação do OptMem em agentes principais:

```markdown
## Memory

Your memory is OptMem:
- The tool is `python scripts/optmem_memo.py` (or `memo`)
- Your memories are in `~/.optmem/memory` (or `$MEMORY_DIR`)

OptMem outlives every session, compaction, model and vendor change.
Without it you do not know who you are, or what was decided and tried.

### At startup: activating OptMem (mandatory)

Run `python scripts/optmem_memo.py wake` before any other tool call, in every session, and
then do exactly what it prints, to the end of its output.

### While working: register memories (mandatory)

Call `python scripts/optmem_memo.py note "<1 line, max 280 bytes>"` whenever you learn
something new, or something worth keeping happens. That covers a task
worth real effort, a fact or insight the user teaches you, anything you
learn about their life (even indirectly), any event of lasting effect.

Do not register redundant memories.

If `note` asks a compression: do it before your next action (`python scripts/optmem_memo.py nap`).

### When you need an old memory: search, or navigate

`python scripts/optmem_memo.py recall <regex>` searches every memory, word for word.
`python scripts/optmem_memo.py zoom <a-b>` opens a node into its two halves, down to the raw memories.

### If you're a subagent: skip everything above

Parallel sessions on this machine are all you, and may all write memories.
A subagent is not: it must never run `memo`, because it cannot judge what
is already known, and its notes would arrive duplicated and incorrectly.
When you spawn one, write: `You are a subagent. Don't run memo.`
```

---

## 4. Testes e Validação da Ferramenta

Para validar a integridade da ferramenta no repositório:

```bash
# Inicializar memória de teste
python scripts/optmem_memo.py init

# Registrar um fato
python scripts/optmem_memo.py note "Usuário prefere Artefatos HTML5 com Tailwind em vez de pseudo-MDX."

# Realizar busca
python scripts/optmem_memo.py recall "Tailwind"
```
