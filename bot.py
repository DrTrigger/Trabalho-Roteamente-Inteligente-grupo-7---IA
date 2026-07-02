import os
from agno.agent import Agent
from agno.team import Team
from agno.models.google import Gemini
from dotenv import load_dotenv

# 1. Instalação e configuração do ambiente
load_dotenv(override=True)

# ==========================================
# AGENTES ESPECIALISTAS
# ==========================================
agent_ti = Agent(
    name="Equipe de TI",
    role="Resolve problemas técnicos de TI (senhas, login, sistemas, infraestrutura)",
    model=Gemini(id="gemini-3.1-flash-lite"),
    instructions=[
        "Você é o técnico de Suporte de TI da universidade.",
        "Forneça passos lógicos e formatados em markdown para resolver falhas tecnológicas.",
    ],
    debug_mode=True, 
)

agent_secretaria = Agent(
    name="Secretaria Acadêmica",
    role="Resolve questões administrativas (matrícula, documentos, trancamento, histórico)",
    model=Gemini(id="gemini-3.1-flash-lite"),
    instructions=[
        "Você é o atendente da Secretaria Acadêmica.",
        "Mantenha um tom formal e institucional.",
        "Explique os procedimentos burocráticos de forma clara.",
    ],
    debug_mode=True,
)

# ==========================================
# TIME DE ROTEAMENTO (Orquestrador)
# ==========================================
support_team = Team(
    name="Bot de Suporte Institucional",
    mode="route", # Classifica e roteia para o agente correto
    members=[agent_ti, agent_secretaria],
    model=Gemini(id="gemini-3.1-flash-lite"),
    instructions=[
        "Você é o roteador de triagem da universidade.",
        "Sua única função é encaminhar a solicitação com o contexto correto para TI ou Secretaria.",
        "Regras:",
        "- Falhas de acesso, sistemas e senhas -> Equipe de TI",
        "- Burocracia, documentos e matrículas -> Secretaria Acadêmica",
        "NUNCA responda diretamente. Apenas delegue. Mas, se o usuario perguntar sobre alguma pergunta dele ou quiser continuar a conversa, puxe o histórico e contexto"
    ],
    add_history_to_context=True, # Mantém o histórico da conversa e permite correção
    debug_mode=True, # show_tool_calls = True (Garante a análise de traces)
    show_members_responses=True,
    markdown=True,
)

# ==========================================
# INTERFACE DE EXECUÇÃO
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎓 SISTEMA DE TRIAGEM INSTITUCIONAL INICIADO 🎓")
    print("Digite 'sair' para encerrar.")
    print("="*50 + "\n")

    while True:
        user_input = input("👤 Aluno: ")
        if user_input.lower() in ['sair', 'exit', 'quit']:
            break
        
        print("\n🤖 Processando...\n")
        support_team.print_response(user_input, stream=True)
        print("-" * 50)