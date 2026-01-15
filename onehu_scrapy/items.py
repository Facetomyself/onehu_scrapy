"""Scrapy item definitions.

Keep items minimal and focused. The spider should yield structured data instead
of raw responses so pipelines/feeds stay stable.
"""

import scrapy


class OnehuArticleItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    tag = scrapy.Field()
    published_time = scrapy.Field()
    modified_time = scrapy.Field()
    content_html = scrapy.Field()
    content_text = scrapy.Field()
    scraped_at = scrapy.Field()
