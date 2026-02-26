"""Telegram mesaj formatlama modülü.

Ham finans, kripto ve haber verilerini okunabilir Telegram mesajına dönüştürür.
MarkdownV2 parse mode kullanır.
"""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

_ISTANBUL_TZ = timezone(timedelta(hours=3))
_TELEGRAM_MAX_LENGTH = 4096
_MARKDOWN_V2_SPECIAL = set(r'_*[]()~`>#+-=|{}.!')


def _escape_md(text: str) -> str:
    """MarkdownV2 özel karakterlerini escape eder.

    Args:
        text: Escape edilecek metin.

    Returns:
        Özel karakterleri backslash ile escape edilmiş metin.
    """
    return "".join(f"\\{ch}" if ch in _MARKDOWN_V2_SPECIAL else ch for ch in text)


def _now_istanbul() -> datetime:
    """Şu anki Istanbul zamanını döndürür."""
    return datetime.now(_ISTANBUL_TZ)


def _format_turkish_number(value: float, decimals: int = 2) -> str:
    """Sayıyı Türkçe formata çevirir ve MarkdownV2 için escape eder.

    Args:
        value: Formatlanacak sayı.
        decimals: Ondalık basamak sayısı.

    Returns:
        Türkçe formatlı, escape edilmiş sayı metni (ör. "2\\.057,50").
    """
    formatted = f"{value:,.{decimals}f}"
    formatted = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return _escape_md(formatted)


def _format_pct_with_emoji(change_pct: float) -> str:
    """Yüzde değişimi emoji ile formatlar (MarkdownV2 uyumlu).

    Args:
        change_pct: Yüzde değişim değeri.

    Returns:
        Emoji ve escape edilmiş yüzde (ör. "📈 \\+2\\.50%").
    """
    if change_pct > 0:
        return f"📈 {_escape_md(f'+{change_pct:.2f}%')}"
    if change_pct < 0:
        return f"📉 {_escape_md(f'{change_pct:.2f}%')}"
    return f"➡️ {_escape_md('0.00%')}"


def format_change(current: float, previous: float) -> str:
    """Mevcut ve önceki değer arasındaki yüzde değişimi formatlar.

    Args:
        current: Güncel değer.
        previous: Önceki değer.

    Returns:
        Emoji ve yüzde içeren metin (ör. "📈 \\+1\\.23%").
    """
    if previous == 0:
        return _format_pct_with_emoji(0.0)

    change_pct = ((current - previous) / previous) * 100
    return _format_pct_with_emoji(change_pct)


def _build_metals_section(finance_data: dict) -> str:
    """Altın ve gümüş bölümünü oluşturur.

    Args:
        finance_data: Finans verileri dict'i.

    Returns:
        Formatlanmış metin bloğu.
    """
    gold_line = (
        f"• Altın \\(gram\\): {_format_turkish_number(finance_data['gold_try'])} ₺ "
        f"{format_change(finance_data['gold_try'], finance_data['gold_prev'])}"
    )
    silver_line = (
        f"• Gümüş \\(gram\\): {_format_turkish_number(finance_data['silver_try'])} ₺ "
        f"{format_change(finance_data['silver_try'], finance_data['silver_prev'])}"
    )
    return f"💛 *ALTIN & GÜMÜŞ*\n{gold_line}\n{silver_line}"


def _build_forex_section(finance_data: dict) -> str:
    """Döviz bölümünü oluşturur.

    Args:
        finance_data: Finans verileri dict'i.

    Returns:
        Formatlanmış metin bloğu.
    """
    usd_line = (
        f"• USD/TRY: {_format_turkish_number(finance_data['usd'])} "
        f"{format_change(finance_data['usd'], finance_data['usd_prev'])}"
    )
    eur_line = (
        f"• EUR/TRY: {_format_turkish_number(finance_data['eur'])} "
        f"{format_change(finance_data['eur'], finance_data['eur_prev'])}"
    )
    return f"💵 *DÖVİZ*\n{usd_line}\n{eur_line}"


