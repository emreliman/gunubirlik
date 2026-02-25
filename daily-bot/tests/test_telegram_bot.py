import pytest
from unittest.mock import AsyncMock, patch
from telegram.error import InvalidToken, NetworkError

from bot.telegram_bot import (
    send_message,
    send_to_channel,
    TelegramAuthError,
    TelegramSendError,
    _split_message,
    _get_channel_id,
    TELEGRAM_MAX_LENGTH,
)


# ---------------------------------------------------------------------------
# _split_message (sync helper)
# ---------------------------------------------------------------------------

class TestSplitMessage:
    def test_short_message_returns_single_chunk(self):
        text = "Kısa mesaj"
        chunks = _split_message(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_message_splits_into_multiple_chunks(self):
        line = "Haber satırı\n"
        text = line * 500
        chunks = _split_message(text)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= TELEGRAM_MAX_LENGTH

    def test_splits_on_newline_boundary(self):
        part_a = "A satırı\n" * 300
        part_b = "B satırı\n" * 300
        text = part_a + part_b
        chunks = _split_message(text)
        for chunk in chunks:
            assert not chunk.startswith("\n")

    def test_reassembled_chunks_equal_original(self):
        line = "Satır içeriği\n"
        text = line * 400
        chunks = _split_message(text)
        reassembled = "".join(chunks)
        assert reassembled == text


# ---------------------------------------------------------------------------
# send_message (async)
# ---------------------------------------------------------------------------

MOCK_CHAT_ID = "123456789"


class TestSendMessage:
    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_chat_id", return_value=MOCK_CHAT_ID)
    @patch("bot.telegram_bot._get_bot")
    async def test_successful_send_returns_true(self, mock_get_bot, mock_chat):
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot

        result = await send_message("Merhaba dünya")

        assert result is True
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_chat_id", return_value=MOCK_CHAT_ID)
    @patch("bot.telegram_bot._get_bot")
    async def test_raises_auth_error_on_invalid_token(self, mock_get_bot, mock_chat):
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = InvalidToken("Invalid token")
        mock_get_bot.return_value = mock_bot

        with pytest.raises(TelegramAuthError):
            await send_message("Test")

    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_chat_id", return_value=MOCK_CHAT_ID)
    @patch("bot.telegram_bot._get_bot")
    async def test_raises_send_error_on_network_failure(self, mock_get_bot, mock_chat):
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = NetworkError("Connection failed")
        mock_get_bot.return_value = mock_bot

        with pytest.raises(TelegramSendError):
            await send_message("Test")

    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_chat_id", return_value=MOCK_CHAT_ID)
    @patch("bot.telegram_bot._get_bot")
    async def test_long_message_sent_in_multiple_parts(self, mock_get_bot, mock_chat):
        mock_bot = AsyncMock()
        mock_get_bot.return_value = mock_bot

        long_text = "Uzun satır\n" * 500

        result = await send_message(long_text)

        assert result is True
        assert mock_bot.send_message.call_count >= 2


# ---------------------------------------------------------------------------
# _get_channel_id
# ---------------------------------------------------------------------------

MOCK_CHANNEL_ID = "@test_channel"


class TestGetChannelId:
    @patch.dict("os.environ", {"TELEGRAM_CHANNEL_ID": MOCK_CHANNEL_ID})
    def test_returns_channel_id(self):
        result = _get_channel_id()
        assert result == MOCK_CHANNEL_ID

    @patch.dict("os.environ", {"TELEGRAM_CHANNEL_ID": ""})
    def test_raises_on_empty_channel_id(self):
        with pytest.raises(TelegramSendError):
            _get_channel_id()


# ---------------------------------------------------------------------------
# send_to_channel
# ---------------------------------------------------------------------------


class TestSendToChannel:
    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_channel_id", return_value=MOCK_CHANNEL_ID)
    async def test_successful_send_returns_true(self, mock_channel):
        mock_bot = AsyncMock()

        result = await send_to_channel(mock_bot, "Kanal mesajı")

        assert result is True
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == MOCK_CHANNEL_ID
        assert call_kwargs["parse_mode"] == "MarkdownV2"

    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_channel_id", return_value=MOCK_CHANNEL_ID)
    async def test_raises_auth_error_on_invalid_token(self, mock_channel):
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = InvalidToken("Invalid token")

        with pytest.raises(TelegramAuthError):
            await send_to_channel(mock_bot, "Test")

    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_channel_id", return_value=MOCK_CHANNEL_ID)
    async def test_raises_send_error_on_network_failure(self, mock_channel):
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = NetworkError("Connection failed")

        with pytest.raises(TelegramSendError):
            await send_to_channel(mock_bot, "Test")

    @pytest.mark.asyncio
    @patch("bot.telegram_bot._get_channel_id", return_value=MOCK_CHANNEL_ID)
    async def test_long_message_splits(self, mock_channel):
        mock_bot = AsyncMock()
        long_text = "Uzun satır\n" * 500

        result = await send_to_channel(mock_bot, long_text)

        assert result is True
        assert mock_bot.send_message.call_count >= 2
