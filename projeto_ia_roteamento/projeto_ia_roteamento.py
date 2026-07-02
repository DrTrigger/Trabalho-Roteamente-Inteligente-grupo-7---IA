import reflex as rx
import uuid
import os
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List
from agno.agent import Agent
from agno.team import Team
from agno.models.google import Gemini
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb

# --- CONFIGURAÇÃO DO .ENV ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_env = os.path.join(diretorio_atual, '..', '.env')
if os.path.exists(caminho_env):
    load_dotenv(dotenv_path=caminho_env, override=True)

# --- STORAGE DO AGNO (memória da IA) ---
db_path = os.path.join(diretorio_atual, "..", "agent_storage.db")
db = SqliteDb(db_file=db_path)

# ==========================================
# AGENTES
# ==========================================
agent_ti = Agent(
    id="equipe-de-ti",
    name="Equipe de TI",
    role="Resolve problemas técnicos de TI (senhas, login, sistemas, infraestrutura)",
    model=Gemini(id="gemini-3.1-flash-lite"),
    db=db,
    instructions=[
        "Você é o técnico de Suporte de TI do IFES.",
        "Atenda APENAS problemas técnicos: senhas, login, e-mail, VPN, Wi-Fi, erros de sistema.",
        "NÃO trate de matrícula, documentos, histórico escolar ou trancamento.",
        "Forneça passos claros e objetivos em markdown.",
        "Use listas numeradas quando possível.",
    ],
    num_history_messages=12,
    add_history_to_context=True,
)

agent_secretaria = Agent(
    id="secretaria-academica",
    name="Secretaria Acadêmica",
    role="Resolve questões administrativas (matrícula, documentos, trancamento, histórico escolar)",
    model=Gemini(id="gemini-3.1-flash-lite"),
    db=db,
    instructions=[
        "Você é o atendente da Secretaria Acadêmica do IFES.",
        "Atenda matrícula, documentos, requerimentos, trancamento e histórico escolar.",
        "NÃO trate de senhas, login, VPN, Wi-Fi, erros técnicos ou falhas de sistema.",
        "Mantenha tom formal e institucional.",
        "Explique os procedimentos de forma clara e organizada.",
    ],
    num_history_messages=12,
    add_history_to_context=True,
)

# --- TEAM (Roteador) ---
support_team = Team(
    name="Bot de Suporte Institucional",
    mode="route",
    members=[agent_ti, agent_secretaria],
    model=Gemini(id="gemini-3.1-flash-lite"),
    db=db,
    instructions=[
        "Você é o roteador inteligente do Portal de Atendimento do IFES.",
        "Sua função principal é delegar para UM membro especialista. Nunca misture os setores.",
        "",
        "Secretaria Acadêmica (secretaria-academica):",
        "- matrícula, cancelamento, trancamento, documentos, diploma, certificado",
        "- histórico ESCOLAR (documento acadêmico), declarações, requerimentos, protocolo",
        "- correção de dados cadastrais (nome errado no portal)",
        "",
        "Equipe de TI (equipe-de-ti):",
        "- senhas, login, e-mail institucional, VPN, Wi-Fi, portal inacessível",
        "- erros técnicos, site fora do ar, Q-Acadêmico com falha, sistemas e infraestrutura",
        "",
        "IMPORTANTE:",
        "- 'histórico escolar' ou 'solicitar histórico' = documento da Secretaria, NUNCA TI.",
        "- Se a mensagem menciona documento E problema técnico (ex: diploma + site fora do ar), priorize TI.",
        "- Se o aluno mudar de assunto na mesma conversa, delegue para o setor da NOVA pergunta.",
        "- Se a NOVA mensagem mencionar login, senha ou erro técnico, mesmo após assunto administrativo, delegue para TI.",
        "- Em continuações do MESMO assunto (ex: 'agora vou onde?'), delegue ao setor que estava tratando aquele tema.",
        "- Se a intenção for vaga (ex: 'preciso de ajuda'), pergunte se é TI ou Secretaria ANTES de delegar.",
        "",
        "Exemplos:",
        "- 'Preciso solicitar meu histórico escolar' -> secretaria-academica",
        "- 'Esqueci minha senha do portal' -> equipe-de-ti",
        "- 'Preciso do diploma, mas o site está fora do ar' -> equipe-de-ti",
        "- 'Meu nome está errado no portal' -> secretaria-academica",
        "- 'Olá, gostaria de ajuda' -> pergunte TI ou Secretaria (não delegue ainda)",
    ],
    num_history_messages=12,
    add_history_to_context=True,
    show_members_responses=True,
    markdown=True,
)