def _build_bist_section(finance_data: dict) -> str:
    """BIST-100 bölümünü oluşturur.

    Args:
        finance_data: Finans verileri dict'i.

    Returns:
        Formatlanmış metin bloğu.
    """
    bist = finance_data["bist100"]
    change_str = _format_pct_with_emoji(bist["change_pct"])

    return (
        f"📈 *BORSA*\n"
        f"• BIST100: {_format_turkish_number(bist['price'], decimals=0)} {change_str}"
    )


def _build_crypto_section(crypto_data: dict) -> str:
    """Kripto bölümünü oluşturur.

    Args:
        crypto_data: Kripto verileri dict'i.

    Returns:
        Formatlanmış metin bloğu.
    """
    lines: list[str] = []
    labels = {"bitcoin": "BTC", "ethereum": "ETH"}

    for coin_id, data in crypto_data.items():
        label = labels.get(coin_id, coin_id.upper())
        price_usd = _format_turkish_number(data["price_usd"], decimals=0)
        price_try = _format_turkish_number(data["price_try"], decimals=0)
        change = _format_pct_with_emoji(data["change_24h"])
        lines.append(f"• {label}: ${price_usd} \\({price_try} ₺\\) {change}")

    return "₿ *KRİPTO*\n" + "\n".join(lines)


def _build_us_markets_section(finance_data: dict) -> str:
    """ABD borsası bölümünü oluşturur.

    Args:
        finance_data: Finans verileri dict'i.

    Returns:
        Formatlanmış metin bloğu veya boş string (veri yoksa).
    """
    us = finance_data.get("us_markets", {})
    if not us:
        return ""

    labels = {"sp500": "S&P 500", "dowjones": "Dow Jones", "nasdaq": "Nasdaq"}
    lines: list[str] = []

    for key, data in us.items():
        label = _escape_md(labels.get(key, key.upper()))
        price = _format_turkish_number(data["price"], decimals=0)
        change = _format_pct_with_emoji(data["change_pct"])
        lines.append(f"• {label}: {price} {change}")

    return "🇺🇸 *ABD BORSA*\n" + "\n".join(lines)


def _build_news_section(news_data: list[dict]) -> str:
    """Haberler bölümünü oluşturur.

    Args:
        news_data: Haber dict'lerinin listesi.

    Returns:
        Formatlanmış metin bloğu veya boş haberler notu.
    """
    if not news_data:
        return "📰 *HABERLER*\nHaber bulunamadı\\."

    lines: list[str] = []
    for item in news_data:
        title = _escape_md(item["title"])
        link = item["link"]
        source = _escape_md(item.get("source", ""))
        lines.append(f"• [{title}]({link}) — {source}")

    return "📰 *HABERLER*\n" + "\n".join(lines)


def _build_date_header() -> str:
    """Tarih başlığı oluşturur (MarkdownV2 uyumlu).

    Returns:
        Escape edilmiş tarih başlığı.
    """
    return _escape_md(_now_istanbul().strftime("%d.%m.%Y"))


def format_metals_only(finance_data: dict) -> str:
    """Sadece altın/gümüş bilgisi — bağımsız mesaj.

    Args:
        finance_data: gold_try, gold_prev, silver_try, silver_prev içeren dict.

    Returns:
        MarkdownV2 formatında altın/gümüş mesajı.
    """
    date_str = _build_date_header()
    section = _build_metals_section(finance_data)
    return f"📊 *{date_str}*\n\n{section}"


def format_forex_only(finance_data: dict) -> str:
    """Sadece döviz bilgisi — bağımsız mesaj.

    Args:
        finance_data: usd, usd_prev, eur, eur_prev içeren dict.

    Returns:
        MarkdownV2 formatında döviz mesajı.
    """
    date_str = _build_date_header()
    section = _build_forex_section(finance_data)
    return f"📊 *{date_str}*\n\n{section}"


