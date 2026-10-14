---
name: optmem-pattern
description: Padrão de memória permanente ultracompacta para agentes de IA autônomos baseado no OptMem (VictorTaelin). Permite persistência contínua entre sessões sem overhead de bancos vetoriais, consumindo menos de 500 tokens.
---

# Padrão de Memória Enxuta para Agentes (`optmem-pattern`)

Esta skill formaliza o padrão de **memória de longo prazo ultraleve** para agentes e subagentes autônomos no repositório, baseado na arquitetura **OptMem** ([github.com/VictorTaelin/OptMem](https://github.com/VictorTaelin/OptMem)).

---

## 1. Filosofia: Por que OptMem em vez de RAG / Vetores?

1. **Zero Infraestrutura**: Dispensa bancos de dados vetoriais (Chroma, Pinecone, Qdrant), containers Docker e custos de embeddings.
2. **Previsibilidade de Contexto**: A memória do agente ocupa uma fração fixa da janela de contexto (**~426 tokens**), deixando 99% do contexto livre para código e raciocínio.
3. **Persistência Humana-Legível**: A memória é armazenada em formato texto/Markdown puro (`agent_memory.md`), permitindo que desenvolvedores leiam, auditem e editem o estado mental do agente a qualquer momento.

---

## 2. O Prompt Mestre de Compressão (426 Tokens)

Ao inicializar ou encerrar ciclos de tarefas longas, o agente deve carregar ou atualizar seu bloco de memória seguindo este prompt:

```text
Você é um agente com memória persistente bounded.
Sua memória é mantida em um único arquivo de texto estruturado.

ESTRUTURA DA MEMÓRIA:
1. FATOS FIXOS: Preferências permanentes do usuário, stack técnica homologada, restrições imutáveis.
2. CONTEXTO ATUAL: Projeto ativo, objetivo imediato da sessão, último estado verificado.
3. LIÇÕES APRENDIDAS: Erros corrigidos, alertas de linters, decisões tomadas para não repetir falhas.
4. PENDÊNCIAS IMEDIATAS: Próximo passo exato a ser executado no retorno.

REGRAS DE ATUALIZAÇÃO (COMPRESSÃO CONTÍNUA):
- Ao receber novas informações, NUNCA apenas anexe linhas infinitas.
- SOBRESCREVA fatos antigos com versões mais recentes e precisas.
- Seja telegráfico, denso e direto. Elimine cortesias e palavras de preenchimento.
- Mantenha o tamanho total do arquivo SEMPRE abaixo de 500 tokens (~300 palavras).
```

---

## 3. Protocolo Operacional para Subagentes

Quando um agente for disparado para executar tarefas de múltiplos passos (como triagem de incidentes, monitoramento de filas ou automações no ClickUp):

1. **Passo 1 (Leitura)**: No início da execução, o agente lê seu arquivo de estado mental:
   * Local padrão para tarefas: `<task_folder>/scratch/agent_memory.md` ou `scratch/agent_memory.md`.
2. **Passo 2 (Execução)**: Opera suas ferramentas normalmente, mantendo em mente os fatos fixos e o objetivo imediato.
3. **Passo 3 (Compressão & Gravação)**: Antes de finalizar o turno ou repassar o controle, o agente reescreve o `agent_memory.md` com o novo estado comprimido.

---

## 4. Exemplo de Estrutura de `agent_memory.md`

```markdown
# Agent Mental State

### Fatos Fixos
- Usuário prefere minimalismo estrito (YAGNI / Anti-bloat).
- Stack: Python 3.11+, Playwright Chromium, Shard Cloud, DBX MCP.
- Proibido instalar PyTorch/CUDA ou containers Docker pesados no repo.

### Contexto Atual
- Projeto: Empresa / Startup / ConsultasPortal BFF.
- Status: Endpoint de autenticação ajustado, pendente teste de carga.

### Lições Aprendidas
- Linters de PDF exigem tags Mermaid entre aspas duplas sem formatação HTML.
- Links internos devem ser relativos, nunca `file:///`.

### Próximos Passos
- Rodar pytest nos validadores e gerar status report semanal.
```

---

## 5. Diretriz de Integração

* **Agentes Principais**: Use o histórico de [`MEMORY.md`](../../../MEMORY.md) para governança global do repositório.
* **Subagentes Efêmeros**: Use `optmem-pattern` para garantir que subagentes mantenham coerência entre chamadas sem sobrecarregar tokens.