# ==========================================
# MODELO DE MENSAGEM
# ==========================================
@dataclass
class Message:
    role: str
    content: str
    agent: str
    timestamp: str

BADGE_TI = "🖥️ Equipe de TI"
BADGE_SECRETARIA = "📋 Secretaria Acadêmica"
BADGE_ORCHESTRATOR = "Assistente IA"


def _sector_from_badge(agent: str) -> str:
    if "TI" in agent:
        return "ti"
    if "Secretaria" in agent:
        return "secretaria"
    return ""


def _badge_from_sector(sector: str) -> str:
    if sector == "ti":
        return BADGE_TI
    if sector == "secretaria":
        return BADGE_SECRETARIA
    return BADGE_ORCHESTRATOR


def _sector_from_member_response(response) -> str:
    for member in reversed(response.member_responses or []):
        name = (getattr(member, "agent_name", None) or "").lower()
        agent_id = (getattr(member, "agent_id", None) or "").lower()
        if "secretaria" in name or "secretaria" in agent_id:
            return "secretaria"
        if "ti" in name or "ti" in agent_id:
            return "ti"
    return "orchestrator"


def _agent_display_name(agent: Agent) -> str:
    agent_id = (getattr(agent, "id", None) or "").lower()
    if "secretaria" in agent_id or "secretaria" in agent.name.lower():
        return BADGE_SECRETARIA
    return BADGE_TI


def _active_sector_from_history(chat_history: List[Message]) -> str:
    for message in reversed(chat_history):
        if message.role == "bot":
            sector = _sector_from_badge(message.agent)
            if sector:
                return sector
    return ""


def _resolve_fallback_agent(active_sector: str, chat_history: List[Message]) -> Agent:
    if active_sector == "ti":
        return agent_ti
    if active_sector == "secretaria":
        return agent_secretaria
    last_sector = _active_sector_from_history(chat_history)
    if last_sector == "ti":
        return agent_ti
    if last_sector == "secretaria":
        return agent_secretaria
    return agent_secretaria


TI_CHANGE_SIGNALS = (
    "senha", "login", "wi-fi", "wifi", "vpn", "erro", "fora do ar",
    "não consigo acessar", "nao consigo acessar", "não consigo entrar",
    "nao consigo entrar",
)
SECRETARIA_CHANGE_SIGNALS = (
    "matrícula", "matricula", "trancar", "trancamento", "documento",
    "histórico escolar", "historico escolar", "diploma", "requerimento",
    "cancelar matrícula", "cancelar matricula",
)


TECH_FAILURE_SIGNALS = (
    "fora do ar", "indisponível", "indisponivel", "não funciona", "nao funciona",
    "não abre", "nao abre", "erro 500", "erro 404", "erro técnico", "erro tecnico",
    "instabilidade", "caiu o site", "caiu o sistema",
)


def _detect_ambiguous_mixed_case(user_message: str) -> Agent | None:
    """Documento/burocracia + falha técnica na mesma mensagem → TI resolve primeiro."""
    lower = user_message.lower()
    has_admin = any(s in lower for s in SECRETARIA_CHANGE_SIGNALS)
    has_tech = any(s in lower for s in TI_CHANGE_SIGNALS) or any(
        s in lower for s in TECH_FAILURE_SIGNALS
    )
    if has_admin and has_tech:
        return agent_ti
    return None


