from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_DIR / "main.py"
ACTIVITY_CLIENT_DIR = PROJECT_DIR / "activities" / "client"
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "dev_runner.log"
ACTIVITY_CLIENT_LOG_FILE = LOG_DIR / "activity_client.log"
POLL_INTERVAL = 5
NODE_DIR = Path("C:/Program Files/nodejs")
CLOUDFLARED_PATH = Path("C:/cloudflared/cloudflared.exe")

LOG_HANDLE = None

load_dotenv(PROJECT_DIR / ".env")


def setup_logging() -> None:
    global LOG_HANDLE
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_HANDLE = LOG_FILE.open("w", encoding="utf-8", buffering=1)
    ACTIVITY_CLIENT_LOG_FILE.write_text("", encoding="utf-8")
    sys.stdout = LOG_HANDLE
    sys.stderr = LOG_HANDLE
    print("=" * 80, flush=True)
    print(f"[RUNNER] Новый запуск. Лог: {LOG_FILE}", flush=True)
    print("=" * 80, flush=True)


def close_logging() -> None:
    global LOG_HANDLE
    if LOG_HANDLE is not None:
        LOG_HANDLE.flush()
        LOG_HANDLE.close()
        LOG_HANDLE = None


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


def resolve_executable(*names: str) -> str:
    for name in names:
        executable = shutil.which(name)
        if executable:
            return executable
    joined_names = ", ".join(names)
    raise FileNotFoundError(f"Не найден исполняемый файл: {joined_names}")


def resolve_npm() -> str:
    npm = shutil.which("npm.cmd") or shutil.which("npm.exe") or shutil.which("npm")
    if npm:
        return npm
    npm_path = NODE_DIR / "npm.cmd"
    if npm_path.is_file():
        return str(npm_path)
    raise FileNotFoundError(f"Не найден npm: {npm_path}")


def start_bot() -> subprocess.Popen:
    print("[RUNNER] Запуск бота...", flush=True)
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.Popen(
        [sys.executable, str(MAIN_FILE)],
        cwd=PROJECT_DIR,
        env=env,
        stdout=LOG_HANDLE,
        stderr=subprocess.STDOUT,
    )


def start_activity_client() -> subprocess.Popen:
    npm = resolve_npm()
    print(f"[RUNNER] Запуск Activity client (Vite): {npm}", flush=True)

    env = dict(os.environ)
    if NODE_DIR.is_dir():
        env["PATH"] = f"{NODE_DIR};{env.get('PATH', '')}"
    activity_client_id = env.get("DISCORD_ACTIVITY_CLIENT_ID", "").strip()
    if activity_client_id:
        env["VITE_DISCORD_CLIENT_ID"] = activity_client_id

    return subprocess.Popen(
        [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=ACTIVITY_CLIENT_DIR,
        env=env,
        stdout=LOG_HANDLE,
        stderr=subprocess.STDOUT,
    )


def start_cloudflare() -> subprocess.Popen:
    cloudflared = shutil.which("cloudflared.exe") or shutil.which("cloudflared")
    if not cloudflared and CLOUDFLARED_PATH.is_file():
        cloudflared = str(CLOUDFLARED_PATH)
    if not cloudflared:
        raise FileNotFoundError(f"Не найден cloudflared: {CLOUDFLARED_PATH}")
    print(f"[RUNNER] Запуск Cloudflare Quick Tunnel: {cloudflared}", flush=True)
    return subprocess.Popen(
        [cloudflared, "tunnel", "--url", "http://127.0.0.1:5173"],
        cwd=PROJECT_DIR,
        stdout=LOG_HANDLE,
        stderr=subprocess.STDOUT,
    )


def stop_process(process: subprocess.Popen, name: str) -> None:
    if process.poll() is None:
        print(f"[RUNNER] Останавливаем {name}...", flush=True)
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f"[RUNNER] {name} не завершился вовремя, принудительно останавливаем.", flush=True)
            process.kill()
            process.wait()


def stop_bot(process: subprocess.Popen) -> None:
    stop_process(process, "бот")


def stop_activity_client(process: subprocess.Popen) -> None:
    stop_process(process, "Activity client")


def start_all() -> tuple[subprocess.Popen, subprocess.Popen, subprocess.Popen]:
    bot = None
    activity_client = None
    cloudflare = None

    try:
        bot = start_bot()
        time.sleep(1)
        activity_client = start_activity_client()
        time.sleep(2)
        cloudflare = start_cloudflare()
        return bot, activity_client, cloudflare
    except Exception:
        if cloudflare is not None:
            stop_process(cloudflare, "Cloudflare Tunnel")
        if activity_client is not None:
            stop_activity_client(activity_client)
        if bot is not None:
            stop_bot(bot)
        raise


def restart_app_processes(
    bot: subprocess.Popen,
    activity_client: subprocess.Popen,
) -> tuple[subprocess.Popen, subprocess.Popen]:
    stop_bot(bot)
    stop_activity_client(activity_client)
    return start_bot(), start_activity_client()


def stop_all(
    bot: subprocess.Popen,
    activity_client: subprocess.Popen,
    cloudflare: subprocess.Popen,
) -> None:
    stop_process(cloudflare, "Cloudflare Tunnel")
    stop_activity_client(activity_client)
    stop_bot(bot)


def main() -> None:
    setup_logging()
    print(f"[RUNNER] Автообновление включено. Проверка Git каждые {POLL_INTERVAL} сек.", flush=True)
    print("[RUNNER] Запуск Discord bot + Activity client + Cloudflare Tunnel.", flush=True)
    print("[RUNNER] Для остановки нажмите Ctrl+C.", flush=True)

    bot, activity_client, cloudflare = start_all()
    current_head = get_head()

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            if bot.poll() is not None:
                print(f"[RUNNER] Бот завершился с кодом {bot.returncode}.", flush=True)
                return
            if activity_client.poll() is not None:
                print(f"[RUNNER] Activity client завершился с кодом {activity_client.returncode}.", flush=True)
                return
            if cloudflare.poll() is not None:
                print(f"[RUNNER] Cloudflare Tunnel завершился с кодом {cloudflare.returncode}.", flush=True)
                return

            old_head = current_head or get_head()
            if not pull():
                print("[GIT] Pull не выполнен. Процессы продолжают работать.", flush=True)
                continue

            new_head = get_head()
            if not new_head or new_head == old_head:
                current_head = new_head or old_head
                continue

            print(f"[RUNNER] Обнаружены изменения: {old_head} -> {new_head}", flush=True)
            bot, activity_client = restart_app_processes(bot, activity_client)
            current_head = new_head

    except KeyboardInterrupt:
        print("\n[RUNNER] Получен Ctrl+C.", flush=True)
        stop_all(bot, activity_client, cloudflare)
    finally:
        close_logging()


if __name__ == "__main__":
    main()
