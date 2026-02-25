import pytest
from unittest.mock import patch, MagicMock

from data.crypto import (
    get_crypto_prices,
    get_previous_crypto_price,
    CryptoRateLimitError,
    CryptoAPIError,
    CryptoDataError,
)


# ---------------------------------------------------------------------------
# fixtures & helpers
# ---------------------------------------------------------------------------

COINGECKO_MARKETS_RESPONSE = [
    {
        "id": "bitcoin",
        "current_price": 65000.0,
        "price_change_percentage_24h": 2.5,
    },
    {
        "id": "ethereum",
        "current_price": 3500.0,
        "price_change_percentage_24h": -1.2,
    },
]

USD_TRY_RATE = 32.0


def _mock_exchange_rates() -> dict:
    return {"USD": USD_TRY_RATE, "EUR": 34.5}


def _make_success_response(json_data, status_code: int = 200) -> MagicMock:
    """requests.get dönüşünü taklit eden mock."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


def _make_error_response(status_code: int) -> MagicMock:
    """Hata dönen HTTP response mock'u."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {}
    resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


# ---------------------------------------------------------------------------
# get_crypto_prices
# ---------------------------------------------------------------------------

class TestGetCryptoPrices:
    @patch("data.crypto.get_exchange_rates", return_value=_mock_exchange_rates())
    @patch("data.crypto.requests.get")
    def test_returns_parsed_prices(self, mock_get, mock_rates):
        mock_get.return_value = _make_success_response(COINGECKO_MARKETS_RESPONSE)

        result = get_crypto_prices()

        assert isinstance(result, dict)
        assert "bitcoin" in result
        assert "ethereum" in result

        btc = result["bitcoin"]
        assert btc["price_usd"] == pytest.approx(65000.0)
        assert btc["price_try"] == pytest.approx(65000.0 * USD_TRY_RATE)
        assert btc["change_24h"] == pytest.approx(2.5)

        eth = result["ethereum"]
        assert eth["price_usd"] == pytest.approx(3500.0)
        assert eth["price_try"] == pytest.approx(3500.0 * USD_TRY_RATE)
        assert eth["change_24h"] == pytest.approx(-1.2)

    @patch("data.crypto.get_exchange_rates", return_value=_mock_exchange_rates())
    @patch("data.crypto.requests.get")
    @patch("data.crypto.time.sleep")
    def test_raises_rate_limit_error_on_429(self, mock_sleep, mock_get, mock_rates):
        mock_get.return_value = _make_error_response(429)

        with pytest.raises(CryptoRateLimitError):
            get_crypto_prices()

    @patch("data.crypto.get_exchange_rates", return_value=_mock_exchange_rates())
    @patch("data.crypto.requests.get")
    def test_raises_api_error_on_500(self, mock_get, mock_rates):
        mock_get.return_value = _make_error_response(500)

        with pytest.raises(CryptoAPIError):
            get_crypto_prices()

    @patch("data.crypto.get_exchange_rates", return_value=_mock_exchange_rates())
    @patch("data.crypto.requests.get")
    def test_raises_data_error_on_empty_response(self, mock_get, mock_rates):
        mock_get.return_value = _make_success_response([])

        with pytest.raises(CryptoDataError):
            get_crypto_prices()

    @patch("data.crypto.get_exchange_rates", return_value=_mock_exchange_rates())
    @patch("data.crypto.requests.get")
    @patch("data.crypto.time.sleep")
    def test_retries_on_429_then_succeeds(self, mock_sleep, mock_get, mock_rates):
        rate_limit_resp = _make_error_response(429)
        success_resp = _make_success_response(COINGECKO_MARKETS_RESPONSE)
        mock_get.side_effect = [rate_limit_resp, success_resp]

        result = get_crypto_prices()

        assert "bitcoin" in result
        assert mock_sleep.called

    @patch("data.crypto.get_exchange_rates", return_value=_mock_exchange_rates())
    @patch("data.crypto.requests.get")
    @patch("data.crypto.time.sleep")
    def test_retries_max_3_times_on_429(self, mock_sleep, mock_get, mock_rates):
        mock_get.return_value = _make_error_response(429)

        with pytest.raises(CryptoRateLimitError):
            get_crypto_prices()

        assert mock_get.call_count == 3


# ---------------------------------------------------------------------------
# get_previous_crypto_price
# ---------------------------------------------------------------------------

MARKET_CHART_RESPONSE = {
    "prices": [
        [1700000000000, 64000.0],
        [1700086400000, 64500.0],
        [1700172800000, 65000.0],
    ]
}


class TestGetPreviousCryptoPrice:
    @patch("data.crypto.requests.get")
    def test_returns_previous_day_close(self, mock_get):
        mock_get.return_value = _make_success_response(MARKET_CHART_RESPONSE)

        result = get_previous_crypto_price("bitcoin")

        assert isinstance(result, float)
        assert result == pytest.approx(64500.0)

    @patch("data.crypto.requests.get")
    def test_raises_api_error_on_failure(self, mock_get):
        mock_get.return_value = _make_error_response(500)

        with pytest.raises(CryptoAPIError):
            get_previous_crypto_price("bitcoin")

    @patch("data.crypto.requests.get")
    def test_raises_data_error_on_empty_prices(self, mock_get):
        mock_get.return_value = _make_success_response({"prices": []})

        with pytest.raises(CryptoDataError):
            get_previous_crypto_price("bitcoin")