def _detect_sector_change(user_message: str, active_sector: str) -> Agent | None:
    """Corrige roteamento quando a nova mensagem indica mudança clara de setor."""
    lower = user_message.lower()
    if active_sector == "secretaria" and any(s in lower for s in TI_CHANGE_SIGNALS):
        return agent_ti
    if active_sector == "ti" and any(s in lower for s in SECRETARIA_CHANGE_SIGNALS):
        return agent_secretaria
    return None


def _build_contextual_message(chat_history: List[Message], user_message: str) -> str:
    prior_messages = [m for m in chat_history[:-1] if m.role in ("user", "bot")][-4:]
    if not prior_messages:
        return user_message

    transcript = []
    for message in prior_messages:
        speaker = "Aluno" if message.role == "user" else message.agent
        transcript.append(f"{speaker}: {message.content[:800]}")

    lower_new = user_message.lower()
    change_hint = ""
    if any(signal in lower_new for signal in TI_CHANGE_SIGNALS):
        change_hint = (
            "ATENÇÃO: a nova mensagem contém termos técnicos (login, senha, acesso, erro). "
            "Avalie se o setor mudou para a Equipe de TI.\n\n"
        )

    return (
        change_hint
        + "Use o histórico abaixo apenas como contexto. "
        "Responda somente à NOVA mensagem do aluno — o assunto pode ter mudado de setor.\n\n"
        + "\n\n".join(transcript)
        + f"\n\nNova mensagem do aluno: {user_message}"
    )


def _extract_team_reply(response) -> str:
    content = response.content
    if content and str(content).strip():
        return str(content)

    for member in reversed(response.member_responses or []):
        member_content = getattr(member, "content", None)
        if member_content and str(member_content).strip():
            return str(member_content)

    return ""


def _run_agent(agent: Agent, message: str, session_id: str) -> str:
    response = agent.run(message, session_id=session_id)
    return _extract_team_reply(response) or "Não foi possível obter uma resposta."


def _run_support_team(
    user_message: str,
    chat_history: List[Message],
    session_id: str,
    active_sector: str = "",
):
    contextual_message = _build_contextual_message(chat_history, user_message)

    ambiguous_agent = _detect_ambiguous_mixed_case(user_message)
    if ambiguous_agent is not None:
        bot_reply = _run_agent(ambiguous_agent, contextual_message, session_id)
        return bot_reply, _agent_display_name(ambiguous_agent), "ti"

    sector_change_agent = _detect_sector_change(user_message, active_sector)
    if sector_change_agent is not None:
        bot_reply = _run_agent(sector_change_agent, contextual_message, session_id)
        sector = "ti" if sector_change_agent is agent_ti else "secretaria"
        return bot_reply, _agent_display_name(sector_change_agent), sector

    response = support_team.run(contextual_message, session_id=session_id)
    bot_reply = _extract_team_reply(response)

    if bot_reply.strip():
        sector = _sector_from_member_response(response)
        if sector == "orchestrator":
            sector = active_sector or "orchestrator"
        return bot_reply, _badge_from_sector(sector), sector

    fallback_agent = _resolve_fallback_agent(active_sector, chat_history)
    bot_reply = _run_agent(fallback_agent, contextual_message, session_id)
    sector = "ti" if fallback_agent is agent_ti else "secretaria"
    return bot_reply, _agent_display_name(fallback_agent), sector


WELCOME_MSG = Message(
    role="bot",
    content=(
        "Olá! Bem-vindo ao **Portal de Atendimento Institucional do IFES**.\n\n"
        "Nossa IA faz a triagem automática e encaminha sua solicitação para o setor correto:\n\n"
        "🖥️ **TI** — senhas, sistemas, acesso, e-mail\n"
        "📋 **Secretaria** — matrícula, documentos, trancamentos, histórico\n\n"
        "Como posso ajudá-lo hoje?"
    ),
    agent="Sistema",
    timestamp="",
)

