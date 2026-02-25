from unittest.mock import patch, MagicMock

from data.news import get_news
from constants import NEWS_LIMIT_PER_SOURCE


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_feed_entry(
    title: str | None = "Test Haber",
    link: str = "https://example.com/haber",
    published: str = "Tue, 25 Feb 2026 09:00:00 GMT",
) -> MagicMock:
    """Tek bir feedparser entry mock'u oluşturur."""
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.published = published
    return entry


def _make_feed(entries: list, bozo: int = 0) -> MagicMock:
    """feedparser.parse dönüşünü taklit eden mock."""
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = bozo
    return feed


# ---------------------------------------------------------------------------
# get_news
# ---------------------------------------------------------------------------

class TestGetNews:
    @patch("data.news.feedparser.parse")
    def test_returns_limited_items_per_source(self, mock_parse):
        entries = [
            _make_feed_entry(title=f"Haber {i}", link=f"https://example.com/{i}")
            for i in range(10)
        ]
        mock_parse.return_value = _make_feed(entries)

        result = get_news()

        assert isinstance(result, list)
        sources = {item["source"] for item in result}
        for source in sources:
            source_items = [item for item in result if item["source"] == source]
            assert len(source_items) <= NEWS_LIMIT_PER_SOURCE

        for item in result:
            assert "title" in item
            assert "source" in item
            assert "link" in item
            assert "published" in item

    @patch("data.news.feedparser.parse")
    def test_returns_empty_list_on_empty_feed(self, mock_parse):
        mock_parse.return_value = _make_feed([])

        result = get_news()

        assert result == []

    @patch("data.news.feedparser.parse")
    def test_skips_failing_source_continues_others(self, mock_parse):
        good_entries = [
            _make_feed_entry(title=f"İyi Haber {i}", link=f"https://good.com/{i}")
            for i in range(5)
        ]
        good_feed = _make_feed(good_entries)

        def side_effect(url):
            if "hurriyet" in url:
                raise Exception("Connection error")
            return good_feed

        mock_parse.side_effect = side_effect

        result = get_news()

        assert len(result) > 0
        hurriyet_items = [item for item in result if item["source"] == "Hürriyet"]
        assert len(hurriyet_items) == 0

    @patch("data.news.feedparser.parse")
    def test_filters_out_entries_with_none_title(self, mock_parse):
        entries = [
            _make_feed_entry(title=None, link="https://example.com/no-title"),
            _make_feed_entry(title="Gerçek Haber", link="https://example.com/real"),
            _make_feed_entry(title="", link="https://example.com/empty"),
        ]
        mock_parse.return_value = _make_feed(entries)

        result = get_news()

        titles = [item["title"] for item in result]
        assert None not in titles
        assert "" not in titles
        assert "Gerçek Haber" in titles

    @patch("data.news.feedparser.parse")
    def test_strips_whitespace_from_titles(self, mock_parse):
        entries = [
            _make_feed_entry(
                title="  Boşluklu Başlık  ", link="https://example.com/ws"
            ),
        ]
        mock_parse.return_value = _make_feed(entries)

        result = get_news()

        assert result[0]["title"] == "Boşluklu Başlık"

    @patch("data.news.feedparser.parse")
    def test_strips_html_tags_from_titles(self, mock_parse):
        entries = [
            _make_feed_entry(
                title="<b>Kalın</b> ve <i>italik</i> başlık",
                link="https://example.com/html",
            ),
        ]
        mock_parse.return_value = _make_feed(entries)

        result = get_news()

        assert "<b>" not in result[0]["title"]
        assert "<i>" not in result[0]["title"]
        assert "Kalın ve italik başlık" == result[0]["title"]

