"""Yetkilendirme modülü.

Telegram bot komutlarını sadece yetkili kullanıcılarla sınırlar.
ADMIN_USER_IDS ortam değişkeninden virgülle ayrılmış user ID'leri okur.
"""

import logging
import os
from functools import wraps
from typing import Callable

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

load_dotenv()


def _load_admin_ids() -> list[int]:
    """ADMIN_USER_IDS ortam değişkenini parse eder.

    Returns:
        Yetkili kullanıcı ID'lerinin listesi.
    """
    raw = os.getenv("ADMIN_USER_IDS", "")
    return [int(uid.strip()) for uid in raw.split(",") if uid.strip()]


ADMIN_USER_IDS: list[int] = _load_admin_ids()


def admin_only(func: Callable) -> Callable:
    """Sadece ADMIN_USER_IDS'deki kullanıcılara izin veren decorator.

    Yetkisiz kullanıcılara uyarı mesajı gönderir.

    Args:
        func: Sarmalanacak async handler fonksiyonu.

    Returns:
        Yetki kontrolü eklenmiş handler.
    """

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        if user_id not in ADMIN_USER_IDS:
            logger.warning("Yetkisiz erişim denemesi: user_id=%d", user_id)
            await update.message.reply_text(
                "⛔ Bu komutu kullanma yetkiniz yok."
            )
            return None
        return await func(update, context)

    return wrapper