# ==========================================
# ESTADO DA APLICAÇÃO
# ==========================================
class State(rx.State):
    chat_history: List[Message] = [WELCOME_MSG]
    user_input: str = ""
    is_processing: bool = False
    active_sector: str = ""
    session_id: str = rx.LocalStorage(name="session_id")
    chat_history_json: str = rx.LocalStorage(name="ifes_chat_history_v2")
    _history_restored: bool = False

    def on_load(self):
        self._restore_from_storage()
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

    def sync_from_storage(self):
        """Restaura histórico após o LocalStorage sincronizar com o backend."""
        self._restore_from_storage()
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

    def _restore_from_storage(self):
        if self._history_restored or not self.chat_history_json:
            return
        try:
            data = json.loads(self.chat_history_json)
            if isinstance(data, list) and len(data) > 0:
                self.chat_history = [Message(**item) for item in data]
                self.active_sector = _active_sector_from_history(self.chat_history)
                self._history_restored = True
        except Exception:
            self.chat_history = [WELCOME_MSG]
            self.active_sector = ""

    def _save_history(self):
        try:
            self.chat_history_json = json.dumps(
                [
                    {
                        "role": m.role,
                        "content": m.content,
                        "agent": m.agent,
                        "timestamp": m.timestamp,
                    }
                    for m in self.chat_history
                ]
            )
        except Exception:
            pass

    def set_input(self, value: str):
        self.user_input = value

    def clear_chat(self):
        self.session_id = str(uuid.uuid4())
        self.active_sector = ""
        self._history_restored = False
        self.chat_history = [
            Message(
                role="bot",
                content=WELCOME_MSG.content,
                agent="Sistema",
                timestamp=datetime.now().strftime("%H:%M"),
            )
        ]
        self.chat_history_json = ""
        self._save_history()

    async def handle_submit(self):
        user_message = self.user_input.strip()
        if not user_message or self.is_processing:
            return

        now = datetime.now().strftime("%H:%M")

        # Adiciona mensagem do usuário
        self.chat_history.append(
            Message(role="user", content=user_message, agent="Você", timestamp=now)
        )
        self._save_history()
        self.user_input = ""
        self.is_processing = True
        yield

        # ============================================
        # DETECÇÃO DE PERGUNTAS SOBRE O HISTÓRICO (META)
        # ============================================
        meta_keywords = [
            "última dúvida", "ultima duvida", "o que eu perguntei",
            "qual foi minha", "minhas perguntas anteriores", "histórico da conversa",
            "o que eu falei", "última mensagem", "contexto anterior"
        ]
        is_meta = any(kw in user_message.lower() for kw in meta_keywords)

        if is_meta:
            ultimas = [m for m in self.chat_history if m.role == "user"][-5:]
            if ultimas:
                conteudo = "Aqui estão suas últimas interações:\n\n"
                for i, msg in enumerate(ultimas, 1):
                    conteudo += f"**{i}.** {msg.content}\n"
            else:
                conteudo = "Ainda não temos interações anteriores registradas nesta conversa."

            self.chat_history.append(
                Message(role="bot", content=conteudo, agent="Assistente IA", timestamp=now)
            )
            self._save_history()
            self.is_processing = False
            return
        # ============================================

        # --- Fluxo normal: Team do Agno como roteador principal ---
        try:
            bot_reply, agent_name, new_sector = _run_support_team(
                user_message,
                self.chat_history,
                self.session_id,
                self.active_sector,
            )
            if new_sector in ("ti", "secretaria"):
                self.active_sector = new_sector

        except Exception as e:
            bot_reply = f"**Erro interno:** {str(e)}"
            agent_name = "Sistema"

        # Adiciona resposta do bot
        self.chat_history.append(
            Message(role="bot", content=bot_reply, agent=agent_name, timestamp=datetime.now().strftime("%H:%M"))
        )
        self._save_history()
        self.is_processing = False

