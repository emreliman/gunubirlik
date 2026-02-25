"""Kripto para verisi çekme modülü.

CoinGecko ücretsiz API üzerinden Bitcoin, Ethereum vb. fiyatlarını çeker.
"""

import logging
import time
import requests

from constants import CRYPTO_IDS
from data.finance import get_exchange_rates

logger = logging.getLogger(__name__)

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CryptoAPIError(Exception):
    """CoinGecko API genel hata."""


class CryptoRateLimitError(CryptoAPIError):
    """CoinGecko API rate limit (429) aşıldığında fırlatılır."""


class CryptoDataError(CryptoAPIError):
    """Beklenen veri bulunamadığında fırlatılır."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_with_retry(url: str, params: dict | None = None) -> requests.Response:
    """GET isteği yapar; 429 alırsa retry uygular.

    Args:
        url: İstek atılacak URL.
        params: Sorgu parametreleri.

    Returns:
        Başarılı HTTP response.

    Raises:
        CryptoRateLimitError: Tüm denemeler sonrası hâlâ 429 alınıyorsa.
        CryptoAPIError: 429 dışındaki HTTP hataları için.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(url, params=params, timeout=10)

        if resp.status_code == 200:
            return resp

        if resp.status_code == 429:
            logger.warning(
                "CoinGecko rate limit, deneme %d/%d", attempt, MAX_RETRIES
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise CryptoRateLimitError(
                f"Rate limit aşıldı, {MAX_RETRIES} deneme sonrası başarısız"
            )

        raise CryptoAPIError(f"CoinGecko API hatası: HTTP {resp.status_code}")

    raise CryptoRateLimitError("Maksimum deneme sayısına ulaşıldı")


def _parse_markets_response(
    data: list[dict], usd_try_rate: float
) -> dict[str, dict]:
    """CoinGecko /coins/markets response'unu parse eder.

    Args:
        data: API'den dönen JSON listesi.
        usd_try_rate: Güncel USD/TRY kuru.

    Returns:
        coin_id -> {price_usd, price_try, change_24h} sözlüğü.

    Raises:
        CryptoDataError: Veri boşsa.
    """
    if not data:
        raise CryptoDataError("CoinGecko API boş veri döndürdü")

    result: dict[str, dict] = {}
    for coin in data:
        coin_id = coin["id"]
        price_usd = float(coin["current_price"])
        result[coin_id] = {
            "price_usd": price_usd,
            "price_try": price_usd * usd_try_rate,
            "change_24h": float(coin["price_change_percentage_24h"]),
        }

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_crypto_prices() -> dict[str, dict]:
    """CRYPTO_IDS'deki coinlerin güncel fiyatlarını döndürür.

    Returns:
        coin_id -> {"price_usd": float, "price_try": float, "change_24h": float}

    Raises:
        CryptoRateLimitError: Rate limit aşılırsa.
        CryptoAPIError: API hatası oluşursa.
        CryptoDataError: Boş veri dönerse.
    """
    rates = get_exchange_rates()
    usd_try_rate = rates["USD"]

    ids_param = ",".join(CRYPTO_IDS)
    url = f"{COINGECKO_BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids_param,
        "order": "market_cap_desc",
    }

    resp = _fetch_with_retry(url, params=params)
    data = resp.json()

    result = _parse_markets_response(data, usd_try_rate)
    logger.info("Kripto fiyatları alındı: %s", list(result.keys()))
    return result


def get_previous_crypto_price(coin_id: str) -> float:
    """Belirtilen coin'in dünkü kapanış fiyatını USD cinsinden döndürür.

    Args:
        coin_id: CoinGecko coin id'si (ör. "bitcoin").

    Returns:
        Dünkü kapanış USD fiyatı.

    Raises:
        CryptoAPIError: API hatası oluşursa.
        CryptoDataError: Yeterli fiyat verisi yoksa.
    """
    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "2"}

    resp = _fetch_with_retry(url, params=params)
    data = resp.json()

    prices = data.get("prices", [])
    if len(prices) < 2:
        raise CryptoDataError(
            f"{coin_id} için yeterli geçmiş fiyat verisi bulunamadı"
        )

    previous_close = float(prices[-2][1])
    logger.info("%s dünkü kapanış: %.2f USD", coin_id, previous_close)
    return previous_close
