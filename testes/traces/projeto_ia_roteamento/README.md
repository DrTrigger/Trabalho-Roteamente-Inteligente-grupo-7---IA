# Traces do MVP — projeto_ia_roteamento.py

Reasoning traces capturados a partir do fluxo real do portal Reflex (`projeto_ia_roteamento/projeto_ia_roteamento.py`), com `SqliteDb`, `debug_mode=True` e os mesmos 10 casos de teste documentados em `testes/casos_de_teste.md`.

## Como regenerar

```bash
python testes/salvar_traces.py
```

Aguarde ~2–3 minutos (há intervalo de 5s entre casos para evitar limite da API Gemini free tier).

## Arquivos

| Arquivo | Caso | Destino esperado |
|---------|------|------------------|
| trace_01_ti.txt | Senha do portal | TI |
| trace_02_secretaria.txt | Cancelar matrícula | Secretaria |
| trace_03_ti_ambiguo.txt | Diploma + site fora do ar | TI |
| trace_04_ti.txt | Wi-Fi biblioteca | TI |
| trace_05_secretaria.txt | Prazo aproveitamento | Secretaria |
| trace_06_secretaria_ambiguo.txt | Nome errado no portal | Secretaria |
| trace_07_ti.txt | Erro 500 no TCC | TI |
| trace_08_secretaria.txt | Comprovante de matrícula | Secretaria |
| trace_09_correcao_rota_ti.txt | Login após caso 08 (mesma sessão) | TI |
| trace_10_triagem_orquestrador.txt | Saudação genérica | Orquestrador |

## Diferença dos traces antigos

A pasta `testes/traces/` (sem subpasta) contém traces do protótipo CLI `bot.py` (Semana 1/2), sem `SqliteDb` e sem interface Reflex. Estes traces são a versão final para entrega e demonstração.