# ==========================================
# COMPONENTES VISUAIS (mantidos iguais)
# ==========================================
def agent_badge(agent: str) -> rx.Component:
    return rx.box(
        rx.text(agent, size="1", weight="bold"),
        bg=rx.cond(
            agent.contains("TI"),
            "#e3f2fd",
            rx.cond(agent.contains("Secretaria"), "#e0f2f1", "#eceff1"),
        ),
        color=rx.cond(
            agent.contains("TI"),
            "#1565c0",
            rx.cond(agent.contains("Secretaria"), "#00695c", "#37474f"),
        ),
        border_radius="20px",
        padding_x="10px",
        padding_y="3px",
        display="inline-block",
        margin_bottom="6px",
    )

def message_bubble(message: Message) -> rx.Component:
    is_user = message.role == "user"
    return rx.box(
        rx.vstack(
            rx.cond(
                ~is_user,
                rx.hstack(
                    agent_badge(message.agent),
                    rx.text(message.timestamp, size="1", color="#90a4ae"),
                    spacing="2",
                    align_items="center",
                ),
                rx.hstack(
                    rx.text("Você", size="1", weight="bold", color="#5c6bc0"),
                    rx.text(message.timestamp, size="1", color="#90a4ae"),
                    spacing="2",
                    justify="end",
                    width="100%",
                ),
            ),
            rx.box(
                rx.markdown(message.content),
                bg=rx.cond(
                    is_user,
                    "linear-gradient(135deg, #3949ab, #1a237e)",
                    "#ffffff",
                ),
                color=rx.cond(is_user, "#ffffff", "#263238"),
                padding="14px 18px",
                border_radius=rx.cond(
                    is_user,
                    "18px 18px 4px 18px",
                    "18px 18px 18px 4px",
                ),
                box_shadow=rx.cond(
                    is_user,
                    "0 2px 12px rgba(57,73,171,0.25)",
                    "0 2px 8px rgba(0,0,0,0.07)",
                ),
                border=rx.cond(is_user, "none", "1px solid #e8eaf6"),
                width="100%",
            ),
            spacing="1",
            align_items=rx.cond(is_user, "flex-end", "flex-start"),
            width="100%",
        ),
        max_width="78%",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
        padding_x="4px",
        class_name="message-item",
    )

def typing_indicator() -> rx.Component:
    return rx.cond(
        State.is_processing,
        rx.box(
            rx.box(
                rx.hstack(
                    rx.box(width="8px", height="8px", border_radius="50%", bg="#3949ab", class_name="dot dot1"),
                    rx.box(width="8px", height="8px", border_radius="50%", bg="#3949ab", class_name="dot dot2"),
                    rx.box(width="8px", height="8px", border_radius="50%", bg="#3949ab", class_name="dot dot3"),
                    spacing="1",
                    align_items="center",
                ),
                bg="white",
                padding="12px 16px",
                border_radius="18px 18px 18px 4px",
                border="1px solid #e8eaf6",
                box_shadow="0 2px 8px rgba(0,0,0,0.07)",
            ),
            align_self="flex-start",
            padding_x="4px",
        ),
        rx.box(),
    )

def chat_window() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.foreach(State.chat_history, message_bubble),
            typing_indicator(),
            spacing="4",
            width="100%",
            padding_bottom="8px",
        ),
        id="chat-scroll",
        flex="1",
        overflow_y="auto",
        width="100%",
        padding="24px 20px",
        bg="#f4f6fb",
        class_name="chat-window",
    )

