# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import time
from random import randint

import scrapy
from scrapy import signals

from spy1st.utils import threading_local_var_get, threading_local_var_set
# useful for handling different item types with a single interface
from spy1st.wd import Webdriver


class Spy1StSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class Spy1StDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        # request.meta["proxy"] = "http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2333"

        # request.meta["proxy"] = "133.18.227.47:8080"
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WebDriverDownloaderMiddleware:

    RETRIES = 5

    def __init__(self, settings):
        self._init(settings)
        self.settings = settings

    def _init(self, settings):
        if not threading_local_var_get("webdriver"):
            webdriver = Webdriver.create(proxy=False)
            threading_local_var_set("webdriver", webdriver)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if request.meta["config"].get("platform", 0) == 4:
            return None

        for i in range(self.RETRIES):
            body = None
            try:
                self._webdriver().get(request.url)
                body = self._webdriver().page_source.encode("utf8")
                self._debug()
                break
            except:
                time.sleep(0.5)

                threading_local_var_set("webdriver", None)
                self._init(self.settings)

                if i == self.RETRIES - 1:
                    raise

        response = scrapy.http.HtmlResponse(url=request.url, body=body)  # type: ignore
        response.meta["page_id"] = randint(100000, 1000000)
        logging.info("save %s page: %s id=%s", response.meta["page_type"], response.url, response.meta["page_id"])

        return response
        # return None

    def process_exception(self, request, exception, spider):
        if isinstance(exception, scrapy.exceptions.IgnoreRequest):
            return

    def _debug(self):
        for v in self._webdriver().requests:  # type: ignore
            logging.info("debug request %s %s", v.url, v.response.status_code)

    def _webdriver(self):
        return threading_local_var_get("webdriver")


class WDMiddleware(WebDriverDownloaderMiddleware):
    def process_request(self, request, spider):
        try:
            return super(WDMiddleware, self).process_request(request, spider)
        except:  # noqa
            raise scrapy.exceptions.CloseSpider()  # type: ignore
