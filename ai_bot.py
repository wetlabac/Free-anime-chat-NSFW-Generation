import logging
import socket
import subprocess
from configparser import ConfigParser
from pathlib import Path

import telebot
from telebot.types import BotCommand

BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "telegram_bot.log"

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)

# Загружаем токен и разрешённые Telegram ID из bot_settings.ini
settings = ConfigParser()
settings_path = BASE_DIR / "bot_settings.ini"

if not settings.read(settings_path, encoding="utf-8"):
    raise FileNotFoundError(f"Не найден файл настроек: {settings_path}")

BOT_TOKEN = settings.get("telegram", "bot_token", fallback="").strip()
ALLOWED_IDS_RAW = settings.get(
    "telegram", "allowed_user_ids", fallback=""
).strip()

if not BOT_TOKEN:
    raise ValueError("В bot_settings.ini не указан bot_token.")

try:
    ALLOWED_USER_IDS = {
        int(user_id.strip())
        for user_id in ALLOWED_IDS_RAW.split(",")
        if user_id.strip()
    }
except ValueError as exc:
    raise ValueError(
        "В allowed_user_ids должны быть указаны числовые Telegram ID "
        "через запятую."
    ) from exc

if not ALLOWED_USER_IDS:
    raise ValueError("В bot_settings.ini не указан allowed_user_ids.")

bot = telebot.TeleBot(BOT_TOKEN)


def is_allowed(message):
    user = getattr(message, "from_user", None)
    return user is not None and user.id in ALLOWED_USER_IDS


def is_allowed_callback(call):
    user = getattr(call, "from_user", None)
    return user is not None and user.id in ALLOWED_USER_IDS


def port_is_open(port):
    """Проверяет, принимает ли соединение локальный сервис на указанном порту."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def get_status():
    services = [
        ("Ollama", 11434),
        ("SillyTavern", 8000),
        ("ComfyUI", 8188),
    ]

    lines = ["✅ Бот работает.", "", "Состояние локальных сервисов:"]

    for name, port in services:
        state = "работает" if port_is_open(port) else "не отвечает"
        lines.append(f"• {name} — {state} (порт {port})")

    lines.extend(
        [
            "",
            "Проверяется доступность порта; это не подтверждает, "
            "что модель загружена.",
        ]
    )
    return "\n".join(lines)


def run_script(script_name, message=None, chat_id=None):
    script_path = BASE_DIR / script_name

    if not script_path.is_file():
        text = f"❌ Не найден файл: {script_path}"
        if message is not None:
            bot.reply_to(message, text)
        elif chat_id is not None:
            bot.send_message(chat_id, text)
        return

    try:
        # Запускаем BAT без отдельного окна CMD; вывод сохраняем в лог.
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            subprocess.Popen(
                ["cmd.exe", "/c", "call", str(script_path)],
                cwd=str(BASE_DIR),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        text = f"✅ Команда отправлена: {script_name}"
        if message is not None:
            bot.reply_to(message, text)
        elif chat_id is not None:
            bot.send_message(chat_id, text)

    except Exception:
        logging.exception("Не удалось запустить %s", script_path)
        text = f"❌ Ошибка запуска {script_name}. Подробности записаны в лог."
        if message is not None:
            bot.reply_to(message, text)
        elif chat_id is not None:
            bot.send_message(chat_id, text)


@bot.message_handler(commands=["start"])
def start_command(message):
    if not is_allowed(message):
        bot.reply_to(message, "❌ Нет доступа.")
        return

    bot.reply_to(message, "Бот запущен. Команды: /status, /start_all, /stop.")


@bot.message_handler(commands=["status"])
def status_command(message):
    if not is_allowed(message):
        bot.reply_to(message, "❌ Нет доступа.")
        return

    bot.reply_to(message, get_status())


@bot.message_handler(commands=["start_all"])
def start_all_command(message):
    if not is_allowed(message):
        bot.reply_to(message, "❌ Нет доступа.")
        return

    run_script("start_all.bat", message=message)


@bot.message_handler(commands=["stop", "stop_all"])
def stop_command(message):
    if not is_allowed(message):
        bot.reply_to(message, "❌ Нет доступа.")
        return

    run_script("stop_all.bat", message=message)


@bot.callback_query_handler(func=lambda call: call.data in ("start_all", "stop_all"))
def button_callback(call):
    if not is_allowed_callback(call):
        bot.answer_callback_query(call.id, "❌ Нет доступа.")
        return

    bot.answer_callback_query(call.id)

    if call.data == "start_all":
        run_script("start_all.bat", chat_id=call.message.chat.id)
    else:
        run_script("stop_all.bat", chat_id=call.message.chat.id)


@bot.message_handler(func=lambda message: True)
def other_messages(message):
    if not is_allowed(message):
        return

    text = message.text or ""
    if not text.startswith("/"):
        bot.reply_to(message, "Используй /status, /start_all или /stop.")


if __name__ == "__main__":
    try:
        bot.set_my_commands(
            [
                BotCommand("start", "Показать команды"),
                BotCommand("status", "Проверить сервисы"),
                BotCommand("start_all", "Запустить нейросети"),
                BotCommand("stop", "Остановить нейросети"),
            ]
        )
        logging.info("Бот запускается.")
        bot.infinity_polling(timeout=10, long_polling_timeout=10)
    except Exception:
        logging.exception("Ошибка при запуске или работе бота.")