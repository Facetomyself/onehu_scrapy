# Scrapy settings for onehu_scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "onehu_scrapy"

SPIDER_MODULES = ["onehu_scrapy.spiders"]
NEWSPIDER_MODULE = "onehu_scrapy.spiders"

# This site serves plain HTML. A common desktop UA reduces the chance of being blocked.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Keep a small delay to be polite; adjust if you need higher throughput.
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure item pipelines
ITEM_PIPELINES = {
    "onehu_scrapy.pipelines.OnehuPersistPipeline": 300,
}

# Persist scheduler and dupefilter state to disk so the crawl can resume after interruption.
JOBDIR = "state/jobdir"
# Keep the legacy priority queue for compatibility with existing JOBDIR state.
SCHEDULER_PRIORITY_QUEUE = "scrapy.pqueues.ScrapyPriorityQueue"

# Project-specific settings
ONEHU_ARCHIVES_START_URL = "https://onehu.xyz/archives/"
ONEHU_STATE_DB = "state/onehu_state.sqlite3"
ONEHU_OUTPUT_JSONL = "data/articles.jsonl"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
