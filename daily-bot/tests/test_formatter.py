from unittest.mock import patch
from datetime import datetime

from bot.formatter import (
    format_message,
    format_change,
    format_metals_only,
    format_forex_only,
    format_bist_only,
    format_crypto_only,
    format_news_only,
)


# ---------------------------------------------------------------------------
# shared test data
# ---------------------------------------------------------------------------

FINANCE_DATA = {
    "gold_try": 2057.5,
    "gold_prev": 2040.0,
    "silver_try": 28.5,
    "silver_prev": 28.0,
    "usd": 32.50,
    "usd_prev": 32.30,
    "eur": 35.10,
    "eur_prev": 34.90,
    "bist100": {"price": 9850.0, "change_pct": 0.75},
    "us_markets": {
        "sp500": {"price": 5987.0, "change_pct": 0.45},
        "dowjones": {"price": 43250.0, "change_pct": -0.12},
        "nasdaq": {"price": 19432.0, "change_pct": 0.78},
    },
}

CRYPTO_DATA = {
    "bitcoin": {"price_usd": 65000.0, "price_try": 2112500.0, "change_24h": 2.5},
    "ethereum": {"price_usd": 3200.0, "price_try": 104000.0, "change_24h": -1.2},
}

NEWS_DATA = [
    {"title": "Haber 1", "source": "Hürriyet", "link": "https://example.com/1"},
    {"title": "Haber 2", "source": "Bloomberg HT", "link": "https://example.com/2"},
]

TELEGRAM_MAX_LENGTH = 4096


# ---------------------------------------------------------------------------
# format_change
# ---------------------------------------------------------------------------

class TestFormatChange:
    def test_positive_change(self):
        result = format_change(100.0, 90.0)
        assert "📈" in result
        assert r"\+11\.11%" in result

    def test_negative_change(self):
        result = format_change(100.0, 110.0)
        assert "📉" in result
        assert r"\-9\.09%" in result

    def test_zero_change(self):
        result = format_change(100.0, 100.0)
        assert "➡️" in result
        assert r"0\.00%" in result

    def test_returns_str(self):
        assert isinstance(format_change(50.0, 40.0), str)


# ---------------------------------------------------------------------------
# format_message
# ---------------------------------------------------------------------------

class TestFormatMessage:
    @patch("bot.formatter._now_istanbul")
    def test_contains_gold_keyword(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert "Altın" in msg

    @patch("bot.formatter._now_istanbul")
    def test_uses_up_emoji_for_increase(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert "📈" in msg

    @patch("bot.formatter._now_istanbul")
    def test_uses_down_emoji_for_decrease(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        crypto_with_drop = {
            "bitcoin": {"price_usd": 65000.0, "price_try": 2112500.0, "change_24h": -3.0},
            "ethereum": {"price_usd": 3200.0, "price_try": 104000.0, "change_24h": -1.2},
        }
        msg = format_message(FINANCE_DATA, crypto_with_drop, NEWS_DATA)
        assert "📉" in msg

    @patch("bot.formatter._now_istanbul")
    def test_change_pct_format(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert "%" in msg

    @patch("bot.formatter._now_istanbul")
    def test_message_within_telegram_limit(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert len(msg) <= TELEGRAM_MAX_LENGTH

    @patch("bot.formatter._now_istanbul")
    def test_contains_news_links(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert "https://example.com/1" in msg
        assert "https://example.com/2" in msg

    @patch("bot.formatter._now_istanbul")
    def test_contains_turkish_number_format(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert r"2\.057,50" in msg

    @patch("bot.formatter._now_istanbul")
    def test_contains_date(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert r"25\.02\.2026" in msg

    @patch("bot.formatter._now_istanbul")
    def test_returns_str(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        result = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert isinstance(result, str)

    @patch("bot.formatter._now_istanbul")
    def test_handles_empty_news(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, [])
        assert isinstance(msg, str)
        assert "Altın" in msg

    @patch("bot.formatter._now_istanbul")
    def test_contains_us_market_section(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_message(FINANCE_DATA, CRYPTO_DATA, NEWS_DATA)
        assert "ABD BORSA" in msg
        assert "S&P 500" in msg
        assert "Nasdaq" in msg

    @patch("bot.formatter._now_istanbul")
    def test_us_markets_section_hidden_when_empty(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        finance_no_us = {**FINANCE_DATA, "us_markets": {}}
        msg = format_message(finance_no_us, CRYPTO_DATA, NEWS_DATA)
        assert "ABD BORSA" not in msg


# ---------------------------------------------------------------------------
# Standalone section format functions
# ---------------------------------------------------------------------------


METALS_DATA = {
    "gold_try": 2057.5,
    "gold_prev": 2040.0,
    "silver_try": 28.5,
    "silver_prev": 28.0,
}

FOREX_DATA = {
    "usd": 32.50,
    "usd_prev": 32.30,
    "eur": 35.10,
    "eur_prev": 34.90,
}

BIST_DATA = {
    "bist100": {"price": 9850.0, "change_pct": 0.75},
    "us_markets": {
        "sp500": {"price": 5987.0, "change_pct": 0.45},
    },
}


class TestFormatMetalsOnly:
    @patch("bot.formatter._now_istanbul")
    def test_contains_date_and_gold(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_metals_only(METALS_DATA)
        assert "Altın" in msg
        assert r"25\.02\.2026" in msg

    @patch("bot.formatter._now_istanbul")
    def test_returns_str(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        assert isinstance(format_metals_only(METALS_DATA), str)


class TestFormatForexOnly:
    @patch("bot.formatter._now_istanbul")
    def test_contains_usd_and_eur(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_forex_only(FOREX_DATA)
        assert "USD" in msg
        assert "EUR" in msg

    @patch("bot.formatter._now_istanbul")
    def test_contains_date(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_forex_only(FOREX_DATA)
        assert r"25\.02\.2026" in msg


class TestFormatBistOnly:
    @patch("bot.formatter._now_istanbul")
    def test_contains_bist_section(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_bist_only(BIST_DATA)
        assert "BIST" in msg

    @patch("bot.formatter._now_istanbul")
    def test_includes_us_markets_when_present(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_bist_only(BIST_DATA)
        assert "ABD BORSA" in msg

    @patch("bot.formatter._now_istanbul")
    def test_hides_us_markets_when_empty(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        data = {"bist100": {"price": 9850.0, "change_pct": 0.75}, "us_markets": {}}
        msg = format_bist_only(data)
        assert "ABD BORSA" not in msg


class TestFormatCryptoOnly:
    @patch("bot.formatter._now_istanbul")
    def test_contains_crypto_data(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_crypto_only(CRYPTO_DATA)
        assert "BTC" in msg
        assert "ETH" in msg


class TestFormatNewsOnly:
    @patch("bot.formatter._now_istanbul")
    def test_contains_news_titles(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_news_only(NEWS_DATA)
        assert "Haber 1" in msg

    @patch("bot.formatter._now_istanbul")
    def test_handles_empty_news(self, mock_now):
        mock_now.return_value = datetime(2026, 2, 25, 9, 0, 0)
        msg = format_news_only([])
        assert "Haber bulunamadı" in msg

