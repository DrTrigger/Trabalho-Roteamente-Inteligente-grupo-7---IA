"""Captura reasoning traces do MVP projeto_ia_roteamento.py para o relatório."""
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from projeto_ia_roteamento.projeto_ia_roteamento import (  # noqa: E402
    Message,
    WELCOME_MSG,
    _active_sector_from_history,
    _run_support_team,
    agent_secretaria,
    agent_ti,
    support_team,
)

TRACES_DIR = Path(__file__).resolve().parent / "traces" / "projeto_ia_roteamento"

CASES = [
    ("01", "trace_01_ti.txt", "Minha senha do portal do aluno não funciona.", "ti"),
    ("02", "trace_02_secretaria.txt", "Quero cancelar minha matrícula, como faço?", "secretaria"),
    ("03", "trace_03_ti_ambiguo.txt", "Preciso do diploma, mas o site de emissão está fora do ar.", "ti"),
    ("04", "trace_04_ti.txt", "Não consigo acessar a rede Wi-Fi da biblioteca.", "ti"),
    ("05", "trace_05_secretaria.txt", "Qual o prazo para solicitar aproveitamento de disciplinas?", "secretaria"),
    ("06", "trace_06_secretaria_ambiguo.txt", "Meu nome está escrito errado no portal, preciso arrumar.", "secretaria"),
    ("07", "trace_07_ti.txt", "Estou tentando enviar meu TCC pelo sistema, mas dá erro 500.", "ti"),
    ("08", "trace_08_secretaria.txt", "Onde pego o comprovante de matrícula para o estágio?", "secretaria"),
    ("10", "trace_10_triagem_orquestrador.txt", "Olá, boa tarde! Gostaria de ajuda.", "orchestrator"),
]

CASE_09 = (
    "09",
    "trace_09_correcao_rota_ti.txt",
    "E se eu esquecer o meu login na hora de baixar?",
    "ti",
)


@contextmanager
def _capture_output(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = handle
        sys.stderr = handle
        try:
            yield handle
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def _enable_debug():
    support_team.debug_mode = True
    agent_ti.debug_mode = True
    agent_secretaria.debug_mode = True


def _write_header(handle, case_id: str, prompt: str, expected: str, extra: str = ""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    handle.write("# MVP — projeto_ia_roteamento.py\n")
    handle.write(f"# Caso ID: {case_id}\n")
    handle.write(f'# Prompt: "{prompt}"\n')
    handle.write(f"# Destino esperado: {expected.upper()}\n")
    if extra:
        handle.write(f"# {extra}\n")
    handle.write(f"# Executado em: {now}\n")
    handle.write("#" + "=" * 59 + "\n\n")


def _run_and_save(
    case_id: str,
    filename: str,
    prompt: str,
    expected: str,
    session_id: str,
    history: list,
    extra: str = "",
):
    history.append(Message(role="user", content=prompt, agent="Você", timestamp="00:00"))
    active_sector = _active_sector_from_history(history[:-1])
    out_path = TRACES_DIR / filename

    for attempt in range(3):
        try:
            with _capture_output(out_path) as handle:
                _write_header(handle, case_id, prompt, expected, extra)
                handle.flush()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = handle
                sys.stderr = handle
                try:
                    print(f"--- Execução caso {case_id} ---")
                    print(f"session_id: {session_id}")
                    print(f"active_sector: {active_sector or '(nenhum)'}")
                    print(f"prompt: {prompt}\n")

                    bot_reply, badge, sector = _run_support_team(
                        prompt, history, session_id, active_sector
                    )

                    print(f"\n--- Resultado ---")
                    print(f"badge: {badge}")
                    print(f"sector: {sector}")
                    print(f"resposta (início): {bot_reply[:300]}...")
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
            break
        except Exception as exc:
            if "429" in str(exc) and attempt < 2:
                time.sleep(65)
                continue
            raise

    history.append(Message(role="bot", content="...", agent=badge, timestamp="00:01"))
    ok = sector == expected
    print(f"  [{'OK' if ok else 'FALHOU'}] {case_id} -> {out_path.name} (sector={sector})")
    return ok


def main():
    print("=" * 60)
    print("Captura de traces — projeto_ia_roteamento.py")
    print(f"Destino: {TRACES_DIR}")
    print("=" * 60)

    _enable_debug()
    TRACES_DIR.mkdir(parents=True, exist_ok=True)

    for case_id, filename, prompt, expected in CASES:
        session_id = str(uuid.uuid4())
        history = [WELCOME_MSG]
        _run_and_save(case_id, filename, prompt, expected, session_id, history)
        time.sleep(5)

    session_id = str(uuid.uuid4())
    history = [WELCOME_MSG]
    c08 = CASES[7]
    _run_and_save(c08[0], c08[1], c08[2], c08[3], session_id, history)
    time.sleep(5)

    c09 = CASE_09
    _run_and_save(
        c09[0],
        c09[1],
        c09[2],
        c09[3],
        session_id,
        history,
        extra="Continuação do caso 08 (mesma sessão)",
    )

    print("-" * 60)
    print(f"Traces salvos em: {TRACES_DIR}")
    print("Próximo passo: atualizar docs/relatorio_tecnico.md com as análises.")


if __name__ == "__main__":
    main()