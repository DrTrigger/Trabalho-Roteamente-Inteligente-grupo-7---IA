# Bot de Suporte Institucional (Roteamento Inteligente)

Projeto final da disciplina de Inteligência Artificial — Tema 7. Bot de suporte do IFES com roteamento inteligente (TI / Secretaria) usando AGNO, Google Gemini e interface web Reflex.

## Instalação rápida

**PC novo (Windows 11, passo a passo completo):** veja [docs/TUTORIAL_INSTALACAO_WINDOWS.md](docs/TUTORIAL_INSTALACAO_WINDOWS.md)

1. Crie um ambiente virtual: `python -m venv venv`
2. Ative o ambiente: `.\venv\Scripts\Activate.ps1`
3. Instale as dependências: `pip install -r requirements.txt`
4. Crie um arquivo `.env` na raiz com sua chave: `GOOGLE_API_KEY=sua_chave`

## Execução (MVP — apresentação)

```bash
reflex run
```

Acesse o portal no navegador, use os atalhos ou digite sua solicitação.

## Ferramentas auxiliares

- **Testes de roteamento (MVP):** `python testes/testar_roteamento.py`
- **Captura de traces (MVP):** `python testes/salvar_traces.py` → salva em `testes/traces/projeto_ia_roteamento/`
- **Debug manual (protótipo CLI):** `python bot.py`

## Estrutura

- `projeto_ia_roteamento/projeto_ia_roteamento.py` — aplicação principal (Reflex + agentes)
- `bot.py` — protótipo CLI da Semana 1 (traces históricos)
- `testes/casos_de_teste.md` — tabela dos 10 casos de teste
- `testes/traces/projeto_ia_roteamento/` — reasoning traces do MVP (entrega final)
- `testes/traces/` — traces históricos do `bot.py`
- `docs/relatorio_tecnico.md` — relatório técnico do trabalho