def format_bist_only(finance_data: dict) -> str:
    """Borsa bilgisi — bağımsız mesaj.

    Args:
        finance_data: bist100 ve us_markets içeren dict.

    Returns:
        MarkdownV2 formatında borsa mesajı.
    """
    date_str = _build_date_header()
    sections = [_build_bist_section(finance_data)]
    us = _build_us_markets_section(finance_data)
    if us:
        sections.append(us)
    return f"📊 *{date_str}*\n\n" + "\n\n".join(sections)


def format_crypto_only(crypto_data: dict) -> str:
    """Kripto bilgisi — bağımsız mesaj.

    Args:
        crypto_data: coin_id -> {price_usd, price_try, change_24h} dict'i.

    Returns:
        MarkdownV2 formatında kripto mesajı.
    """
    date_str = _build_date_header()
    section = _build_crypto_section(crypto_data)
    return f"📊 *{date_str}*\n\n{section}"


def format_news_only(news_data: list[dict]) -> str:
    """Haberler — bağımsız mesaj.

    Args:
        news_data: Haber dict'lerinin listesi.

    Returns:
        MarkdownV2 formatında haber mesajı.
    """
    date_str = _build_date_header()
    section = _build_news_section(news_data)
    return f"📊 *{date_str}*\n\n{section}"


def _format_plain_number(value: float, decimals: int = 2) -> str:
    """Sayıyı Türkçe formata çevirir (düz metin, MarkdownV2 escape olmadan).

    Args:
        value: Formatlanacak sayı.
        decimals: Ondalık basamak sayısı.

    Returns:
        Türkçe formatlı sayı metni (ör. "2.057,50").
    """
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")


def _format_pct_plain(change_pct: float) -> str:
    """Yüzde değişimi düz metin emoji ile formatlar (Twitter için).

    Args:
        change_pct: Yüzde değişim değeri.

    Returns:
        Emoji ve yüzde (ör. "📈 +2.50%").
    """
    if change_pct > 0:
        return f"📈 +{change_pct:.2f}%"
    if change_pct < 0:
        return f"📉 {change_pct:.2f}%"
    return "➡️ 0.00%"


def _change_pct_plain(current: float, previous: float) -> str:
    """Mevcut ve önceki değer arasındaki yüzde değişimini düz metin formatlar.

    Args:
        current: Güncel değer.
        previous: Önceki değer.

    Returns:
        Emoji ve yüzde içeren düz metin.
    """
    if previous == 0:
        return _format_pct_plain(0.0)
    change_pct = ((current - previous) / previous) * 100
    return _format_pct_plain(change_pct)


