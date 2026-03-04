"""Financial news fetcher via RSS feeds."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup

from analyst.core.types import NewsItem

logger = logging.getLogger(__name__)

# RSS feed configuration - reliable, free, no API key needed
NEWS_FEEDS: dict[str, dict[str, str]] = {
    "google_finance_de": {
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtUmxHZ0pFUlNnQVAB",
        "source_name": "Google News",
    },
    "yahoo_finance": {
        "url": "https://finance.yahoo.com/news/rssindex",
        "source_name": "Yahoo Finance",
    },
    "marketwatch": {
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "source_name": "MarketWatch",
    },
    "cnbc_world": {
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "source_name": "CNBC",
    },
}


class NewsSource:
    """Fetches financial news from multiple RSS feeds."""

    def __init__(self, max_age_hours: int = 24, max_items_per_feed: int = 10):
        self.max_age_hours = max_age_hours
        self.max_items_per_feed = max_items_per_feed

    async def fetch_news(
        self,
        feed_keys: list[str] | None = None,
        max_total: int = 25,
        max_age_hours: int | None = None,
    ) -> list[NewsItem]:
        """Fetch news from multiple RSS feeds in parallel.

        Args:
            feed_keys: Which feeds to query (None = all)
            max_total: Maximum total items to return
            max_age_hours: Override default max age filter
        """
        age_hours = max_age_hours or self.max_age_hours
        feeds = feed_keys or list(NEWS_FEEDS.keys())
        tasks = [self._fetch_feed(key, age_hours) for key in feeds if key in NEWS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[NewsItem] = []
        for key, result in zip(feeds, results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch news from {key}: {result}")
            else:
                all_items.extend(result)
                logger.info(f"Fetched {len(result)} items from {key}")

        # Sort by published date (newest first), deduplicate
        all_items.sort(
            key=lambda n: n.published or datetime.min.replace(tzinfo=None),
            reverse=True,
        )
        unique = self._deduplicate(all_items)
        logger.info(f"Total news items: {len(unique)} (after dedup from {len(all_items)})")
        return unique[:max_total]

    async def _fetch_feed(self, feed_key: str, max_age_hours: int) -> list[NewsItem]:
        """Fetch and parse a single RSS feed."""
        feed_config = NEWS_FEEDS[feed_key]
        url = feed_config["url"]
        source_name = feed_config["source_name"]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "FinancialAnalyst/1.0"},
                    follow_redirects=True,
                )
                response.raise_for_status()

            # feedparser is synchronous
            feed = await asyncio.to_thread(feedparser.parse, response.text)

            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            items: list[NewsItem] = []

            for entry in feed.entries[: self.max_items_per_feed]:
                published = self._parse_date(entry)
                if published and published < cutoff:
                    continue

                summary = getattr(entry, "summary", "") or ""
                if summary:
                    summary = BeautifulSoup(summary, "html.parser").get_text()[:300].strip()

                title = entry.get("title", "").strip()
                if not title:
                    continue

                items.append(
                    NewsItem(
                        title=title,
                        source=source_name,
                        published=published,
                        url=entry.get("link", ""),
                        summary=summary,
                    )
                )

            return items

        except Exception as e:
            logger.warning(f"Error fetching {source_name} ({feed_key}): {e}")
            return []

    def _parse_date(self, entry: Any) -> datetime | None:
        """Parse published date from RSS entry."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                return None
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                return datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                return None
        return None

    def _deduplicate(self, items: list[NewsItem]) -> list[NewsItem]:
        """Remove near-duplicate headlines from different sources."""
        seen: set[str] = set()
        unique: list[NewsItem] = []
        for item in items:
            # Normalize: lowercase, strip, first 50 chars
            key = item.title.lower().strip()[:50]
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
