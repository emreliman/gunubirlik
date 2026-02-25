"""Telegram haber botu ana giriş noktası.

Komut tabanlı etkileşim ve günlük zamanlanmış kanal özeti.
Manuel tetikleme: python main.py --now
"""

import argparse
import asyncio
import logging
import os
from datetime import time as dt_time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

from constants import SEND_HOUR, SEND_MINUTE
from scheduler.jobs import run_daily_summary
from bot.commands import (
    ozet_command,
    doviz_command,
    altin_command,
    kripto_command,
    haber_command,
    bist_command,
    yardim_command,
)

logger = logging.getLogger(__name__)

load_dotenv()

TIMEZONE = "Europe/Istanbul"


def _setup_logging() -> None:
    """Logging yapılandırmasını kurar."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _parse_args() -> argparse.Namespace:
    """Komut satırı argümanlarını parse eder.

    Returns:
        Parse edilmiş argümanlar.
    """
    parser = argparse.ArgumentParser(
        description="Telegram Günlük Finans & Haber Botu"
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Günlük özeti hemen kanala gönder ve çık",
    )
    return parser.parse_args()


async def _daily_job_callback(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """JobQueue tarafından çağrılan günlük özet görevi.

    Args:
        context: Telegram bot context'i.
    """
    logger.info("Zamanlanmış günlük özet tetiklendi")
    try:
        await run_daily_summary(context.bot)
    except Exception as exc:
        logger.error("Zamanlanmış görev hatası: %s", exc)


async def _send_now() -> None:
    """Özeti hemen kanala gönderip çıkar."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN ortam değişkeni tanımlı değil")
    bot = Bot(token=token)
    await run_daily_summary(bot)


def main() -> None:
    """Ana giriş noktası.

    --now ile çalıştırılırsa özeti anında kanala gönderip çıkar.
    Argümansız çalıştırılırsa komut dinleme + scheduler modunda başlar.
    """
    _setup_logging()
    args = _parse_args()

    if args.now:
        logger.info("Manuel tetikleme — günlük özet gönderiliyor...")
        asyncio.run(_send_now())
        logger.info("Manuel gönderim tamamlandı")
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN ortam değişkeni tanımlı değil")
        return

    logger.info("Bot başlatılıyor...")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("ozet", ozet_command))
    app.add_handler(CommandHandler("doviz", doviz_command))
    app.add_handler(CommandHandler("altin", altin_command))
    app.add_handler(CommandHandler("kripto", kripto_command))
    app.add_handler(CommandHandler("haber", haber_command))
    app.add_handler(CommandHandler("bist", bist_command))
    app.add_handler(CommandHandler("yardim", yardim_command))
    app.add_handler(CommandHandler("start", yardim_command))
    app.add_handler(CommandHandler("help", yardim_command))

    tz = ZoneInfo(TIMEZONE)
    job_time = dt_time(hour=SEND_HOUR, minute=SEND_MINUTE, tzinfo=tz)
    app.job_queue.run_daily(
        _daily_job_callback,
        time=job_time,
        name="daily_summary",
    )

    logger.info(
        "Bot başlatıldı — komutlar aktif, günlük özet %02d:%02d %s",
        SEND_HOUR,
        SEND_MINUTE,
        TIMEZONE,
    )

    try:
        app.run_polling()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Bot kapatıldı")


if __name__ == "__main__":
    main()
