"""Grafik verisi toplama ve PNG grafik üretimi modülü."""

from __future__ import annotations

import io
import logging
from datetime import datetime

import requests
import yfinance as yf

from constants import (
    CHART_ASSET_ALIASES,
    CHART_PERIOD_DAYS,
    CHART_PERIOD_LABELS,
    GOLD_TICKER,
    TROY_OUNCE_TO_GRAM,
    USDTRY_TICKER,
)

logger = logging.getLogger(__name__)

COINGECKO_MARKET_CHART_URL = (
    "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
)
REQUEST_TIMEOUT_SECONDS = 10
MIN_PRICE_POINTS = 2
CHART_FIGURE_WIDTH = 9
CHART_FIGURE_HEIGHT = 4
CHART_LINE_WIDTH = 2
CHART_DPI = 150


def _normalize_asset(asset: str) -> str:
    """Desteklenen varlik adini normalize eder.

    Args:
        asset: Kullanici girdisi varlik adi.

    Returns:
        "btc" veya "altin".

    Raises:
        ValueError: Varlik desteklenmiyorsa.
    """
    normalized = CHART_ASSET_ALIASES.get(asset.lower())
    if normalized is None:
        raise ValueError("Desteklenen varliklar: btc, altin")
    return normalized


def _normalize_period(period: str) -> tuple[int, str]:
    """Periyot girdisini gun sayisi ve etiketine cevirir.

    Args:
        period: Kullanici periyot girdisi.

    Returns:
        (gun_sayisi, etiket) tuple'i.

    Raises:
        ValueError: Periyot desteklenmiyorsa.
    """
    period_key = period.lower()
    days = CHART_PERIOD_DAYS.get(period_key)
    label = CHART_PERIOD_LABELS.get(period_key)
    if days is None or label is None:
        raise ValueError("Desteklenen periyotlar: 1h (1 hafta), 1a (1 ay)")
    return days, label


def _fetch_btc_prices_try(days: int) -> list[tuple[str, float]]:
    """BTC icin TRY bazli gunluk fiyat serisini ceker.

    Args:
        days: Geriye donuk gun sayisi.

    Returns:
        [(tarih, fiyat)] formatinda sirali liste.

    Raises:
        ValueError: Veri alinamazsa veya yetersizse.
    """
    params = {"vs_currency": "try", "days": str(days), "interval": "daily"}
    response = requests.get(
        COINGECKO_MARKET_CHART_URL,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise ValueError(f"BTC veri kaynagi hatasi: HTTP {response.status_code}")

    payload = response.json()
    prices = payload.get("prices", [])
    if len(prices) < MIN_PRICE_POINTS:
        raise ValueError("BTC icin yeterli grafik verisi bulunamadi")

    points: list[tuple[str, float]] = []
    for timestamp_ms, price in prices:
        date_str = datetime.utcfromtimestamp(timestamp_ms / 1000).strftime(
            "%Y-%m-%d"
        )
        points.append((date_str, float(price)))

    return points[-days:]


def _fetch_gold_prices_try(days: int) -> list[tuple[str, float]]:
    """Altin icin TRY/gram gunluk fiyat serisini ceker.

    Args:
        days: Geriye donuk gun sayisi.

    Returns:
        [(tarih, fiyat)] formatinda sirali liste.

    Raises:
        ValueError: Veri alinamazsa veya yetersizse.
    """
    history_period = f"{days + MIN_PRICE_POINTS}d"
    gold_history = yf.Ticker(GOLD_TICKER).history(period=history_period, interval="1d")
    usdtry_history = yf.Ticker(USDTRY_TICKER).history(
        period=history_period, interval="1d"
    )

    if gold_history.empty or usdtry_history.empty:
        raise ValueError("Altin icin yeterli grafik verisi bulunamadi")

    merged = gold_history[["Close"]].rename(columns={"Close": "gold_close"}).join(
        usdtry_history[["Close"]].rename(columns={"Close": "usdtry_close"}),
        how="inner",
    )
    merged = merged.dropna()
    if len(merged) < MIN_PRICE_POINTS:
        raise ValueError("Altin icin yeterli grafik verisi bulunamadi")

    points: list[tuple[str, float]] = []
    for index, row in merged.tail(days).iterrows():
        gram_try_price = (float(row["gold_close"]) * float(row["usdtry_close"])) / (
            TROY_OUNCE_TO_GRAM
        )
        points.append((index.strftime("%Y-%m-%d"), gram_try_price))

    return points


def _render_chart_png(
    points: list[tuple[str, float]], title: str, y_label: str
) -> bytes:
    """Verilen seri icin PNG grafik byte'larini uretir.

    Args:
        points: [(tarih, fiyat)] serisi.
        title: Grafik basligi.
        y_label: Y ekseni etiketi.

    Returns:
        PNG byte verisi.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    figure, axis = plt.subplots(
        figsize=(CHART_FIGURE_WIDTH, CHART_FIGURE_HEIGHT)
    )
    axis.plot(x_values, y_values, linewidth=CHART_LINE_WIDTH)
    axis.set_title(title)
    axis.set_xlabel("Tarih")
    axis.set_ylabel(y_label)
    axis.grid(True, alpha=0.3)
    axis.tick_params(axis="x", rotation=45)

    figure.tight_layout()
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=CHART_DPI)
    plt.close(figure)
    buffer.seek(0)
    return buffer.read()


def _build_caption(asset_name: str, period_label: str, points: list[tuple[str, float]]) -> str:
    """Grafik alt yazisini olusturur.

    Args:
        asset_name: Gorunur varlik adi.
        period_label: Gorunur periyot adi.
        points: [(tarih, fiyat)] serisi.

    Returns:
        Telegram'da gosterilecek basit metin.
    """
    first_price = points[0][1]
    last_price = points[-1][1]
    change_pct = ((last_price - first_price) / first_price) * 100
    return (
        f"{asset_name} - Son {period_label}\n"
        f"Baslangic: {first_price:,.2f} TRY\n"
        f"Guncel: {last_price:,.2f} TRY\n"
        f"Degisim: {change_pct:+.2f}%"
    )


def generate_asset_chart_png(asset: str, period: str) -> tuple[bytes, str]:
    """Istenen varlik/periyot icin grafik PNG ve aciklama metni dondurur.

    Args:
        asset: btc/altin benzeri varlik parametresi.
        period: 1h/1a benzeri periyot parametresi.

    Returns:
        (png_bytes, caption_text)

    Raises:
        ValueError: Parametre veya veri hatasinda.
    """
    normalized_asset = _normalize_asset(asset)
    days, period_label = _normalize_period(period)

    if normalized_asset == "btc":
        points = _fetch_btc_prices_try(days)
        title = f"BTC/TRY - Son {period_label}"
        caption_asset = "BTC"
    else:
        points = _fetch_gold_prices_try(days)
        title = f"Gram Altin (TRY) - Son {period_label}"
        caption_asset = "Altin"

    if len(points) < MIN_PRICE_POINTS:
        raise ValueError("Grafik icin yeterli veri bulunamadi")

    image_bytes = _render_chart_png(points, title=title, y_label="TRY")
    caption = _build_caption(caption_asset, period_label, points)
    logger.info(
        "Grafik uretildi: asset=%s period=%s points=%d",
        normalized_asset,
        period,
        len(points),
    )
    return image_bytes, caption
