"""Valida os 10 casos de roteamento pelo fluxo do projeto_ia_roteamento.py."""
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from projeto_ia_roteamento.projeto_ia_roteamento import (  # noqa: E402
    Message,
    WELCOME_MSG,
    _active_sector_from_history,
    _run_support_team,
)

CASES = [
    ("01", "Minha senha do portal do aluno não funciona.", "ti"),
    ("02", "Quero cancelar minha matrícula, como faço?", "secretaria"),
    ("03", "Preciso do diploma, mas o site de emissão está fora do ar.", "ti"),
    ("04", "Não consigo acessar a rede Wi-Fi da biblioteca.", "ti"),
    ("05", "Qual o prazo para solicitar aproveitamento de disciplinas?", "secretaria"),
    ("06", "Meu nome está escrito errado no portal, preciso arrumar.", "secretaria"),
    ("07", "Estou tentando enviar meu TCC pelo sistema, mas dá erro 500.", "ti"),
    ("08", "Onde pego o comprovante de matrícula para o estágio?", "secretaria"),
    ("10", "Olá, boa tarde! Gostaria de ajuda.", "orchestrator"),
]

FOLLOW_UP = (
    "09",
    "E se eu esquecer o meu login na hora de baixar?",
    "ti",
    "08",
)


def _run_case(case_id: str, prompt: str, expected: str, session_id: str, history: list):
    history.append(Message(role="user", content=prompt, agent="Você", timestamp="00:00"))
    active_sector = _active_sector_from_history(history[:-1])

    for attempt in range(3):
        try:
            _, badge, sector = _run_support_team(prompt, history, session_id, active_sector)
            break
        except Exception as exc:
            if "429" in str(exc) and attempt < 2:
                time.sleep(65)
                continue
            raise

    history.append(Message(role="bot", content="...", agent=badge, timestamp="00:01"))
    time.sleep(5)

    ok = sector == expected
    status = "OK" if ok else "FALHOU"
    print(f"  [{status}] {case_id}: esperado={expected}, obtido={sector} ({badge})")
    return ok


def main():
    print("=" * 60)
    print("Testes de roteamento — projeto_ia_roteamento.py")
    print("=" * 60)

    results = []

    for case_id, prompt, expected in CASES:
        session_id = str(uuid.uuid4())
        history = [WELCOME_MSG]
        ok = _run_case(case_id, prompt, expected, session_id, history)
        results.append(ok)

    session_id = str(uuid.uuid4())
    history = [WELCOME_MSG]
    parent_id = FOLLOW_UP[3]
    case_id, prompt, expected = CASES[7]
    _run_case(case_id, prompt, expected, session_id, history)
    ok = _run_case(FOLLOW_UP[0], FOLLOW_UP[1], FOLLOW_UP[2], session_id, history)
    results.append(ok)
    print(f"  (caso {FOLLOW_UP[0]} continua sessão do caso {parent_id})")

    passed = sum(results)
    total = len(results)
    print("-" * 60)
    print(f"Resultado: {passed}/{total} ({100 * passed // total}%)")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()