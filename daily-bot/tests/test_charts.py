"""Grafik üretimi modülü testleri."""

from unittest.mock import patch

import pytest

from data.charts import generate_asset_chart_png


class TestGenerateAssetChartPng:
    """generate_asset_chart_png fonksiyonu testleri."""

    @patch("data.charts._render_chart_png", return_value=b"png-bytes")
    @patch(
        "data.charts._fetch_btc_prices_try",
        return_value=[
            ("2026-02-01", 100.0),
            ("2026-02-02", 110.0),
        ],
    )
    def test_returns_bytes_and_caption_for_btc(
        self, mock_fetch, mock_render
    ) -> None:
        image_bytes, caption = generate_asset_chart_png("btc", "1a")

        assert image_bytes == b"png-bytes"
        assert "BTC" in caption
        mock_fetch.assert_called_once_with(30)
        mock_render.assert_called_once()

    @patch("data.charts._render_chart_png", return_value=b"png-bytes")
    @patch(
        "data.charts._fetch_gold_prices_try",
        return_value=[
            ("2026-02-01", 2000.0),
            ("2026-02-02", 1980.0),
        ],
    )
    def test_returns_bytes_and_caption_for_gold(
        self, mock_fetch, mock_render
    ) -> None:
        image_bytes, caption = generate_asset_chart_png("altin", "1h")

        assert image_bytes == b"png-bytes"
        assert "Altin" in caption
        mock_fetch.assert_called_once_with(7)
        mock_render.assert_called_once()

    def test_raises_on_invalid_asset(self) -> None:
        with pytest.raises(ValueError):
            generate_asset_chart_png("gumus", "1h")

    def test_raises_on_invalid_period(self) -> None:
        with pytest.raises(ValueError):
            generate_asset_chart_png("btc", "3ay")
