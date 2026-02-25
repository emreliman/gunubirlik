"""Telegram bot mesaj gönderme modülü.

python-telegram-bot kütüphanesi ile async mesaj gönderir.
Token ve chat_id .env dosyasından okunur.
"""

import logging
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import InvalidToken, NetworkError, TelegramError

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_MAX_LENGTH = 4096


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class TelegramAuthError(Exception):
    """Token geçersiz veya yetkilendirme başarısız."""


class TelegramSendError(Exception):
    """Mesaj gönderimi sırasında oluşan hata."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_bot() -> Bot:
    """Ortam değişkenlerinden Bot instance'ı oluşturur.

    Returns:
        Yapılandırılmış Bot nesnesi.

    Raises:
        TelegramAuthError: Token tanımlı değilse.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise TelegramAuthError("TELEGRAM_BOT_TOKEN ortam değişkeni tanımlı değil")
    return Bot(token=token)


def _get_chat_id() -> str:
    """Ortam değişkenlerinden chat_id okur.

    Returns:
        Telegram chat ID.

    Raises:
        TelegramSendError: Chat ID tanımlı değilse.
    """
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise TelegramSendError("TELEGRAM_CHAT_ID ortam değişkeni tanımlı değil")
    return chat_id


def _split_message(text: str) -> list[str]:
    """Uzun mesajı Telegram limitine uygun parçalara böler.

    Satır sonu sınırlarında böler, haber ortasında kesmez.

    Args:
        text: Bölünecek mesaj metni.

    Returns:
        Her biri TELEGRAM_MAX_LENGTH'i aşmayan parçalar listesi.
    """
    if len(text) <= TELEGRAM_MAX_LENGTH:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= TELEGRAM_MAX_LENGTH:
            chunks.append(remaining)
            break

        split_pos = remaining.rfind("\n", 0, TELEGRAM_MAX_LENGTH)
        if split_pos == -1:
            split_pos = TELEGRAM_MAX_LENGTH

        chunks.append(remaining[:split_pos + 1])
        remaining = remaining[split_pos + 1:]

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _get_channel_id() -> str:
    """Ortam değişkenlerinden channel ID okur.

    Returns:
        Telegram kanal ID'si.

    Raises:
        TelegramSendError: Channel ID tanımlı değilse.
    """
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not channel_id:
        raise TelegramSendError(
            "TELEGRAM_CHANNEL_ID ortam değişkeni tanımlı değil"
        )
    return channel_id


async def send_message(text: str) -> bool:
    """Telegram'a mesaj gönderir. Uzun mesajları otomatik böler.

    Args:
        text: Gönderilecek mesaj metni.

    Returns:
        Başarılıysa True.

    Raises:
        TelegramAuthError: Token geçersizse.
        TelegramSendError: Gönderim başarısızsa.
    """
    bot = _get_bot()
    chat_id = _get_chat_id()
    chunks = _split_message(text)

    try:
        for chunk in chunks:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode="MarkdownV2",
            )
            logger.info("Mesaj parçası gönderildi (%d karakter)", len(chunk))
    except InvalidToken as exc:
        logger.error("Telegram token geçersiz: %s", exc)
        raise TelegramAuthError("Bot token geçersiz") from exc
    except (NetworkError, TelegramError) as exc:
        logger.error("Telegram gönderim hatası: %s", exc)
        raise TelegramSendError(f"Mesaj gönderilemedi: {exc}") from exc

    logger.info("Toplam %d parça başarıyla gönderildi", len(chunks))
    return True


async def send_to_channel(bot: Bot, text: str) -> bool:
    """Telegram kanalına mesaj gönderir. Uzun mesajları otomatik böler.

    Args:
        bot: Telegram Bot instance'ı.
        text: Gönderilecek mesaj metni.

    Returns:
        Başarılıysa True.

    Raises:
        TelegramAuthError: Token geçersizse.
        TelegramSendError: Gönderim başarısızsa.
    """
    channel_id = _get_channel_id()
    chunks = _split_message(text)

    try:
        for chunk in chunks:
            await bot.send_message(
                chat_id=channel_id,
                text=chunk,
                parse_mode="MarkdownV2",
            )
            logger.info(
                "Kanal mesaj parçası gönderildi (%d karakter)", len(chunk)
            )
    except InvalidToken as exc:
        logger.error("Telegram token geçersiz: %s", exc)
        raise TelegramAuthError("Bot token geçersiz") from exc
    except (NetworkError, TelegramError) as exc:
        logger.error("Kanal gönderim hatası: %s", exc)
        raise TelegramSendError(f"Kanala mesaj gönderilemedi: {exc}") from exc

    logger.info("Toplam %d parça kanala gönderildi", len(chunks))
    return True
