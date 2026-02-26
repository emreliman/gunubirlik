"""bot.commands modülü testleri."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.commands import (
    doviz_command,
    altin_command,
    kripto_command,
    haber_command,
    bist_command,
    grafik_command,
    yardim_command,
    ozet_command,
    dm_command,
    twitter_command,
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
    update.message.reply_photo = AsyncMock()
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
    @patch("bot.commands._fetch_forex_message", return_value="formatted_msg")
    async def test_sends_forex_to_channel(self, mock_fetch, mock_send):
        update = _make_update()
        context = _make_context()

        await doviz_command(update, context)

        mock_fetch.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "formatted_msg")

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_forex_message", side_effect=Exception("API down"))
    async def test_replies_error_on_failure(self, mock_fetch):
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
    @patch("bot.commands._fetch_metals_message", return_value="metals_msg")
    async def test_sends_metals_to_channel(self, mock_fetch, mock_send):
        update = _make_update()
        context = _make_context()

        await altin_command(update, context)

        mock_fetch.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "metals_msg")

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_metals_message", side_effect=Exception("API down"))
    async def test_replies_error_on_failure(self, mock_fetch):
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
    @patch("bot.commands._fetch_crypto_message", return_value="crypto_msg")
    async def test_sends_crypto_to_channel(self, mock_fetch, mock_send):
        update = _make_update()
        context = _make_context()

        await kripto_command(update, context)

        mock_fetch.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "crypto_msg")


# ---------------------------------------------------------------------------
# /haber
# ---------------------------------------------------------------------------


class TestHaberCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands._fetch_news_message", return_value="news_msg")
    async def test_sends_news_to_channel(self, mock_fetch, mock_send):
        update = _make_update()
        context = _make_context()

        await haber_command(update, context)

        mock_fetch.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "news_msg")


# ---------------------------------------------------------------------------
# /bist
# ---------------------------------------------------------------------------


class TestBistCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands.send_to_channel", new_callable=AsyncMock, return_value=True)
    @patch("bot.commands._fetch_bist_message", return_value="bist_msg")
    async def test_sends_bist_to_channel(self, mock_fetch, mock_send):
        update = _make_update()
        context = _make_context()

        await bist_command(update, context)

        mock_fetch.assert_called_once()
        mock_send.assert_called_once_with(context.bot, "bist_msg")

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_bist_message", side_effect=Exception("API down"))
    async def test_replies_error_on_failure(self, mock_fetch):
        update = _make_update()
        context = _make_context()

        await bist_command(update, context)

        error_call = update.message.reply_text.call_args_list[-1]
        assert "❌" in error_call[0][0]


# ---------------------------------------------------------------------------
# /grafik
# ---------------------------------------------------------------------------


class TestGrafikCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands.send_photo_to_channel",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch(
        "bot.commands.generate_asset_chart_png",
        return_value=(b"png-bytes", "Grafik notu"),
    )
    async def test_sends_chart_to_channel(self, mock_generate, mock_send):
        update = _make_update()
        context = _make_context()
        context.args = ["btc", "1a"]

        await grafik_command(update, context)

        mock_generate.assert_called_once_with("btc", "1a")
        mock_send.assert_called_once_with(
            context.bot, b"png-bytes", "Grafik notu"
        )
        last_reply = update.message.reply_text.call_args_list[-1][0][0]
        assert "✅" in last_reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_shows_usage_when_args_missing(self):
        update = _make_update()
        context = _make_context()
        context.args = ["btc"]

        await grafik_command(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert "Kullanım" in reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands.generate_asset_chart_png",
        side_effect=ValueError("Geçersiz varlık"),
    )
    async def test_shows_validation_error(self, mock_generate):
        update = _make_update()
        context = _make_context()
        context.args = ["abc", "1a"]

        await grafik_command(update, context)

        mock_generate.assert_called_once()
        reply = update.message.reply_text.call_args[0][0]
        assert "❓" in reply

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
# /dm
# ---------------------------------------------------------------------------


class TestDmCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_forex_message", return_value="dm_forex_msg")
    async def test_dm_doviz_replies_to_admin(self, mock_fetch):
        update = _make_update()
        context = _make_context()
        context.args = ["doviz"]

        await dm_command(update, context)

        mock_fetch.assert_called_once()
        update.message.reply_text.assert_called_once_with(
            "dm_forex_msg", parse_mode="MarkdownV2"
        )

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_metals_message", return_value="dm_metals_msg")
    async def test_dm_altin_replies_to_admin(self, mock_fetch):
        update = _make_update()
        context = _make_context()
        context.args = ["altin"]

        await dm_command(update, context)

        mock_fetch.assert_called_once()
        update.message.reply_text.assert_called_once_with(
            "dm_metals_msg", parse_mode="MarkdownV2"
        )

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_crypto_message", return_value="dm_crypto_msg")
    async def test_dm_kripto_replies_to_admin(self, mock_fetch):
        update = _make_update()
        context = _make_context()
        context.args = ["kripto"]

        await dm_command(update, context)

        update.message.reply_text.assert_called_once_with(
            "dm_crypto_msg", parse_mode="MarkdownV2"
        )

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_dm_no_args_shows_usage(self):
        update = _make_update()
        context = _make_context()
        context.args = []

        await dm_command(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert "Kullanım" in reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_dm_unknown_subcommand_shows_error(self):
        update = _make_update()
        context = _make_context()
        context.args = ["bilmiyorum"]

        await dm_command(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert "Bilinmeyen komut" in reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands._fetch_forex_message",
        side_effect=Exception("API error"),
    )
    async def test_dm_replies_error_on_failure(self, mock_fetch):
        update = _make_update()
        context = _make_context()
        context.args = ["doviz"]

        await dm_command(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert "❌" in reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch("bot.commands._fetch_forex_message", return_value="msg")
    async def test_dm_does_not_send_to_channel(self, mock_fetch):
        """DM komutu kanala mesaj göndermemeli."""
        update = _make_update()
        context = _make_context()
        context.args = ["doviz"]

        with patch(
            "bot.commands.send_to_channel", new_callable=AsyncMock
        ) as mock_send:
            await dm_command(update, context)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands.generate_asset_chart_png",
        return_value=(b"png-bytes", "Grafik aciklamasi"),
    )
    async def test_dm_grafik_replies_photo_to_admin(self, mock_generate):
        update = _make_update()
        context = _make_context()
        context.args = ["grafik", "btc", "1a"]

        await dm_command(update, context)

        mock_generate.assert_called_once_with("btc", "1a")
        update.message.reply_photo.assert_called_once()
        photo_arg = update.message.reply_photo.call_args.kwargs["photo"]
        caption_arg = update.message.reply_photo.call_args.kwargs["caption"]
        assert photo_arg is not None
        assert caption_arg == "Grafik aciklamasi"

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_dm_grafik_usage_when_missing_args(self):
        update = _make_update()
        context = _make_context()
        context.args = ["grafik", "btc"]

        await dm_command(update, context)

        reply = update.message.reply_text.call_args[0][0]
        assert "Kullanım" in reply


# ---------------------------------------------------------------------------
# /twitter
# ---------------------------------------------------------------------------


class TestTwitterCommand:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands._fetch_twitter_messages",
        return_value=["tweet1", "tweet2", "tweet3"],
    )
    async def test_sends_multiple_messages_to_admin(self, mock_fetch):
        update = _make_update()
        context = _make_context()

        await twitter_command(update, context)

        # reply_text should be called once for the loading message + once per tweet
        assert update.message.reply_text.call_count == 4

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands._fetch_twitter_messages",
        return_value=["tweet1", "tweet2"],
    )
    async def test_does_not_send_to_channel(self, mock_fetch):
        """Twitter komutu kanala mesaj göndermemeli."""
        update = _make_update()
        context = _make_context()

        with patch(
            "bot.commands.send_to_channel", new_callable=AsyncMock
        ) as mock_send:
            await twitter_command(update, context)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    @patch(
        "bot.commands._fetch_twitter_messages",
        side_effect=Exception("Format error"),
    )
    async def test_replies_error_on_failure(self, mock_fetch):
        update = _make_update()
        context = _make_context()

        await twitter_command(update, context)

        last_reply = update.message.reply_text.call_args_list[-1][0][0]
        assert "❌" in last_reply

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [ADMIN_ID])
    async def test_non_admin_cannot_use_twitter(self):
        update = _make_update(user_id=999999)
        context = _make_context()

        await twitter_command(update, context)

        update.message.reply_text.assert_called_once_with(
            "⛔ Bu komutu kullanma yetkiniz yok."
        )


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
