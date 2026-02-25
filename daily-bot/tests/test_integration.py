"""Entegrasyon testleri.

run_daily_summary fonksiyonunun baştan sona çalışmasını test eder.
Tüm dış bağımlılıklar (yfinance, CoinGecko, feedparser, Telegram) mock'lanır.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from constants import (
    GOLD_TICKER,
    SILVER_TICKER,
    USDTRY_TICKER,
    EURTRY_TICKER,
)
from scheduler.jobs import run_daily_summary


MOCK_CRYPTO = {
    "bitcoin": {"price_usd": 65000.0, "price_try": 2112500.0, "change_24h": 2.5},
    "ethereum": {"price_usd": 3200.0, "price_try": 104000.0, "change_24h": -1.2},
}

MOCK_US_MARKETS = {
    "sp500": {"price": 5987.0, "change_pct": 0.45},
    "dowjones": {"price": 43250.0, "change_pct": -0.12},
    "nasdaq": {"price": 19432.0, "change_pct": 0.78},
}

MOCK_NEWS = [
    {
        "title": "Ekonomi haberi",
        "source": "Hürriyet",
        "link": "https://example.com/1",
        "published": "",
    },
    {
        "title": "Borsa rallisi",
        "source": "Bloomberg HT",
        "link": "https://example.com/2",
        "published": "",
    },
]

PREV_CLOSE_MAP = {
    GOLD_TICKER: 1980.0,
    SILVER_TICKER: 24.5,
    USDTRY_TICKER: 32.30,
    EURTRY_TICKER: 34.90,
}


class TestRunDailySummaryIntegration:
    """run_daily_summary end-to-end entegrasyon testleri."""

    @pytest.mark.asyncio
    @patch(
        "scheduler.jobs.send_to_channel",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("scheduler.jobs.get_news", return_value=MOCK_NEWS)
    @patch("scheduler.jobs.get_crypto_prices", return_value=MOCK_CRYPTO)
    @patch("scheduler.jobs.get_us_markets", return_value=MOCK_US_MARKETS)
    @patch(
        "scheduler.jobs.get_previous_close",
        side_effect=lambda t: PREV_CLOSE_MAP[t],
    )
    @patch(
        "scheduler.jobs.get_bist100",
        return_value={"price": 9850.0, "change_pct": 0.75},
    )
    @patch(
        "scheduler.jobs.get_exchange_rates",
        return_value={"USD": 32.50, "EUR": 35.10},
    )
    @patch("scheduler.jobs.get_silver_price_try", return_value=28.5)
    @patch("scheduler.jobs.get_gold_price_try", return_value=2057.5)
    async def test_end_to_end_success(
        self,
        mock_gold,
        mock_silver,
        mock_rates,
        mock_bist,
        mock_prev_close,
        mock_us,
        mock_crypto,
        mock_news,
        mock_send,
    ):
        """Tüm adımlar başarılı olduğunda mesaj formatlanıp kanala gönderilmeli."""
        mock_bot = AsyncMock()

        await run_daily_summary(mock_bot)

        mock_gold.assert_called_once()
        mock_silver.assert_called_once()
        mock_rates.assert_called_once()
        mock_bist.assert_called_once()
        assert mock_prev_close.call_count == 4
        mock_us.assert_called_once()
        mock_crypto.assert_called_once()
        mock_news.assert_called_once()
        mock_send.assert_called_once()

        sent_text = mock_send.call_args[0][1]
        assert "Altın" in sent_text
        assert "BTC" in sent_text
        assert "S&P 500" in sent_text
        assert "Ekonomi haberi" in sent_text

    @pytest.mark.asyncio
    @patch(
        "scheduler.jobs.send_to_channel",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("scheduler.jobs.get_news", return_value=MOCK_NEWS)
    @patch("scheduler.jobs.get_crypto_prices", return_value=MOCK_CRYPTO)
    @patch(
        "scheduler.jobs.get_previous_close",
        side_effect=Exception("API down"),
    )
    @patch("scheduler.jobs.get_bist100", side_effect=Exception("API down"))
    @patch(
        "scheduler.jobs.get_exchange_rates",
        side_effect=Exception("API down"),
    )
    @patch(
        "scheduler.jobs.get_silver_price_try",
        side_effect=Exception("API down"),
    )
    @patch(
        "scheduler.jobs.get_gold_price_try",
        side_effect=Exception("API down"),
    )
    async def test_finance_fails_but_crypto_and_news_still_sent(
        self,
        mock_gold,
        mock_silver,
        mock_rates,
        mock_bist,
        mock_prev_close,
        mock_crypto,
        mock_news,
        mock_send,
    ):
        """Finans verisi başarısız olsa da kripto ve haberlerle mesaj gönderilmeli."""
        mock_bot = AsyncMock()

        await run_daily_summary(mock_bot)

        mock_send.assert_called_once()
        sent_text = mock_send.call_args[0][1]
        assert "BTC" in sent_text
        assert "Ekonomi haberi" in sent_text

    @pytest.mark.asyncio
    @patch(
        "scheduler.jobs.send_to_channel",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("scheduler.jobs.get_news", return_value=[])
    @patch(
        "scheduler.jobs.get_crypto_prices",
        side_effect=Exception("API down"),
    )
    @patch(
        "scheduler.jobs.get_previous_close",
        side_effect=Exception("API down"),
    )
    @patch("scheduler.jobs.get_bist100", side_effect=Exception("API down"))
    @patch(
        "scheduler.jobs.get_exchange_rates",
        side_effect=Exception("API down"),
    )
    @patch(
        "scheduler.jobs.get_silver_price_try",
        side_effect=Exception("API down"),
    )
    @patch(
        "scheduler.jobs.get_gold_price_try",
        side_effect=Exception("API down"),
    )
    async def test_all_sources_fail_no_message_sent(
        self,
        mock_gold,
        mock_silver,
        mock_rates,
        mock_bist,
        mock_prev_close,
        mock_crypto,
        mock_news,
        mock_send,
    ):
        """Tüm veri kaynakları başarısız olursa mesaj gönderilmemeli."""
        mock_bot = AsyncMock()

        await run_daily_summary(mock_bot)

        mock_send.assert_not_called()

    @pytest.mark.asyncio
    @patch(
        "scheduler.jobs.send_to_channel",
        new_callable=AsyncMock,
        side_effect=Exception("Telegram error"),
    )
    @patch("scheduler.jobs.get_news", return_value=MOCK_NEWS)
    @patch("scheduler.jobs.get_crypto_prices", return_value=MOCK_CRYPTO)
    @patch("scheduler.jobs.get_us_markets", return_value=MOCK_US_MARKETS)
    @patch(
        "scheduler.jobs.get_previous_close",
        side_effect=lambda t: PREV_CLOSE_MAP[t],
    )
    @patch(
        "scheduler.jobs.get_bist100",
        return_value={"price": 9850.0, "change_pct": 0.75},
    )
    @patch(
        "scheduler.jobs.get_exchange_rates",
        return_value={"USD": 32.50, "EUR": 35.10},
    )
    @patch("scheduler.jobs.get_silver_price_try", return_value=28.5)
    @patch("scheduler.jobs.get_gold_price_try", return_value=2057.5)
    async def test_telegram_send_fails_does_not_crash(
        self,
        mock_gold,
        mock_silver,
        mock_rates,
        mock_bist,
        mock_prev_close,
        mock_us,
        mock_crypto,
        mock_news,
        mock_send,
    ):
        """Telegram gönderimi başarısız olsa da program crash etmemeli."""
        mock_bot = AsyncMock()

        await run_daily_summary(mock_bot)

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "scheduler.jobs.send_to_channel",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch("scheduler.jobs.get_news", return_value=MOCK_NEWS)
    @patch(
        "scheduler.jobs.get_crypto_prices",
        side_effect=Exception("CoinGecko down"),
    )
    @patch("scheduler.jobs.get_us_markets", return_value=MOCK_US_MARKETS)
    @patch(
        "scheduler.jobs.get_previous_close",
        side_effect=lambda t: PREV_CLOSE_MAP[t],
    )
    @patch(
        "scheduler.jobs.get_bist100",
        return_value={"price": 9850.0, "change_pct": 0.75},
    )
    @patch(
        "scheduler.jobs.get_exchange_rates",
        return_value={"USD": 32.50, "EUR": 35.10},
    )
    @patch("scheduler.jobs.get_silver_price_try", return_value=28.5)
    @patch("scheduler.jobs.get_gold_price_try", return_value=2057.5)
    async def test_crypto_fails_finance_and_news_still_sent(
        self,
        mock_gold,
        mock_silver,
        mock_rates,
        mock_bist,
        mock_prev_close,
        mock_us,
        mock_crypto,
        mock_news,
        mock_send,
    ):
        """Kripto başarısız olsa da finans ve haberlerle mesaj gönderilmeli."""
        mock_bot = AsyncMock()

        await run_daily_summary(mock_bot)

        mock_send.assert_called_once()
        sent_text = mock_send.call_args[0][1]
        assert "Altın" in sent_text
        assert "Ekonomi haberi" in sent_text

    @pytest.mark.asyncio
    @patch(
        "scheduler.jobs.send_to_channel",
        new_callable=AsyncMock,
        return_value=True,
    )
    @patch(
        "scheduler.jobs.format_message",
        side_effect=Exception("Format error"),
    )
    @patch("scheduler.jobs.get_news", return_value=MOCK_NEWS)
    @patch("scheduler.jobs.get_crypto_prices", return_value=MOCK_CRYPTO)
    @patch("scheduler.jobs.get_us_markets", return_value=MOCK_US_MARKETS)
    @patch(
        "scheduler.jobs.get_previous_close",
        side_effect=lambda t: PREV_CLOSE_MAP[t],
    )
    @patch(
        "scheduler.jobs.get_bist100",
        return_value={"price": 9850.0, "change_pct": 0.75},
    )
    @patch(
        "scheduler.jobs.get_exchange_rates",
        return_value={"USD": 32.50, "EUR": 35.10},
    )
    @patch("scheduler.jobs.get_silver_price_try", return_value=28.5)
    @patch("scheduler.jobs.get_gold_price_try", return_value=2057.5)
    async def test_format_fails_does_not_crash(
        self,
        mock_gold,
        mock_silver,
        mock_rates,
        mock_bist,
        mock_prev_close,
        mock_us,
        mock_crypto,
        mock_news,
        mock_format,
        mock_send,
    ):
        """Mesaj formatlama başarısız olursa program crash etmemeli."""
        mock_bot = AsyncMock()

        await run_daily_summary(mock_bot)

        mock_send.assert_not_called()
