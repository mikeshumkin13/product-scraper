"""
Телеграм-бот для product_scraper.
Получает текстовое сообщение (например: "пылесос"),
запускает src/main.py и отправляет пользователю CSV.

Запуск:
    PS_BOT_TOKEN=... PS_BROWSER=chrome poetry run python src/bot.py
или с .env (см. ниже).
"""

from __future__ import annotations

import os
import socket
import tempfile
import subprocess
import logging
from datetime import datetime
from telegram.constants import ChatAction
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# ── 1) Загружаем настройки из .env ─────────────────────────────────────────────
load_dotenv()  # ищет .env в текущей рабочей директории (корень проекта)

TOKEN = os.getenv("PS_BOT_TOKEN", "")  # токен бота
BROWSER_DEFAULT = os.getenv("PS_BROWSER", "chrome")
MODE_DEFAULT = os.getenv("PS_MODE", "real")  # real|mock
SLOW_DEFAULT = os.getenv("PS_SLOW", "1").lower() in ("1", "true", "yes", "on")
SITES_DEFAULT = os.getenv("PS_SITES", "dns,citilink,wb,ozon")

# Простое состояние (в памяти процесса)
state = {"mode": MODE_DEFAULT, "slow": SLOW_DEFAULT}

HELP_TEXT = (
    "Привет! Отправь мне запрос, например: *пылесос*.\n"
    "Соберу товары с DNS, Citilink, Wildberries и Ozon и пришлю CSV.\n\n"
    "Команды:\n"
    "• /start — помощь\n"
    "• /mock — режим mock (без Selenium)\n"
    "• /real — режим real (Selenium)\n"
)


def build_app() -> Application:
    # подчистим возможные системные прокси, чтобы они не мешали
    for var in (
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "all_proxy",
        "ALL_PROXY",
    ):
        os.environ.pop(var, None)

    # аккуратно парсим прокси из .env (если нужен)
    proxy_raw = os.getenv("TG_PROXY_URL", "")
    proxy = proxy_raw.strip() or None

    req = HTTPXRequest(
        http_version=os.getenv("TG_HTTP_VERSION", "1.1"),
        connect_timeout=float(os.getenv("TG_CONNECT_TIMEOUT", "5")),
        read_timeout=float(os.getenv("TG_READ_TIMEOUT", "30")),
        write_timeout=float(os.getenv("TG_WRITE_TIMEOUT", "30")),
        pool_timeout=float(os.getenv("TG_POOL_TIMEOUT", "5")),
        proxy_url=proxy,
    )
    print(f"[BOT] http={os.getenv('TG_HTTP_VERSION','1.1')} proxy={repr(proxy)}")
    return Application.builder().token(TOKEN).request(req).build()


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Лаконичный лог: чтобы видеть сетевые/прочие сбои PTB
    logging.warning("[PTB] error: %s", context.error)
    # Пытаемся ответить пользователю один раз (не критично, если не получится)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ Небольшой сбой сети на стороне бота. Повторяю попытки, можете отправить запрос ещё раз."
            )
    except Exception:
        pass


# ── 2) Утилиты ────────────────────────────────────────────────────────────────
def have_internet(timeout: float = 2.5) -> bool:
    targets = [("1.1.1.1", 53), ("8.8.8.8", 53), ("www.google.com", 80), ("ya.ru", 80)]
    for host, port in targets:
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            return True
        except OSError:
            continue
    return False


# ── 3) Хэндлеры бота ─────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def set_mock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state["mode"] = "mock"
    await update.message.reply_text("Режим: mock ✅")


async def set_real(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state["mode"] = "real"
    await update.message.reply_text("Режим: real ✅")


async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.message.text or "").strip()
    if not query or query.startswith("/"):
        return

    # Вежливый оффлайн-ответ
    net_ok = have_internet()
    if state["mode"] == "real" and not net_ok:
        await update.message.reply_text(
            "Похоже, есть проблемы с интернетом/VPN. Попробую всё равно; "
            "если не получится — используйте команду /mock."
        )

    await update.message.reply_text(
        f"Ищу: *{query}*\nРежим: `{state['mode']}` — это может занять время…",
        parse_mode="Markdown",
    )
    await update.message.chat.send_action(ChatAction.TYPING)

    # Куда сохраняем CSV (во временную папку)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outname = f"{query}_{ts}.csv".replace(" ", "_")
    outfile = os.path.join(tempfile.gettempdir(), outname)

    # Команда запуска скрапера (main.py)
    cmd = [
        "poetry",
        "run",
        "python",
        "src/main.py",
        "--query",
        query,
        "--mode",
        state["mode"],
        "--output",
        outfile,
    ]
    if state["mode"] == "real" and state["slow"]:
        cmd.append("--slow")

    # Опционально: профиль браузера из .env
    use_profile = os.getenv("PS_USE_PROFILE", "0").lower() in ("1", "true", "yes", "on")
    profile_dir = (os.getenv("PS_PROFILE_DIR", "") or "").strip()
    if use_profile:
        cmd.append("--profile")
    if use_profile and profile_dir:
        cmd += ["--profile-dir", profile_dir]

    # ✅ ВАЖНО: окружение для дочернего процесса (чтобы main.py увидел PS_BROWSER)
    env = os.environ.copy()
    env.setdefault("PS_BROWSER", BROWSER_DEFAULT)

    try:
        # Таймаут 20 минут на тяжёлые запросы
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=1200
        )

        log_tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-3500:]

        if proc.returncode != 0:
            await update.message.reply_text(
                "Парсер вернул ошибку. Отправляю хвост лога:"
            )
            await update.message.reply_text(
                f"```\n{log_tail}\n```", parse_mode="Markdown"
            )
            return

        if not os.path.exists(outfile) or os.path.getsize(outfile) == 0:
            await update.message.reply_text(
                "Похоже, результатов нет. Проверьте VPN/куки и попробуйте другой запрос."
            )
            return

        await update.message.reply_document(
            open(outfile, "rb"), filename=os.path.basename(outfile)
        )
    except subprocess.TimeoutExpired:
        await update.message.reply_text(
            "Время ожидания истекло. Попробуйте более узкий запрос."
        )
    except Exception as e:
        await update.message.reply_text(f"Сбой запуска: `{e}`", parse_mode="Markdown")


def main():
    if not TOKEN:
        raise SystemExit("Задайте PS_BOT_TOKEN в .env или переменных окружения.")

    app = build_app()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mock", set_mock))
    app.add_handler(CommandHandler("real", set_real))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    app.add_error_handler(on_error)

    # drop_pending_updates=True — не тянуть старые апдейты после провалов сети/перезапуска
    app.run_polling(drop_pending_updates=True, poll_interval=1.5)


if __name__ == "__main__":
    main()
