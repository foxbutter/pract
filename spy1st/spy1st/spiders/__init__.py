# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import logging
from urllib.parse import urlparse

import scrapy
from scrapy import signals

from spy1st.utils import threading_local_var_get


class CustomSpider(scrapy.Spider):
    CATEGORY_MAX_PAGE_NUMBERS = 8
    SHOP_BRAND_MAX_PAGE_NUMBERS = 25

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    @classmethod
    def get_pure_url(cls, img_url):
        if not img_url:
            return ""

        pr = urlparse(img_url)
        return f"{pr.scheme}://{pr.netloc}{pr.path}"

    def spider_closed(self, spider):
        spider.logger.info("Spider closed: %s", spider.name)

        wd = threading_local_var_get("webdriver")
        if not wd:
            return

        try:
            wd.close()
            wd.quit()
        except Exception as e:
            logging.exception(e)

    @classmethod
    def remove_html_tag(cls, text, main_html_selector, tags=None):
        if not tags:
            tags = ["a", "iframe", "img"]

        for x in tags:
            for y in main_html_selector:
                for z in y.xpath(f".//{x}").extract():
                    text = text.replace(z, "")

        return text
