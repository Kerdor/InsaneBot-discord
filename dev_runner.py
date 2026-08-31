from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_DIR / "main.py"
POLL_INTERVAL = 5


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def get_head() -> str | None:
    result = run_git("rev-parse", "HEAD")
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def pull() -> bool:
    result = run_git("pull")
    output = (result.stdout + result.stderr).strip()
    if output:
        print(f"[GIT] {output}", flush=True)
    return result.returncode == 0


def start_bot() -> subprocess.Popen:
    print("[RUNNER] Запуск бота...", flush=True)
    return subprocess.Popen([sys.executable, str(MAIN_FILE)], cwd=PROJECT_DIR)


def stop_bot(process: subprocess.Popen) -> None:
    if process.poll() is None:
        print("[RUNNER] Останавливаем старый процесс бота...", flush=True)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("[RUNNER] Бот не завершился вовремя, принудительно останавливаем.", flush=True)
            process.kill()
            process.wait()


def main() -> None:
    print(f"[RUNNER] Автообновление включено. Проверка Git каждые {POLL_INTERVAL} сек.", flush=True)
    print("[RUNNER] Для остановки нажмите Ctrl+C.", flush=True)

    process = start_bot()
    current_head = get_head()

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            if process.poll() is not None:
                print(f"[RUNNER] Бот завершился с кодом {process.returncode}.", flush=True)
                return

            old_head = current_head or get_head()
            if not pull():
                print("[GIT] Pull не выполнен. Бот продолжает работать.", flush=True)
                continue

            new_head = get_head()
            if not new_head or new_head == old_head:
                current_head = new_head or old_head
                continue

            print(f"[RUNNER] Обнаружены изменения: {old_head} -> {new_head}", flush=True)
            stop_bot(process)
            current_head = new_head
            process = start_bot()

    except KeyboardInterrupt:
        print("\n[RUNNER] Получен Ctrl+C.", flush=True)
        stop_bot(process)


if __name__ == "__main__":
    main()
