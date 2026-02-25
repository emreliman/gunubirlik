"""Telegram bot komut handler'ları.

Admin kullanıcıların özel mesajla gönderdiği komutları işler.
Kanal komutları (/doviz, /altin vb.) sonucu kanala gönderir.
DM komutu (/dm doviz, /dm altin vb.) sonucu admin'e özel gönderir.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.auth import admin_only
from bot.formatter import (
    format_message,
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
    "📢 Kanala gönder:\n"
    "/ozet — Tam günlük özet\n"
    "/doviz — Döviz kurları\n"
    "/altin — Altın & Gümüş\n"
    "/kripto — Kripto paralar\n"
    "/haber — Son haberler\n"
    "/bist — Borsa (BIST-100 + ABD)\n\n"
    "👤 Sadece bana gönder:\n"
    "/dm doviz — Döviz kurları\n"
    "/dm altin — Altın & Gümüş\n"
    "/dm kripto — Kripto paralar\n"
    "/dm haber — Son haberler\n"
    "/dm bist — Borsa\n"
    "/dm ozet — Tam günlük özet\n\n"
    "/yardim — Bu mesaj"
)


# ---------------------------------------------------------------------------
# Data fetching helpers
# ---------------------------------------------------------------------------


def _fetch_forex_message() -> str:
    """Döviz verilerini çekip formatlanmış mesaj döndürür.

    Returns:
        MarkdownV2 formatında döviz mesajı.
    """
    rates = get_exchange_rates()
    usd_prev = get_previous_close(USDTRY_TICKER)
    eur_prev = get_previous_close(EURTRY_TICKER)
    data = {
        "usd": rates["USD"],
        "usd_prev": usd_prev,
        "eur": rates["EUR"],
        "eur_prev": eur_prev,
    }
    return format_forex_only(data)


def _fetch_metals_message() -> str:
    """Altın/gümüş verilerini çekip formatlanmış mesaj döndürür.

    Returns:
        MarkdownV2 formatında altın/gümüş mesajı.
    """
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
    return format_metals_only(data)


def _fetch_crypto_message() -> str:
    """Kripto verilerini çekip formatlanmış mesaj döndürür.

    Returns:
        MarkdownV2 formatında kripto mesajı.
    """
    crypto_data = get_crypto_prices()
    return format_crypto_only(crypto_data)


def _fetch_news_message() -> str:
    """Haber verilerini çekip formatlanmış mesaj döndürür.

    Returns:
        MarkdownV2 formatında haber mesajı.
    """
    news_data = get_news()
    return format_news_only(news_data)


def _fetch_bist_message() -> str:
    """Borsa verilerini çekip formatlanmış mesaj döndürür.

    Returns:
        MarkdownV2 formatında borsa mesajı.
    """
    bist = get_bist100()
    try:
        us_markets = get_us_markets()
    except Exception as exc:
        logger.error("ABD borsa verileri alınamadı: %s", exc)
        us_markets = {}
    data = {"bist100": bist, "us_markets": us_markets}
    return format_bist_only(data)


def _fetch_summary_message() -> str:
    """Tam günlük özet mesajını oluşturur (göndermez).

    Returns:
        MarkdownV2 formatında tam özet mesajı.
    """
    from scheduler.jobs import (
        _collect_finance_data,
        _collect_crypto_data,
        _collect_news_data,
        _DEFAULT_FINANCE_DATA,
    )

    finance = _collect_finance_data()
    crypto = _collect_crypto_data()
    news = _collect_news_data()

    eff_finance = finance if finance is not None else _DEFAULT_FINANCE_DATA
    eff_crypto = crypto if crypto is not None else {}

    return format_message(eff_finance, eff_crypto, news)


_DM_FETCHER_MAP: dict[str, str] = {
    "doviz": "_fetch_forex_message",
    "altin": "_fetch_metals_message",
    "kripto": "_fetch_crypto_message",
    "haber": "_fetch_news_message",
    "bist": "_fetch_bist_message",
    "ozet": "_fetch_summary_message",
}


# ---------------------------------------------------------------------------
# Channel command handlers
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
        message = _fetch_forex_message()
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
        message = _fetch_metals_message()
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
        message = _fetch_crypto_message()
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
        message = _fetch_news_message()
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
        message = _fetch_bist_message()
        await send_to_channel(context.bot, message)
        await update.message.reply_text(
            "✅ Borsa bilgisi kanala gönderildi."
        )
    except Exception as exc:
        logger.error("BIST komutu hatası: %s", exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


# ---------------------------------------------------------------------------
# DM command handler
# ---------------------------------------------------------------------------


@admin_only
async def dm_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Veriyi kanala değil, admin'e özel mesaj olarak gönderir.

    Kullanım: /dm <komut>
    Örnek: /dm doviz, /dm kripto, /dm ozet
    """
    if not context.args:
        available = ", ".join(_DM_FETCHER_MAP.keys())
        await update.message.reply_text(
            f"Kullanım: /dm <komut>\nKomutlar: {available}"
        )
        return

    sub = context.args[0].lower()
    fetcher_name = _DM_FETCHER_MAP.get(sub)

    if fetcher_name is None:
        available = ", ".join(_DM_FETCHER_MAP.keys())
        await update.message.reply_text(
            f"❓ Bilinmeyen komut: {sub}\nKomutlar: {available}"
        )
        return

    try:
        fetcher = globals()[fetcher_name]
        message = fetcher()
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except Exception as exc:
        logger.error("DM komutu hatası (%s): %s", sub, exc)
        await update.message.reply_text(f"❌ Hata oluştu: {exc}")


# ---------------------------------------------------------------------------
# Help command handler
# ---------------------------------------------------------------------------


@admin_only
async def yardim_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Yardım mesajını admin'e gönderir (kanala değil, DM olarak)."""
    await update.message.reply_text(YARDIM_METNI)
