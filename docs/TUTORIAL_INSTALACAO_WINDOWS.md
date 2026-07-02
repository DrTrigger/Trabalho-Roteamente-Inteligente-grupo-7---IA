# Tutorial — Instalar e executar o projeto (Windows 11)

Guia passo a passo para quem baixou o **RAR completo** do projeto e quer rodar o portal Reflex em um PC novo, usando o **Prompt de Comando (CMD)**.

**Projeto:** Bot de Suporte IFES — `projeto_ia_roteamento.py`  
**Comando final:** `reflex run`

---

## O que você vai precisar

| Item | Versão recomendada | Onde baixar |
|------|-------------------|-------------|
| Python | 3.11 ou superior (3.13 funciona) | https://www.python.org/downloads/ |
| Node.js | 20 LTS ou superior | https://nodejs.org/ |
| Chave da API Google (Gemini) | — | https://aistudio.google.com/apikey |

> O Reflex usa Node.js para montar a interface web. Sem Node, o `reflex run` pode falhar.

---

## Passo 1 — Instalar o Python

1. Baixe o instalador do Python para Windows.
2. Execute o instalador.
3. **Marque a opção:** `Add python.exe to PATH` (adicionar ao PATH).
4. Clique em **Install Now** e aguarde terminar.
5. Feche e abra um **novo** CMD para o PATH atualizar.

**Testar no CMD:**

```cmd
python --version
```

Deve aparecer algo como `Python 3.13.x`. Se der erro, reinstale o Python marcando **Add to PATH**.

---

## Passo 2 — Instalar o Node.js

1. Baixe a versão **LTS** em https://nodejs.org/
2. Instale com as opções padrão (Next → Next → Install).
3. Feche e abra um **novo** CMD.

**Testar no CMD:**

```cmd
node --version
npm --version
```

Ambos devem mostrar números de versão.

---

## Passo 3 — Extrair o RAR do projeto

1. Clique com o botão direito no arquivo `.rar` → **Extrair aqui** ou **Extrair em...**
2. Escolha uma pasta simples, por exemplo:

```
C:\projetos\projeto_ia_roteamento
```

3. Evite caminhos muito longos ou com caracteres especiais, se possível.

