"""bot.commands modülü testleri."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.commands import (
    doviz_command,
    altin_command,
    kripto_command,
    haber_command,
    bist_command,
    yardim_command,
    ozet_command,
    YARDIM_METNI,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

ADMIN_ID = 123456


def _make_update(user_id: int = ADMIN_ID) -> MagicMock:
    """Komut handler'ları için Update mock'u oluşturur."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.message.reply_text = AsyncMock()
    return update


def _make_context() -> MagicMock:
    """Handler context mock'u oluşturur."""
    context = MagicMock()
    context.bot = AsyncMock()
    return context


# ---------------------------------------------------------------------------
# /doviz
# ---------------------------------------------------------------------------


class TestDovizCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands.format_forex_only", return_value="formatted_msg")
    @patch("bot.commands.get_previous_close", return_value=32.0)
    @patch("bot.commands.get_exchange_rates", return_value={"USD": 32.5, "EUR": 35.1})
    async def test_sends_forex_to_channel(
        self, mock_rates, mock_prev, mock_fmt, mock_send
    ):
        update = _make_update()
        context = _make_context()

        await doviz_command(update, context)

        mock_rates.assert_called_once()
        mock_fmt.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "formatted_msg")

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.get_exchange_rates", side_effect=Exception("API down"))
    async def test_replies_error_on_failure(self, mock_rates):
        update = _make_update()
        context = _make_context()

        await doviz_command(update, context)

        error_call = update.message.reply_text.call_args_list[-1]
        assert "❌" in error_call[0][0]


# ---------------------------------------------------------------------------
# /altin
# ---------------------------------------------------------------------------


class TestAltinCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands.format_metals_only", return_value="metals_msg")
    @patch("bot.commands.get_previous_close", return_value=100.0)
    @patch("bot.commands.get_silver_price_try", return_value=28.5)
    @patch("bot.commands.get_gold_price_try", return_value=2057.5)
    async def test_sends_metals_to_channel(
        self, mock_gold, mock_silver, mock_prev, mock_fmt, mock_send
    ):
        update = _make_update()
        context = _make_context()

        await altin_command(update, context)

        mock_gold.assert_called_once()
        mock_silver.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "metals_msg")

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.get_gold_price_try", side_effect=Exception("API down"))
    async def test_replies_error_on_failure(self, mock_gold):
        update = _make_update()
        context = _make_context()

        await altin_command(update, context)

        error_call = update.message.reply_text.call_args_list[-1]
        assert "❌" in error_call[0][0]


# ---------------------------------------------------------------------------
# /kripto
# ---------------------------------------------------------------------------


class TestKriptoCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands.format_crypto_only", return_value="crypto_msg")
    @patch(
        "bot.commands.get_crypto_prices",
        return_value={
            "bitcoin": {"price_usd": 65000, "price_try": 2112500, "change_24h": 2.5}
        },
    )
    async def test_sends_crypto_to_channel(
        self, mock_crypto, mock_fmt, mock_send
    ):
        update = _make_update()
        context = _make_context()

        await kripto_command(update, context)

        mock_crypto.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "crypto_msg")


# ---------------------------------------------------------------------------
# /haber
# ---------------------------------------------------------------------------


class TestHaberCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands.format_news_only", return_value="news_msg")
    @patch(
        "bot.commands.get_news",
        return_value=[{"title": "Test", "source": "X", "link": "http://x.com"}],
    )
    async def test_sends_news_to_channel(
        self, mock_news, mock_fmt, mock_send
    ):
        update = _make_update()
        context = _make_context()

        await haber_command(update, context)

        mock_news.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "news_msg")


# ---------------------------------------------------------------------------
# /bist
# ---------------------------------------------------------------------------


class TestBistCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands.format_bist_only", return_value="bist_msg")
    @patch(
        "bot.commands.get_us_markets",
        return_value={"sp500": {"price": 5987, "change_pct": 0.45}},
    )
    @patch(
        "bot.commands.get_bist100",
        return_value={"price": 9850, "change_pct": 0.75},
    )
    async def test_sends_bist_to_channel(
        self, mock_bist, mock_us, mock_fmt, mock_send
    ):
        update = _make_update()
        context = _make_context()

        await bist_command(update, context)

        mock_bist.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "bist_msg")

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands.format_bist_only", return_value="bist_msg")
    @patch(
        "bot.commands.get_us_markets",
        side_effect=Exception("US API down"),
    )
    @patch(
        "bot.commands.get_bist100",
        return_value={"price": 9850, "change_pct": 0.75},
    )
    async def test_continues_when_us_markets_fail(
        self, mock_bist, mock_us, mock_fmt, mock_send
    ):
        update = _make_update()
        context = _make_context()

        await bist_command(update, context)

        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# /yardim
# ---------------------------------------------------------------------------


class TestYardimCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_sends_help_text_to_admin(self):
        update = _make_update()
        context = _make_context()

        await yardim_command(update, context)

        update.message.reply_text.assert_called_once_with(YARDIM_METNI)


# ---------------------------------------------------------------------------
# /ozet
# ---------------------------------------------------------------------------


class TestOzetCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.run_daily_summary", new_callable=AsyncMock)
    async def test_triggers_full_summary(self, mock_summary):
        update = _make_update()
        context = _make_context()

        await ozet_command(update, context)

        mock_summary.assert_called_once_with(context.bot)
        last_reply = update.message.reply_text.call_args_list[-1][0][0]
        assert "✅" in last_reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands.run_daily_summary",
        new_callable=AsyncMock,
        side_effect=Exception("Fail"),
    )
    async def test_replies_error_on_failure(self, mock_summary):
        update = _make_update()
        context = _make_context()

        await ozet_command(update, context)

        last_reply = update.message.reply_text.call_args_list[-1][0][0]
        assert "❌" in last_reply


# ---------------------------------------------------------------------------
# Yetkisiz erişim (tüm komutlar)
# ---------------------------------------------------------------------------


class TestUnauthorizedAccess:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_non_admin_cannot_use_doviz(self):
        update = _make_update(user_id=999999)
        context = _make_context()

        await doviz_command(update, context)

        update.message.reply_text.assert_called_once_with(
            "⛔ Bu komutu kullanma yetkiniz yok."
        )

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_non_admin_cannot_use_ozet(self):
        update = _make_update(user_id=999999)
        context = _make_context()

        await ozet_command(update, context)

        update.message.reply_text.assert_called_once_with(
            "⛔ Bu komutu kullanma yetkiniz yok."
        )