def header() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text("IFES", size="3", weight="bold", color="white"),
                bg="rgba(255,255,255,0.15)",
                border_radius="10px",
                padding="8px 12px",
                border="1px solid rgba(255,255,255,0.2)",
            ),
            rx.vstack(
                rx.text("Portal de Atendimento Institucional", size="4", weight="bold", color="white", line_height="1"),
                rx.text("Bot de Suporte com Roteamento Inteligente por IA", size="1", color="rgba(255,255,255,0.75)"),
                spacing="1",
                align_items="flex-start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.box(width="8px", height="8px", border_radius="50%", bg="#69f0ae", box_shadow="0 0 6px #69f0ae"),
                rx.text("Online", size="1", color="rgba(255,255,255,0.85)", weight="medium"),
                spacing="1",
                align_items="center",
            ),
            rx.button(
                rx.hstack(rx.icon("printer", size=14), rx.text("Imprimir", size="1"), spacing="1"),
                on_click=rx.call_script("window.print()"),
                bg="rgba(255,255,255,0.12)", color="white", border="1px solid rgba(255,255,255,0.25)",
                border_radius="8px", padding_x="14px", padding_y="8px", cursor="pointer",
                _hover={"bg": "rgba(255,255,255,0.22)"}, class_name="no-print",
            ),
            rx.button(
                rx.hstack(rx.icon("rotate-ccw", size=14), rx.text("Nova Conversa", size="1"), spacing="1"),
                on_click=State.clear_chat,
                bg="rgba(255,255,255,0.12)", color="white", border="1px solid rgba(255,255,255,0.25)",
                border_radius="8px", padding_x="14px", padding_y="8px", cursor="pointer",
                _hover={"bg": "rgba(255,255,255,0.22)"}, class_name="no-print",
            ),
            spacing="3", align_items="center", width="100%",
        ),
        bg="linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%)",
        padding="18px 24px", width="100%", class_name="portal-header",
    )

def sector_chips() -> rx.Component:
    chip_style = dict(border_radius="20px", padding_x="14px", padding_y="7px", cursor="pointer", size="1", font_size="12px")
    return rx.hstack(
        rx.text("Atalhos:", size="1", color="#78909c", weight="medium"),
        rx.button("🖥️ Resetar senha", on_click=State.set_input("Preciso resetar minha senha do portal acadêmico"),
                  bg="#e8eaf6", color="#3949ab", border="none", _hover={"bg": "#c5cae9"}, **chip_style),
        rx.button("📋 Trancar disciplina", on_click=State.set_input("Quero trancar uma disciplina"),
                  bg="#e0f2f1", color="#00695c", border="none", _hover={"bg": "#b2dfdb"}, **chip_style),
        rx.button("📄 Solicitar histórico", on_click=State.set_input("Preciso solicitar meu histórico escolar"),
                  bg="#e0f2f1", color="#00695c", border="none", _hover={"bg": "#b2dfdb"}, **chip_style),
        rx.button("🔐 Problema de acesso", on_click=State.set_input("Não consigo acessar o sistema Q-Acadêmico"),
                  bg="#e8eaf6", color="#3949ab", border="none", _hover={"bg": "#c5cae9"}, **chip_style),
        spacing="2", align_items="center", wrap="wrap", padding_x="20px", padding_y="10px",
        bg="#fafbff", border_bottom="1px solid #e8eaf6", class_name="no-print",
    )

def input_area() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.input(
                value=State.user_input, on_change=State.set_input,
                placeholder="Descreva sua solicitação... (ex: esqueci minha senha, quero trancar matrícula)",
                width="100%", disabled=State.is_processing, size="3", border_radius="12px",
                border="1.5px solid #c5cae9", padding_x="16px", bg="white", color="#263238",
                _focus={"border_color": "#3949ab", "box_shadow": "0 0 0 3px rgba(57,73,171,0.12)", "outline": "none"},
                _placeholder={"color": "#b0bec5"},
            ),
            rx.button(
                rx.cond(
                    State.is_processing,
                    rx.hstack(rx.spinner(size="2", color="white"), rx.text("Processando...", size="2"), spacing="2"),
                    rx.hstack(rx.icon("send", size=16), rx.text("Enviar", size="2", weight="medium"), spacing="2"),
                ),
                on_click=State.handle_submit,
                bg=rx.cond(State.is_processing, "#7986cb", "#3949ab"),
                color="white", border_radius="12px", padding_x="22px", padding_y="0", height="44px",
                disabled=State.is_processing, cursor=rx.cond(State.is_processing, "not-allowed", "pointer"),
                box_shadow="0 2px 8px rgba(57,73,171,0.3)",
                _hover={"bg": "#1a237e", "box_shadow": "0 4px 12px rgba(57,73,171,0.4)"},
                transition="all 0.2s ease",
            ),
            spacing="3", align_items="center", width="100%",
        ),
        rx.hstack(
            rx.icon("info", size=12, color="#90a4ae"),
            rx.text("Clique em Enviar • A IA identifica e encaminha para TI ou Secretaria automaticamente",
                    size="1", color="#90a4ae"),
            spacing="1", align_items="center", margin_top="8px",
        ),
        padding="16px 20px 18px", bg="white", border_top="1px solid #e8eaf6", width="100%", class_name="no-print",
    )

