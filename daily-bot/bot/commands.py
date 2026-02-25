"""Telegram bot komut handler'ları.

Admin kullanıcıların özel mesajla gönderdiği komutları işler
ve sonucu Telegram kanalına gönderir.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.auth import admin_only
from bot.formatter import (
    format_metals_only,
    format_forex_only,
    format_bist_only,
    format_crypto_only,
    format_news_only,
)
from bot.telegram_bot import send_to_channel
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
from constants import (
    GOLD_TICKER,
    SILVER_TICKER,
    USDTRY_TICKER,
    EURTRY_TICKER,
    TROY_OUNCE_TO_GRAM,
)
from scheduler.jobs import run_daily_summary

logger = logging.getLogger(__name__)

YARDIM_METNI = (
    "📋 Kullanılabilir Komutlar\n\n"
    "/ozet — Tam günlük özeti kanala gönder\n"
    "/doviz — Döviz kurları\n"
    "/altin — Altın & Gümüş\n"
    "/kripto — Kripto paralar\n"
    "/haber — Son haberler\n"
    "/bist — Borsa (BIST-100 + ABD)\n"
    "/yardim — Bu mesaj"
)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


@admin_only
async def ozet_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Tam günlük özeti kanala gönderir."""
    await update.message.reply_text("📊 Günlük özet hazırlanıyor...")
    try:
        await run_daily_summary(context.bot)
        await update.message.reply_text("✅ Günlük özet kanala gönderildi.")
    except Exception as exc:
        logger.error("Özet komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


@admin_only
async def doviz_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Döviz kurlarını kanala gönderir."""
    try:
        rates = get_exchange_rates()
        usd_prev = get_previous_close(USDTRY_TICKER)
        eur_prev = get_previous_close(EURTRY_TICKER)
        data = {
            "usd": rates["USD"],
            "usd_prev": usd_prev,
            "eur": rates["EUR"],
            "eur_prev": eur_prev,
        }
        message = format_forex_only(data)
        await send_to_channel(context.bot, message)
        await update.message.reply_text("✅ Döviz bilgisi kanala gönderildi.")
    except Exception as exc:
        logger.error("Döviz komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


@admin_only
async def altin_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Altın ve gümüş fiyatlarını kanala gönderir."""
    try:
        gold_try = get_gold_price_try()
        silver_try = get_silver_price_try()
        usd_prev = get_previous_close(USDTRY_TICKER)
        gold_prev_usd = get_previous_close(GOLD_TICKER)
        silver_prev_usd = get_previous_close(SILVER_TICKER)
        gold_prev_try = (gold_prev_usd * usd_prev) / TROY_OUNCE_TO_GRAM
        silver_prev_try = (silver_prev_usd * usd_prev) / TROY_OUNCE_TO_GRAM
        data = {
            "gold_try": gold_try,
            "gold_prev": gold_prev_try,
            "silver_try": silver_try,
            "silver_prev": silver_prev_try,
        }
        message = format_metals_only(data)
        await send_to_channel(context.bot, message)
        await update.message.reply_text(
            "✅ Altın & Gümüş bilgisi kanala gönderildi."
        )
    except Exception as exc:
        logger.error("Altın komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


@admin_only
async def kripto_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Kripto para fiyatlarını kanala gönderir."""
    try:
        crypto_data = get_crypto_prices()
        message = format_crypto_only(crypto_data)
        await send_to_channel(context.bot, message)
        await update.message.reply_text(
            "✅ Kripto bilgisi kanala gönderildi."
        )
    except Exception as exc:
        logger.error("Kripto komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


@admin_only
async def haber_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Son haberleri kanala gönderir."""
    try:
        news_data = get_news()
        message = format_news_only(news_data)
        await send_to_channel(context.bot, message)
        await update.message.reply_text("✅ Haberler kanala gönderildi.")
    except Exception as exc:
        logger.error("Haber komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


@admin_only
async def bist_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Borsa bilgilerini kanala gönderir."""
    try:
        bist = get_bist100()
        try:
            us_markets = get_us_markets()
        except Exception as exc:
            logger.error("ABD borsa verileri alınamadı: %s", exc)
            us_markets = {}
        data = {"bist100": bist, "us_markets": us_markets}
        message = format_bist_only(data)
        await send_to_channel(context.bot, message)
        await update.message.reply_text(
            "✅ Borsa bilgisi kanala gönderildi."
        )
    except Exception as exc:
        logger.error("BIST komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


@admin_only
async def yardim_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Yardım mesajını admin'e gönderir (kanala değil, DM olarak)."""
    await update.message.reply_text(YARDIM_METNI)
