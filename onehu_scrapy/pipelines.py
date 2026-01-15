"""Pipelines for persistence.

This project keeps dependencies minimal by using:
- SQLite for state (incremental / safe early-stop).
- JSON Lines for exported items.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from itemadapter import ItemAdapter


class OnehuPersistPipeline:
    def __init__(self, output_jsonl_path: str) -> None:
        self._output_path = Path(output_jsonl_path)
        self._fp: TextIO | None = None

    @classmethod
    def from_crawler(cls, crawler):
        output_path = crawler.settings.get("ONEHU_OUTPUT_JSONL", "data/articles.jsonl")
        return cls(output_jsonl_path=output_path)

    def open_spider(self, spider) -> None:
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        # Append for incremental runs. Dedup is enforced via the state store.
        self._fp = self._output_path.open("a", encoding="utf-8", newline="\n")

    def close_spider(self, spider) -> None:
        if self._fp is not None:
            self._fp.close()
            self._fp = None

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get("url")
        if not url:
            return item

        persisted_urls = getattr(spider, "persisted_urls", None)
        is_new = True if persisted_urls is None else url not in persisted_urls

        state_store = getattr(spider, "state_store", None)
        if state_store is not None:
            seen_at = adapter.get("scraped_at") or datetime.now(timezone.utc).isoformat(timespec="seconds")
            state_store.upsert_article(
                url=url,
                title=adapter.get("title"),
                tag=adapter.get("tag"),
                published_time=adapter.get("published_time"),
                modified_time=adapter.get("modified_time"),
                seen_at=seen_at,
            )
            if persisted_urls is not None:
                persisted_urls.add(url)

        if is_new and self._fp is not None:
            self._fp.write(json.dumps(adapter.asdict(), ensure_ascii=False) + "\n")
            self._fp.flush()

        return item
