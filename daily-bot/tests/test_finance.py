import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from data.finance import (
    get_gold_price_try,
    get_silver_price_try,
    get_exchange_rates,
    get_bist100,
    get_previous_close,
    get_us_markets,
)
from constants import TROY_OUNCE_TO_GRAM


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_ticker_mock(price: float) -> MagicMock:
    """yfinance.Ticker nesnesini taklit eden mock oluşturur."""
    ticker = MagicMock()
    ticker.fast_info = {"lastPrice": price}
    return ticker


def _make_ticker_mock_with_history(
    price: float, previous_close: float, change_pct: float
) -> MagicMock:
    """fast_info + history() dönen mock oluşturur."""
    ticker = MagicMock()
    ticker.fast_info = {"lastPrice": price, "previousClose": previous_close}
    history_df = pd.DataFrame({"Close": [previous_close, price]})
    ticker.history.return_value = history_df
    return ticker


# ---------------------------------------------------------------------------
# get_gold_price_try
# ---------------------------------------------------------------------------

class TestGetGoldPriceTry:
    @patch("data.finance.yf.Ticker")
    def test_returns_gram_gold_price_in_try(self, mock_ticker_cls):
        gold_usd = 2000.0
        usd_try = 32.0

        gold_mock = _make_ticker_mock(gold_usd)
        usd_mock = _make_ticker_mock(usd_try)
        mock_ticker_cls.side_effect = lambda t: (
            gold_mock if t == "GC=F" else usd_mock
        )

        result = get_gold_price_try()
        expected = gold_usd * usd_try / TROY_OUNCE_TO_GRAM

        assert isinstance(result, float)
        assert result == pytest.approx(expected, rel=1e-2)

    @patch("data.finance.yf.Ticker")
    def test_raises_on_missing_data(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("No data")
        with pytest.raises(Exception):
            get_gold_price_try()


# ---------------------------------------------------------------------------
# get_silver_price_try
# ---------------------------------------------------------------------------

class TestGetSilverPriceTry:
    @patch("data.finance.yf.Ticker")
    def test_returns_gram_silver_price_in_try(self, mock_ticker_cls):
        silver_usd = 25.0
        usd_try = 32.0

        silver_mock = _make_ticker_mock(silver_usd)
        usd_mock = _make_ticker_mock(usd_try)
        mock_ticker_cls.side_effect = lambda t: (
            silver_mock if t == "SI=F" else usd_mock
        )

        result = get_silver_price_try()
        expected = silver_usd * usd_try / TROY_OUNCE_TO_GRAM

        assert isinstance(result, float)
        assert result == pytest.approx(expected, rel=1e-2)

    @patch("data.finance.yf.Ticker")
    def test_raises_on_missing_data(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("No data")
        with pytest.raises(Exception):
            get_silver_price_try()


# ---------------------------------------------------------------------------
# get_exchange_rates
# ---------------------------------------------------------------------------

class TestGetExchangeRates:
    @patch("data.finance.yf.Ticker")
    def test_returns_usd_and_eur_rates(self, mock_ticker_cls):
        usd_try = 32.0
        eur_try = 34.5

        mock_ticker_cls.side_effect = lambda t: (
            _make_ticker_mock(usd_try)
            if t == "USDTRY=X"
            else _make_ticker_mock(eur_try)
        )

        result = get_exchange_rates()

        assert isinstance(result, dict)
        assert "USD" in result
        assert "EUR" in result
        assert result["USD"] == pytest.approx(usd_try)
        assert result["EUR"] == pytest.approx(eur_try)

    @patch("data.finance.yf.Ticker")
    def test_raises_on_missing_data(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("No data")
        with pytest.raises(Exception):
            get_exchange_rates()


# ---------------------------------------------------------------------------
# get_bist100
# ---------------------------------------------------------------------------

class TestGetBist100:
    @patch("data.finance.yf.Ticker")
    def test_returns_price_and_change_pct(self, mock_ticker_cls):
        price = 9500.0
        prev_close = 9400.0
        change_pct = ((price - prev_close) / prev_close) * 100

        ticker_mock = _make_ticker_mock_with_history(price, prev_close, change_pct)
        mock_ticker_cls.return_value = ticker_mock

        result = get_bist100()

        assert isinstance(result, dict)
        assert "price" in result
        assert "change_pct" in result
        assert result["price"] == pytest.approx(price)
        assert result["change_pct"] == pytest.approx(change_pct, rel=1e-2)

    @patch("data.finance.yf.Ticker")
    def test_raises_on_missing_data(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("No data")
        with pytest.raises(Exception):
            get_bist100()


# ---------------------------------------------------------------------------
# get_previous_close
# ---------------------------------------------------------------------------

class TestGetPreviousClose:
    @patch("data.finance.yf.Ticker")
    def test_returns_previous_close_price(self, mock_ticker_cls):
        prev_close = 150.0
        current = 155.0

        ticker_mock = MagicMock()
        history_df = pd.DataFrame({"Close": [prev_close, current]})
        ticker_mock.history.return_value = history_df
        mock_ticker_cls.return_value = ticker_mock

        result = get_previous_close("AAPL")

        assert isinstance(result, float)
        assert result == pytest.approx(prev_close)

    @patch("data.finance.yf.Ticker")
    def test_raises_on_empty_history(self, mock_ticker_cls):
        ticker_mock = MagicMock()
        ticker_mock.history.return_value = pd.DataFrame({"Close": []})
        mock_ticker_cls.return_value = ticker_mock

        with pytest.raises(ValueError):
            get_previous_close("INVALID")

    @patch("data.finance.yf.Ticker")
    def test_raises_on_api_error(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("API error")
        with pytest.raises(Exception):
            get_previous_close("AAPL")


# ---------------------------------------------------------------------------
# get_us_markets
# ---------------------------------------------------------------------------

class TestGetUsMarkets:
    @patch("data.finance.yf.Ticker")
    def test_returns_three_indices(self, mock_ticker_cls):
        sp_price, sp_prev = 5987.0, 5960.0
        dj_price, dj_prev = 43250.0, 43300.0
        nq_price, nq_prev = 19432.0, 19280.0

        def side_effect(symbol):
            mapping = {
                "^GSPC": (sp_price, sp_prev),
                "^DJI": (dj_price, dj_prev),
                "^IXIC": (nq_price, nq_prev),
            }
            price, prev = mapping[symbol]
            mock = MagicMock()
            mock.fast_info = {"lastPrice": price, "previousClose": prev}
            return mock

        mock_ticker_cls.side_effect = side_effect

        result = get_us_markets()

        assert "sp500" in result
        assert "dowjones" in result
        assert "nasdaq" in result

        for data in result.values():
            assert "price" in data
            assert "change_pct" in data

        expected_sp_pct = ((sp_price - sp_prev) / sp_prev) * 100
        assert result["sp500"]["price"] == pytest.approx(sp_price)
        assert result["sp500"]["change_pct"] == pytest.approx(expected_sp_pct, rel=1e-2)

    @patch("data.finance.yf.Ticker")
    def test_raises_on_api_error(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("API error")
        with pytest.raises(Exception):
            get_us_markets()
