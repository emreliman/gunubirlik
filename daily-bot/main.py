"""Telegram haber botu ana giriş noktası.

APScheduler ile her gün 09:00 Europe/Istanbul'da günlük özet gönderir.
Manuel tetikleme: python main.py --now
"""

import argparse
import asyncio
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from constants import SEND_HOUR, SEND_MINUTE
from scheduler.jobs import run_daily_summary
from bot.telegram_bot import send_message

logger = logging.getLogger(__name__)

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
    parser = argparse.ArgumentParser(description="Telegram Günlük Finans & Haber Botu")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Günlük özeti hemen gönder ve çık (scheduler başlatma)",
    )
    return parser.parse_args()


def _send_startup_message() -> None:
    """Bot başlatıldığında test mesajı gönderir."""
    try:
        asyncio.run(send_message("Bot başladı ✅"))
        logger.info("Başlangıç mesajı gönderildi")
    except Exception as exc:
        logger.error("Başlangıç mesajı gönderilemedi: %s", exc)


def main() -> None:
    """Ana giriş noktası.

    --now ile çalıştırılırsa özeti anında gönderip çıkar.
    Argümansız çalıştırılırsa scheduler modunda başlar.
    """
    _setup_logging()
    args = _parse_args()

    if args.now:
        logger.info("Manuel tetikleme — günlük özet gönderiliyor...")
        run_daily_summary()
        logger.info("Manuel gönderim tamamlandı")
        return

    logger.info("Bot başlatılıyor...")
    _send_startup_message()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_daily_summary,
        trigger=CronTrigger(
            hour=SEND_HOUR,
            minute=SEND_MINUTE,
            timezone=TIMEZONE,
        ),
        id="daily_summary",
        name="Günlük Özet",
    )

    logger.info(
        "Scheduler başlatıldı — her gün %02d:%02d %s",
        SEND_HOUR,
        SEND_MINUTE,
        TIMEZONE,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Bot kapatıldı")


if __name__ == "__main__":
    main()
