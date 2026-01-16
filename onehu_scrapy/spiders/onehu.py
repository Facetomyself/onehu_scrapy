from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urldefrag

import scrapy

from onehu_scrapy.items import OnehuArticleItem
from onehu_scrapy.state_store import ArticleStateStore


class OnehuSpider(scrapy.Spider):
    name = "onehu"
    allowed_domains = ["onehu.xyz"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state_store: ArticleStateStore | None = None
        self.persisted_urls: set[str] = set()
        self.full_crawl_completed: bool = False

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)

        db_path = crawler.settings.get("ONEHU_STATE_DB", "state/onehu_state.sqlite3")
        spider.state_store = ArticleStateStore(db_path)
        spider.state_store.open()
        spider.persisted_urls = spider.state_store.load_seen_urls()
        spider.full_crawl_completed = spider.state_store.is_full_crawl_completed()

        return spider

    def closed(self, reason) -> None:
        if self.state_store is not None:
            self.state_store.close()

    @staticmethod
    def _normalize_url(url: str) -> str:
        # Strip fragments like "#board" so state/dupe checks are stable.
        return urldefrag(url)[0]

    @staticmethod
    def _now_iso_utc() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _clean_text(chunks: list[str]) -> str:
        lines = []
        for chunk in chunks:
            cleaned = (chunk or "").strip()
            if cleaned:
                lines.append(cleaned)
        return "\n".join(lines)

    def _iter_start_requests(self):
        start_url = self.settings.get("ONEHU_ARCHIVES_START_URL", "https://onehu.xyz/archives/")
        # For incremental runs we want to re-fetch archives even if dupefilter remembers them.
        dont_filter = bool(self.full_crawl_completed)
        yield scrapy.Request(start_url, callback=self.parse_archives, dont_filter=dont_filter)

    def start_requests(self):
        # Backward-compatible hook for Scrapy < 2.13.
        yield from self._iter_start_requests()

    def parse_archives(self, response: scrapy.http.Response):
        hrefs = response.css("div.list-group a.list-group-item::attr(href)").getall()
        if not hrefs:
            self.logger.warning("No archive links found on url=%s", response.url)

        new_links = 0
        for href in hrefs:
            url = self._normalize_url(response.urljoin(href))
            if url in self.persisted_urls:
                continue
            new_links += 1
            yield scrapy.Request(url, callback=self.parse_detail)

        next_href = response.css("#pagination a.extend.next::attr(href)").get()
        if next_href:
            next_url = self._normalize_url(response.urljoin(next_href))

            # First full run: crawl all archive pages until the end.
            if not self.full_crawl_completed:
                yield scrapy.Request(next_url, callback=self.parse_archives, dont_filter=False)
                return

            # Incremental runs: stop once we hit a page with no new article links.
            if new_links > 0:
                yield scrapy.Request(next_url, callback=self.parse_archives, dont_filter=True)
            else:
                self.logger.info("Incremental stop: no new links on url=%s", response.url)
            return

        # No next page. This means we reached the end of archives (full crawl finished).
        if self.state_store is not None and not self.full_crawl_completed:
            self.state_store.mark_full_crawl_completed()
            self.full_crawl_completed = True
            self.logger.info("Full archives crawl completed; future runs will be incremental.")

    def parse_detail(self, response: scrapy.http.Response):
        item = OnehuArticleItem()
        item["url"] = self._normalize_url(response.url)
        item["title"] = response.css('meta[property="og:title"]::attr(content)').get()
        item["tag"] = response.css('meta[property="article:tag"]::attr(content)').get()
        item["published_time"] = response.css('meta[property="article:published_time"]::attr(content)').get()
        item["modified_time"] = response.css('meta[property="article:modified_time"]::attr(content)').get()

        content_sel = response.css("article.post-content .markdown-body")
        item["content_html"] = content_sel.get()
        item["content_text"] = self._clean_text(content_sel.css("::text").getall())
        item["scraped_at"] = self._now_iso_utc()

        yield item
