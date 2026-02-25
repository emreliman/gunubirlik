"""bot.auth modülü testleri."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.auth import admin_only


# ---------------------------------------------------------------------------
# admin_only decorator
# ---------------------------------------------------------------------------


class TestAdminOnly:
    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [123456])
    async def test_allows_admin_user(self):
        @admin_only
        async def handler(update, context):
            return "OK"

        update = MagicMock()
        update.effective_user.id = 123456
        context = MagicMock()

        result = await handler(update, context)
        assert result == "OK"

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [123456])
    async def test_rejects_non_admin_user(self):
        @admin_only
        async def handler(update, context):
            return "OK"

        update = MagicMock()
        update.effective_user.id = 999999
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        result = await handler(update, context)

        assert result is None
        update.message.reply_text.assert_called_once_with(
            "⛔ Bu komutu kullanma yetkiniz yok."
        )

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [])
    async def test_rejects_when_no_admins_configured(self):
        @admin_only
        async def handler(update, context):
            return "OK"

        update = MagicMock()
        update.effective_user.id = 123456
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        result = await handler(update, context)
        assert result is None

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [111, 222, 333])
    async def test_allows_any_admin_in_list(self):
        @admin_only
        async def handler(update, context):
            return "OK"

        for uid in [111, 222, 333]:
            update = MagicMock()
            update.effective_user.id = uid
            context = MagicMock()
            result = await handler(update, context)
            assert result == "OK"

    @pytest.mark.asyncio
    @patch("bot.auth.ADMIN_USER_IDS", [123456])
    async def test_preserves_function_name(self):
        @admin_only
        async def my_handler(update, context):
            pass

        assert my_handler.__name__ == "my_handler"


class TestLoadAdminIds:
    @patch.dict("os.environ", {"ADMIN_USER_IDS": "111,222,333"})
    def test_parses_comma_separated_ids(self):
        from bot.auth import _load_admin_ids

        result = _load_admin_ids()
        assert result == [111, 222, 333]

    @patch.dict("os.environ", {"ADMIN_USER_IDS": " 111 , 222 "})
    def test_strips_whitespace(self):
        from bot.auth import _load_admin_ids

        result = _load_admin_ids()
        assert result == [111, 222]

    @patch.dict("os.environ", {"ADMIN_USER_IDS": ""})
    def test_returns_empty_for_empty_string(self):
        from bot.auth import _load_admin_ids

        result = _load_admin_ids()
        assert result == []

    @patch.dict("os.environ", {}, clear=False)
    def test_returns_empty_when_not_set(self):
        import os

        os.environ.pop("ADMIN_USER_IDS", None)
        from bot.auth import _load_admin_ids

        result = _load_admin_ids()
        assert result == []
