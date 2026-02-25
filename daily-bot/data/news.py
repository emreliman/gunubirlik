"""Haber verisi çekme modülü.

RSS feed'lerinden feedparser ile haberleri çeker ve temizler.
"""

import logging
import re

import feedparser

from constants import RSS_FEEDS, NEWS_LIMIT_PER_SOURCE

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html(raw_text: str) -> str:
    """Metinden HTML tag'lerini kaldırır ve whitespace'i temizler.

    Args:
        raw_text: Ham metin.

    Returns:
        Temizlenmiş metin.
    """
    stripped = _HTML_TAG_RE.sub("", raw_text)
    return stripped.strip()


def _parse_single_feed(source_name: str, feed_url: str) -> list[dict]:
    """Tek bir RSS kaynağını parse eder.

    Args:
        source_name: Kaynak adı (ör. "Hürriyet").
        feed_url: RSS feed URL'si.

    Returns:
        En fazla NEWS_LIMIT_PER_SOURCE adet haber dict'i.
    """
    feed = feedparser.parse(feed_url)

    items: list[dict] = []
    for entry in feed.entries[:NEWS_LIMIT_PER_SOURCE]:
        raw_title = getattr(entry, "title", None)
        if not raw_title:
            continue

        title = _clean_html(raw_title)
        if not title:
            continue

        items.append({
            "title": title,
            "source": source_name,
            "link": getattr(entry, "link", ""),
            "published": getattr(entry, "published", ""),
        })

    return items


def get_news() -> list[dict]:
    """Tüm RSS kaynaklarından haberleri çeker.

    Her kaynaktan en fazla NEWS_LIMIT_PER_SOURCE adet haber alınır.
    Bir kaynak hata verirse atlanır, diğerlerine devam edilir.

    Returns:
        Haber dict'lerinin listesi.
        Her dict: {"title": str, "source": str, "link": str, "published": str}
    """
    all_news: list[dict] = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            items = _parse_single_feed(source_name, feed_url)
            all_news.extend(items)
            logger.info(
                "%s kaynağından %d haber alındı", source_name, len(items)
            )
        except Exception as exc:
            logger.error(
                "%s kaynağı okunamadı, atlanıyor: %s", source_name, exc
            )
            continue

    logger.info("Toplam %d haber toplandı", len(all_news))
    return all_news