A pasta extraída deve conter arquivos como:
- `requirements.txt`
- `rxconfig.py`
- `projeto_ia_roteamento\` (pasta do app)
- `docs\`
- `testes\`

---

## Passo 4 — Abrir o CMD na pasta do projeto

**Opção A — Pelo Explorer**

1. Abra a pasta do projeto no Explorador de Arquivos.
2. Clique na barra de endereço, digite `cmd` e pressione **Enter**.

**Opção B — Manualmente**

```cmd
cd /d C:\projetos\projeto_ia_roteamento
```

> Se a pasta estiver em outro lugar (ex.: Área de Trabalho), use aspas:
>
> ```cmd
> cd /d "C:\Users\SEU_USUARIO\OneDrive\Área de Trabalho\projeto_ia_roteamento"
> ```

**Confirmar que está na pasta certa:**

```cmd
dir
```

Deve listar `requirements.txt`, `rxconfig.py`, etc.

---

## Passo 5 — Criar ambiente virtual Python

No CMD, dentro da pasta do projeto:

```cmd
python -m venv venv
```

Aguarde alguns segundos. Será criada a pasta `venv\`.

---

## Passo 6 — Ativar o ambiente virtual

No **CMD** (não PowerShell):

```cmd
venv\Scripts\activate.bat
```

O prompt deve mudar e mostrar `(venv)` no início da linha:

```
(venv) C:\projetos\projeto_ia_roteamento>
```

---

## Passo 7 — Instalar dependências do projeto

Com o `(venv)` ativo:

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Aguarde o download e instalação (pode levar 2–5 minutos na primeira vez).

---

## Passo 8 — Configurar a chave da API (arquivo .env)

O projeto **não funciona** sem a chave do Google Gemini.

1. Na raiz do projeto (mesma pasta do `requirements.txt`), crie um arquivo chamado `.env`
2. Abra com o Bloco de Notas e coloque **uma linha**:

```
GOOGLE_API_KEY=sua_chave_aqui
```

3. Substitua `sua_chave_aqui` pela chave real obtida em https://aistudio.google.com/apikey
4. Salve e feche.

**Pelo CMD (alternativa rápida):**

```cmd
echo GOOGLE_API_KEY=COLE_SUA_CHAVE_AQUI > .env
```

Depois edite o `.env` no Bloco de Notas e cole a chave correta.

> **Importante:** nunca compartilhe o arquivo `.env` publicamente.

---

## Passo 9 — Iniciar o portal (Reflex)

Ainda com `(venv)` ativo e na pasta raiz do projeto:

```cmd
reflex run
```

**Na primeira execução**, o Reflex pode:
- Baixar pacotes npm (demora alguns minutos)
- Perguntar sobre inicialização — aceite as opções padrão se aparecer algo

Quando subir com sucesso, o terminal mostra URLs parecidas com:

```
App running at: http://localhost:3000
Backend running at: http://localhost:8000
```

O navegador pode abrir automaticamente. Se não abrir, acesse manualmente:

**http://localhost:3000**

---

## Passo 10 — Usar o portal

1. Aguarde a tela de chat do **Portal de Atendimento IFES** carregar.
2. Digite uma solicitação (ex.: `Esqueci minha senha do portal`) ou use os atalhos.
3. Clique em **Enviar**.
4. A IA encaminha para **TI** ou **Secretaria** conforme o assunto.

Para encerrar o servidor: no CMD, pressione **Ctrl + C**.

---

## Resumo rápido (copiar e colar)

Abra o CMD na pasta do projeto e execute **na ordem**:

```cmd
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Crie o `.env` com `GOOGLE_API_KEY=...` e depois:

```cmd
reflex run
```

---

## Problemas comuns

### `python` não é reconhecido

- Reinstale o Python marcando **Add python.exe to PATH**.
- Feche e abra o CMD novamente.

### `reflex` não é reconhecido

- Confirme que o venv está ativo: `(venv)` no prompt.
- Rode de novo: `pip install -r requirements.txt`

### Erro de API / 401 / 403

- Verifique se o `.env` está na **raiz** do projeto (junto com `requirements.txt`).
- Confirme se a chave em `GOOGLE_API_KEY` está correta, sem espaços extras.

### Erro 429 (quota exceeded)

- A API Gemini free tier tem limite de requisições por minuto.
- Aguarde 1 minuto e tente de novo.

### `npm` ou `node` não encontrado

- Instale o Node.js LTS e abra um **novo** CMD.

### Pasta com acento ou espaço dá erro

- Use aspas no `cd`:
  ```cmd
  cd /d "C:\Users\breno\OneDrive\Área de Trabalho\projeto_ia_roteamento"
  ```

### Firewall do Windows bloqueou

- Clique em **Permitir acesso** quando o Windows perguntar sobre Python/Node na rede privada.

---

## Comandos opcionais (não necessários para a demo)

**Testar roteamento (10 casos):**

```cmd
venv\Scripts\activate.bat
python testes\testar_roteamento.py
```

**Protótipo CLI (sem interface web):**

```cmd
venv\Scripts\activate.bat
python bot.py
```

---

## Estrutura mínima esperada após extração

```
projeto_ia_roteamento/
├── .env                    ← você cria (não vem no RAR público)
├── requirements.txt
├── rxconfig.py
├── venv/                   ← você cria no Passo 5
├── projeto_ia_roteamento/
│   └── projeto_ia_roteamento.py
├── docs/
│   └── relatorio_tecnico.md
└── testes/
```

---

**Dúvidas sobre o trabalho:** consulte `docs/relatorio_tecnico.md`  
**Demonstração em sala:** use `reflex run` e mostre 2 casos (senha → TI; diploma + site fora do ar → TI).