def format_twitter_messages(
    finance_data: dict, crypto_data: dict, news_data: list[dict]
) -> list[str]:
    """Verileri Twitter paylaşımına uygun, birden fazla tweet listesi olarak biçimlendirir.

    Her tweet ayrı bir Telegram mesajı olarak gönderilir; kullanıcı doğrudan
    kopyalayıp Twitter'da paylaşabilir. Düz metin kullanılır (MarkdownV2 yok).

    Args:
        finance_data: Finans verileri dict'i.
        crypto_data: Kripto verileri dict'i.
        news_data: Haber dict'lerinin listesi.

    Returns:
        Twitter'a uygun tweet metinlerinin listesi.
    """
    now = _now_istanbul()
    date_str = now.strftime("%d.%m.%Y")
    tweets: list[str] = []

    # Tweet 1 — Döviz
    usd_line = (
        f"💵 USD/TRY: {_format_plain_number(finance_data['usd'])} "
        f"{_change_pct_plain(finance_data['usd'], finance_data['usd_prev'])}"
    )
    eur_line = (
        f"💶 EUR/TRY: {_format_plain_number(finance_data['eur'])} "
        f"{_change_pct_plain(finance_data['eur'], finance_data['eur_prev'])}"
    )
    tweets.append(
        f"💵 DÖVİZ | {date_str}\n\n"
        f"{usd_line}\n{eur_line}\n\n"
        f"#Dolar #Euro #DovizKuru #USDTRY #Ekonomi"
    )

    # Tweet 2 — Altın & Gümüş
    gold_line = (
        f"🟡 Altın (gram): {_format_plain_number(finance_data['gold_try'])} ₺ "
        f"{_change_pct_plain(finance_data['gold_try'], finance_data['gold_prev'])}"
    )
    silver_line = (
        f"⚪ Gümüş (gram): {_format_plain_number(finance_data['silver_try'])} ₺ "
        f"{_change_pct_plain(finance_data['silver_try'], finance_data['silver_prev'])}"
    )
    tweets.append(
        f"💛 ALTIN & GÜMÜŞ | {date_str}\n\n"
        f"{gold_line}\n{silver_line}\n\n"
        f"#Altin #Gumus #AltinFiyati #Ekonomi"
    )

    # Tweet 3 — Borsa
    bist = finance_data["bist100"]
    bist_line = (
        f"📊 BIST 100: {_format_plain_number(bist['price'], decimals=0)} "
        f"{_format_pct_plain(bist['change_pct'])}"
    )
    borsa_lines = [bist_line]
    us = finance_data.get("us_markets", {})
    us_labels = {"sp500": "S&P 500", "dowjones": "Dow Jones", "nasdaq": "Nasdaq"}
    for key, data in us.items():
        label = us_labels.get(key, key.upper())
        price = _format_plain_number(data["price"], decimals=0)
        change = _format_pct_plain(data["change_pct"])
        borsa_lines.append(f"🇺🇸 {label}: {price} {change}")
    tweets.append(
        f"📈 BORSA | {date_str}\n\n"
        + "\n".join(borsa_lines)
        + "\n\n#BIST100 #Borsa #Hisse #SPX #Nasdaq #Ekonomi"
    )

    # Tweet 4 — Kripto
    crypto_labels = {"bitcoin": "BTC", "ethereum": "ETH"}
    crypto_lines: list[str] = []
    crypto_hashtags: list[str] = ["#Kripto", "#Blockchain"]
    for coin_id, data in crypto_data.items():
        label = crypto_labels.get(coin_id, coin_id.upper())
        price_usd = _format_plain_number(data["price_usd"], decimals=0)
        price_try = _format_plain_number(data["price_try"], decimals=0)
        change = _format_pct_plain(data["change_24h"])
        crypto_lines.append(
            f"• {label}: ${price_usd} ({price_try} ₺) {change}"
        )
        crypto_hashtags.append(f"#{label}")
    if crypto_lines:
        tweets.append(
            f"₿ KRİPTO | {date_str}\n\n"
            + "\n".join(crypto_lines)
            + "\n\n"
            + " ".join(crypto_hashtags)
        )

    return tweets


def format_message(
    finance_data: dict, crypto_data: dict, news_data: list[dict]
) -> str:
    """Tüm verileri birleştirip Telegram mesajı oluşturur.

    Args:
        finance_data: Finans verileri dict'i.
        crypto_data: Kripto verileri dict'i.
        news_data: Haber dict'lerinin listesi.

    Returns:
        Telegram MarkdownV2 formatında mesaj metni (max 4096 karakter).
    """
    now = _now_istanbul()
    date_str = _escape_md(now.strftime("%d.%m.%Y"))

    us_section = _build_us_markets_section(finance_data)

    sections = [
        f"📊 *Günlük Özet — {date_str}*",
        "",
        _build_metals_section(finance_data),
        "",
        _build_forex_section(finance_data),
        "",
        _build_bist_section(finance_data),
    ]

    if us_section:
        sections += ["", us_section]

    sections += [
        "",
        _build_crypto_section(crypto_data),
        "",
        _build_news_section(news_data),
    ]

    message = "\n".join(sections)

    if len(message) > _TELEGRAM_MAX_LENGTH:
        message = message[:_TELEGRAM_MAX_LENGTH - 3] + "\\.\\.\\."
        logger.warning("Mesaj %d karaktere kırpıldı", _TELEGRAM_MAX_LENGTH)

    logger.info("Mesaj oluşturuldu (%d karakter)", len(message))
    return message
