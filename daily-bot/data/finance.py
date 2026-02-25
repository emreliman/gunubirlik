"""Finans verisi çekme modülü.

yfinance üzerinden altın, gümüş, döviz ve BIST-100 verilerini çeker.
"""

import logging

import yfinance as yf

from constants import (
    GOLD_TICKER,
    SILVER_TICKER,
    USDTRY_TICKER,
    EURTRY_TICKER,
    BIST100_TICKER,
    TROY_OUNCE_TO_GRAM,
    US_MARKET_TICKERS,
)

logger = logging.getLogger(__name__)


class FinanceDataError(Exception):
    """Finans verisi alınamadığında fırlatılır."""


def _get_last_price(ticker: str) -> float:
    """Verilen ticker sembolünün son fiyatını döndürür.

    Args:
        ticker: yfinance ticker sembolü.

    Returns:
        Son işlem fiyatı.

    Raises:
        FinanceDataError: Fiyat bilgisi alınamazsa.
    """
    try:
        data = yf.Ticker(ticker)
        price = data.fast_info["lastPrice"]
        logger.info("Ticker %s fiyat: %s", ticker, price)
        return float(price)
    except Exception as exc:
        logger.error("Ticker %s verisi alınamadı: %s", ticker, exc)
        raise FinanceDataError(
            f"{ticker} fiyat bilgisi alınamadı"
        ) from exc


def _get_precious_metal_price_try(metal_ticker: str) -> float:
    """Kıymetli metal fiyatını USD/ons'tan TRY/gram'a çevirir.

    Args:
        metal_ticker: Metal için yfinance ticker sembolü (ör. GC=F).

    Returns:
        Gram başına TRY fiyatı.

    Raises:
        FinanceDataError: Veri alınamazsa.
    """
    metal_usd = _get_last_price(metal_ticker)
    usd_try = _get_last_price(USDTRY_TICKER)
    gram_price = (metal_usd * usd_try) / TROY_OUNCE_TO_GRAM
    logger.info(
        "%s gram fiyatı: %.2f TRY", metal_ticker, gram_price
    )
    return gram_price


def get_gold_price_try() -> float:
    """Gram altın fiyatını TRY cinsinden döndürür.

    Returns:
        Gram altın TRY fiyatı.

    Raises:
        FinanceDataError: Veri alınamazsa.
    """
    return _get_precious_metal_price_try(GOLD_TICKER)


def get_silver_price_try() -> float:
    """Gram gümüş fiyatını TRY cinsinden döndürür.

    Returns:
        Gram gümüş TRY fiyatı.

    Raises:
        FinanceDataError: Veri alınamazsa.
    """
    return _get_precious_metal_price_try(SILVER_TICKER)


def get_exchange_rates() -> dict[str, float]:
    """USD/TRY ve EUR/TRY kurlarını döndürür.

    Returns:
        {"USD": float, "EUR": float} formatında döviz kurları.

    Raises:
        FinanceDataError: Veri alınamazsa.
    """
    usd = _get_last_price(USDTRY_TICKER)
    eur = _get_last_price(EURTRY_TICKER)
    rates = {"USD": usd, "EUR": eur}
    logger.info("Döviz kurları: %s", rates)
    return rates


def get_bist100() -> dict[str, float]:
    """BIST-100 endeksinin güncel fiyatını ve günlük değişim yüzdesini döndürür.

    Returns:
        {"price": float, "change_pct": float} formatında endeks bilgisi.

    Raises:
        FinanceDataError: Veri alınamazsa.
    """
    try:
        data = yf.Ticker(BIST100_TICKER)
        price = float(data.fast_info["lastPrice"])
        prev_close = float(data.fast_info["previousClose"])
        change_pct = ((price - prev_close) / prev_close) * 100
        logger.info("BIST-100: %.2f (%%%.2f)", price, change_pct)
        return {"price": price, "change_pct": change_pct}
    except Exception as exc:
        logger.error("BIST-100 verisi alınamadı: %s", exc)
        raise FinanceDataError("BIST-100 verisi alınamadı") from exc


def get_previous_close(ticker: str) -> float:
    """Verilen ticker için önceki günün kapanış fiyatını döndürür.

    Args:
        ticker: yfinance ticker sembolü.

    Returns:
        Önceki günün kapanış fiyatı.

    Raises:
        FinanceDataError: API hatası oluşursa.
        ValueError: Yeterli geçmiş verisi yoksa.
    """
    try:
        data = yf.Ticker(ticker)
        history = data.history(period="5d")
    except Exception as exc:
        logger.error("Ticker %s geçmişi alınamadı: %s", ticker, exc)
        raise FinanceDataError(
            f"{ticker} geçmiş verisi alınamadı"
        ) from exc

    if history.empty or len(history) < 2:
        raise ValueError(
            f"{ticker} için yeterli geçmiş verisi bulunamadı"
        )

    previous_close = float(history["Close"].iloc[-2])
    logger.info("Ticker %s önceki kapanış: %s", ticker, previous_close)
    return previous_close


def get_us_markets() -> dict[str, dict[str, float]]:
    """ABD borsası endeks verilerini döndürür.

    Returns:
        {"sp500": {"price": float, "change_pct": float}, ...} formatında.

    Raises:
        FinanceDataError: Herhangi bir endeks verisi alınamazsa.
    """
    result: dict[str, dict[str, float]] = {}

    for name, ticker in US_MARKET_TICKERS.items():
        try:
            data = yf.Ticker(ticker)
            price = float(data.fast_info["lastPrice"])
            prev_close = float(data.fast_info["previousClose"])
            change_pct = ((price - prev_close) / prev_close) * 100
            result[name] = {"price": price, "change_pct": change_pct}
            logger.info("%s: %.2f (%%%.2f)", name, price, change_pct)
        except Exception as exc:
            logger.error("%s verisi alınamadı: %s", name, exc)
            raise FinanceDataError(f"{name} verisi alınamadı") from exc

    return result
