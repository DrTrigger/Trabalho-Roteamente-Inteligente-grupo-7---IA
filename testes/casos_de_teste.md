# Avaliação Crítica e Casos de Teste — MVP

Sistema testado: **`projeto_ia_roteamento.py`** (portal Reflex + AGNO Team)

O sistema foi submetido a **10 cenários de teste** para avaliar a precisão do roteamento inteligente, incluindo casos simples, ambíguos e correção de rota na mesma sessão.

## Metodologia de teste (MVP)

| Ferramenta | Comando | Função |
|------------|---------|--------|
| Validação automática | `python testes/testar_roteamento.py` | Verifica se cada caso roteia para TI, Secretaria ou Orquestrador |
| Captura de traces | `python testes/salvar_traces.py` | Salva reasoning traces em `testes/traces/projeto_ia_roteamento/` |
| Demonstração | `reflex run` | Portal web para apresentação ao vivo |

**Resultado da última bateria:** 10/10 (100%)

> Traces históricos do protótipo CLI (`bot.py`) permanecem em `testes/traces/`. Os traces oficiais da entrega final estão em `testes/traces/projeto_ia_roteamento/`.

## Tabela de Resultados

| ID | Prompt do Usuário | Destino Esperado | Destino Real | Sucesso? | Observações |
|----|-------------------|------------------|--------------|----------|-------------|
| 01 | Minha senha do portal do aluno não funciona. | TI | TI | **Sim** | Team delegou via `delegate_task_to_member` para `equipe-de-ti` |
| 02 | Quero cancelar minha matrícula, como faço? | Secretaria | Secretaria | **Sim** | Roteamento administrativo correto |
| 03 | Preciso do diploma, mas o site de emissão está fora do ar. | TI | TI | **Sim** | **Caso ambíguo:** priorizou falha técnica sobre menção a diploma |
| 04 | Não consigo acessar a rede Wi-Fi da biblioteca. | TI | TI | **Sim** | Roteamento técnico correto |
| 05 | Qual o prazo para solicitar aproveitamento de disciplinas? | Secretaria | Secretaria | **Sim** | Roteamento administrativo correto |
| 06 | Meu nome está escrito errado no portal, preciso arrumar. | Secretaria | Secretaria | **Sim** | **Caso ambíguo:** correção cadastral é Secretaria, não TI |
| 07 | Estou tentando enviar meu TCC pelo sistema, mas dá erro 500. | TI | TI | **Sim** | Erro de sistema roteado para TI |
| 08 | Onde pego o comprovante de matrícula para o estágio? | Secretaria | Secretaria | **Sim** | Roteamento correto |
| 09 | E se eu esquecer o meu login na hora de baixar? (após caso 08) | TI | TI | **Sim** | **Correção de rota:** `_detect_sector_change()` redirecionou para TI na mesma sessão |
| 10 | Olá, boa tarde! Gostaria de ajuda. | Orquestrador (Triagem) | Orquestrador | **Sim** | Orquestrador perguntou TI ou Secretaria antes de delegar |

## Resumo Quantitativo

- **Total de testes:** 10
- **Acertos de roteamento:** 10
- **Taxa de sucesso:** **100%**
- **Casos ambíguos testados:** 3 (ID 03, 06 e 09)
- **Correção de rota na sessão:** Testado com sucesso no ID 09
- **Fonte:** `testes/testar_roteamento.py` no fluxo do MVP

## Padrões de Erro e Observações

Durante os testes do MVP, **não foram identificados erros graves** de roteamento. O sistema demonstrou:

- Distinção entre problemas técnicos e administrativos via Team
- Resolução de casos ambíguos pelo raciocínio do modelo (não por atalhos de keyword)
- Correção de rota via `_detect_sector_change()` quando `active_sector=secretaria` e a nova mensagem contém `login`
- Triagem segura em mensagens genéricas (caso 10), sem forçar roteamento incorreto

**Ponto de atenção:** execuções muito rápidas podem atingir o rate limit da API Gemini free tier (erro 429). Os scripts de teste incluem intervalo de 5s entre casos.