def footer_info() -> rx.Component:
    return rx.hstack(
        rx.hstack(rx.box(width="6px", height="6px", border_radius="50%", bg="#69f0ae"),
                  rx.text("TI • Infraestrutura e Sistemas", size="1", color="#78909c"), spacing="1"),
        rx.text("•", color="#cfd8dc", size="1"),
        rx.hstack(rx.box(width="6px", height="6px", border_radius="50%", bg="#4db6ac"),
                  rx.text("Secretaria Acadêmica", size="1", color="#78909c"), spacing="1"),
        rx.spacer(),
        rx.text("Sessão ativa", size="1", color="#b0bec5"),
        spacing="2", align_items="center", padding_x="20px", padding_y="8px",
        bg="#f4f6fb", border_top="1px solid #e8eaf6", width="100%", class_name="no-print",
    )

def index() -> rx.Component:
    return rx.box(
        rx.html("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', system-ui, sans-serif !important; box-sizing: border-box; }
body { margin: 0; padding: 0; background: #e8eaf6; }
.chat-window::-webkit-scrollbar { width: 5px; }
.chat-window::-webkit-scrollbar-track { background: transparent; }
.chat-window::-webkit-scrollbar-thumb { background: #c5cae9; border-radius: 10px; }
.chat-window::-webkit-scrollbar-thumb:hover { background: #9fa8da; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; } 40% { transform: scale(1); opacity: 1; } }
.dot { animation: bounce 1.4s infinite ease-in-out; }
.dot1 { animation-delay: 0s; } .dot2 { animation-delay: 0.2s; } .dot3 { animation-delay: 0.4s; }
#chat-scroll { scroll-behavior: smooth; }
.message-item { animation: fadeSlide 0.25s ease-out; }
@keyframes fadeSlide { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media print {
  @page { size: A4 portrait; margin: 15mm 20mm; }
  body { background: white !important; }
  .no-print { display: none !important; }
  .portal-header { background: #1a237e !important; print-color-adjust: exact; padding: 12px 20px !important; }
  .chat-window { height: auto !important; max-height: none !important; overflow: visible !important; background: white !important; }
  .message-item { break-inside: avoid; }
  * { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}
</style>
<script>
const observer = new MutationObserver(() => {
  const el = document.getElementById('chat-scroll');
  if (el) el.scrollTop = el.scrollHeight;
});
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('chat-scroll');
  if (el) {
    observer.observe(el, { childList: true, subtree: true });
    el.scrollTop = el.scrollHeight;
  }
  setTimeout(() => {
    const btn = document.getElementById('sync-storage-trigger');
    if (btn) btn.click();
  }, 300);
});
</script>"""),
        rx.vstack(
            header(),
            sector_chips(),
            chat_window(),
            input_area(),
            footer_info(),
            spacing="0", width="100%", height="100%", border_radius="16px",
            overflow="hidden", box_shadow="0 8px 40px rgba(26,35,126,0.18)",
        ),
        rx.button(
            id="sync-storage-trigger",
            on_click=State.sync_from_storage,
            display="none",
        ),
        width="min(95vw, 920px)", height="min(95vh, 820px)", margin="auto",
        position="fixed", top="50%", left="50%", transform="translate(-50%, -50%)",
    )

app = rx.App(style={"background": "#e8eaf6", "min_height": "100vh"})
app.add_page(index, title="Portal de Atendimento IFES", on_load=State.on_load)