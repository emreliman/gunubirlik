"""Zamanlı görev tanımları.

APScheduler / JobQueue tarafından tetiklenen günlük özet gönderme görevi.
"""

import logging

from telegram import Bot

from constants import (
    GOLD_TICKER,
    SILVER_TICKER,
    USDTRY_TICKER,
    EURTRY_TICKER,
    TROY_OUNCE_TO_GRAM,
)
from data.finance import (
    get_gold_price_try,
    get_silver_price_try,
    get_exchange_rates,
    get_bist100,
    get_previous_close,
    get_us_markets,
)
from data.crypto import get_crypto_prices
from data.news import get_news
from bot.formatter import format_message
from bot.telegram_bot import send_to_channel

logger = logging.getLogger(__name__)

_DEFAULT_FINANCE_DATA: dict = {
    "gold_try": 0.0,
    "gold_prev": 0.0,
    "silver_try": 0.0,
    "silver_prev": 0.0,
    "usd": 0.0,
    "usd_prev": 0.0,
    "eur": 0.0,
    "eur_prev": 0.0,
    "bist100": {"price": 0.0, "change_pct": 0.0},
    "us_markets": {},
}


def _collect_finance_data() -> dict | None:
    """Finans verilerini toplar ve formatter'ın beklediği dict'e dönüştürür.

    Returns:
        Finans verileri dict'i veya hata durumunda None.
    """
    try:
        gold_try = get_gold_price_try()
        silver_try = get_silver_price_try()
        rates = get_exchange_rates()
        bist = get_bist100()

        gold_prev_usd = get_previous_close(GOLD_TICKER)
        silver_prev_usd = get_previous_close(SILVER_TICKER)
        usd_prev = get_previous_close(USDTRY_TICKER)
        eur_prev = get_previous_close(EURTRY_TICKER)

        gold_prev_try = (gold_prev_usd * usd_prev) / TROY_OUNCE_TO_GRAM
        silver_prev_try = (silver_prev_usd * usd_prev) / TROY_OUNCE_TO_GRAM

        try:
            us_markets = get_us_markets()
        except Exception as exc:
            logger.error("ABD borsa verileri alınamadı: %s", exc)
            us_markets = {}

        finance_data = {
            "gold_try": gold_try,
            "gold_prev": gold_prev_try,
            "silver_try": silver_try,
            "silver_prev": silver_prev_try,
            "usd": rates["USD"],
            "usd_prev": usd_prev,
            "eur": rates["EUR"],
            "eur_prev": eur_prev,
            "bist100": bist,
            "us_markets": us_markets,
        }
        logger.info("Finans verileri toplandı")
        return finance_data
    except Exception as exc:
        logger.error("Finans verileri alınamadı: %s", exc)
        return None


def _collect_crypto_data() -> dict | None:
    """Kripto verilerini toplar.

    Returns:
        Kripto verileri dict'i veya hata durumunda None.
    """
    try:
        crypto_data = get_crypto_prices()
        logger.info("Kripto verileri toplandı")
        return crypto_data
    except Exception as exc:
        logger.error("Kripto verileri alınamadı: %s", exc)
        return None


def _collect_news_data() -> list[dict]:
    """Haber verilerini toplar.

    Returns:
        Haber listesi (hata durumunda boş liste).
    """
    try:
        news_data = get_news()
        logger.info("Haber verileri toplandı")
        return news_data
    except Exception as exc:
        logger.error("Haber verileri alınamadı: %s", exc)
        return []


async def run_daily_summary(bot: Bot) -> None:
    """Günlük özet mesajını oluşturup Telegram kanalına gönderir.

    Args:
        bot: Telegram Bot instance'ı.

    Adımlar:
        1. Finans verisi çek
        2. Kripto verisi çek
        3. Haber verisi çek
        4. Mesajı formatla
        5. Kanala gönder

    Herhangi bir veri kaynağı hata verirse diğerlerine devam eder.
    Tüm kaynaklar başarısız olursa mesaj gönderilmez.
    """
    logger.info("Günlük özet görevi başladı")

    finance_data = _collect_finance_data()
    crypto_data = _collect_crypto_data()
    news_data = _collect_news_data()

    if finance_data is None and crypto_data is None and not news_data:
        logger.error(
            "Hiçbir veri kaynağından veri alınamadı, mesaj gönderilmiyor"
        )
        return

    effective_finance = (
        finance_data if finance_data is not None else _DEFAULT_FINANCE_DATA
    )
    effective_crypto = crypto_data if crypto_data is not None else {}

    try:
        message = format_message(
            effective_finance, effective_crypto, news_data
        )
        logger.info("Mesaj formatlandı (%d karakter)", len(message))
    except Exception as exc:
        logger.error("Mesaj formatlanamadı: %s", exc)
        return

    try:
        await send_to_channel(bot, message)
        logger.info("Günlük özet kanala gönderildi")
    except Exception as exc:
        logger.error("Mesaj kanala gönderilemedi: %s", exc)

    logger.info("Günlük özet görevi tamamlandı")
