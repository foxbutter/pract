import logging
import re
import time
from urllib.parse import urlparse, parse_qsl

import scrapy
from scrapy import signals

from spy1st.utils import threading_local_var_get


class ZozoSpider(scrapy.Spider):
    name = 'zozo'
    # allowed_domains = ['rakuten.co.jp']
    # start_urls = ['http://rakuten.co.jp/']

    gtid_pattern = re.compile(r""".*gtid:\s+['"]*(\d+)['"]*""")
    tcaid_pattern = re.compile(r""".*tcaid:\s+['"]*(\d+)['"]*""")
    shop_id_pattern = re.compile(r""".*shop_id:\s+['"]*(\d+)['"]*""")

    CATEGORY_MAX_PAGE_NUMBERS = 8
    SHOP_BRAND_MAX_PAGE_NUMBERS = 25

    fetch_zozo_size_category_list = (
        "tops",
        "jacket-outerwear",
        "pants",
        "skirt",
        "onepiece",
        "suit",
        "shoes",
        "underwear",
        "loungewear",
    )


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

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

    def start_requests(self):
        # for v in Config.load().rakuten_all:
        yield scrapy.Request(
            url=self._goods_list_url("https://zozo.jp/brand/nanouniverse/", 1),
            callback=self.parse,
            meta={"page_type": 1},
        )

    def parse(self, response):
        print(response)
        # ZozoPage.save_page(response)
        # logging.info("save %s page: %s", PageType.name(response.meta.get("page_type")), response.url)
        #
        methods = {
            1: (self._process_list,),
        }
        for method in methods[response.meta.get("page_type")]:
            for v in method(response):
                yield v

    def _fetch_coordinate(self, response):
        # # TODO 初期控制抓取次数, 否则会影响 goods 抓取
        # if randint(1, 100) > 1:
        #     return []
        #
        # goods_id = self._parse_goods_id(response)
        # shop_id = self._search_shop_id(response)
        # if not shop_id:
        #     logging.error("can not find shop_id, url: %s", response.url)
        #     return []
        #
        # logging.info("fetch coordinate for goods: %s", response.url)
        #
        # url = self._coordinate_url(goods_id, shop_id)
        # if not ZozoPage.expired(PageType.COORDINATE, url):
        #     logging.info("coordinate not expired: %s", url)
        #     return []
        #
        # yield scrapy.Request(
        #     url=url,
        #     callback=self.parse,
        #     meta={
        #         "page_type": PageType.COORDINATE,
        #         "goods_id": goods_id,
        #         "config": response.meta["config"],
        #     },
        # )
        pass

    def _has_zozo_size(self, response):
        v = response.css(
            "div.p-goods-information-spec a.p-goods-information-spec-category-list-item__link::attr(href)"
        ).extract_first("")
        return (v.split("/")[2:3] + [""])[0] in self.fetch_zozo_size_category_list

    def _process_zozo_size(self, response):
        return []

    def _process_coordinate(self, response):
        # TODO 解析JSON存储到数据库, 参考 _process_zozo_size
        return []

    def _search_shop_id(self, response):
        for s in response.css("script::text").extract():
            m = self.shop_id_pattern.search(s)
            if m:
                return m.group(1)
        return 0

    def _search_gtid_tcaid(self, response):
        for s in response.css("script::text").extract():
            m1 = self.gtid_pattern.search(s)
            if not m1:
                continue

            m2 = self.tcaid_pattern.search(s)
            if not m2:
                continue

            return m1.group(1), m2.group(1)

        return 0, 0

    def _parse_goods_id(self, response):
        return urlparse(response.url).path.strip("/").split("/")[-1]

    def _zozo_size_mapping_url(self, goods_id, gtid, tcaid):
        return f"https://zozo.jp/?command=GetSizeMappinngList&gid={goods_id}&gtid={gtid}&gtcid={tcaid}"

    def _coordinate_url(self, goods_id, shop_id):
        ts = int(time.time() * 1000)
        return f"https://zozo.jp/?command=Goods_CdRelationList&cd_gid={goods_id}&cd_shid={shop_id}&_={ts}"

    def _process_list(self, response):
        other_pages_xpath = "div.p-search-pager ol.c-pager-page-number-list li a::attr(href)"
        urls = [response.urljoin(href) for href in response.css(other_pages_xpath).extract()]
        for url in self._other_pages(urls):
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "page_type": 1,
                    "config": response.meta["config"],
                },
            )

        # for n in response.css("div.p-search-list div.c-catalog"):
        #     href = n.css(".c-catalog-header a::attr(href)").extract_first("")
        #     if not href:
        #         continue
        #
        #     category = n.css(".c-catalog-body__caption::text").extract_first("")
        #     brand = n.css(".c-catalog-body__title::text").extract_first("")
        #     shop = (href.split("/")[2:3] + [""])[0]
        #     if response.meta["config"] and not response.meta["config"].validate(category, brand, shop):
        #         logging.info("the goods is not match spider configs: %s", href)
        #         continue
        #
        #     url = response.urljoin(href)
        #     if not ZozoPage.expired(PageType.DETAIL, url):
        #         logging.info("goods detail not expired: %s", url)
        #         continue
        #
        #     yield scrapy.Request(
        #         url=url,
        #         callback=self.parse,
        #         meta={
        #             "page_type": PageType.DETAIL,
        #             "config": response.meta["config"],
        #         },
        #     )

    def _other_pages(self, page_urls):
        if not page_urls:
            return page_urls

        pages = dict()
        last_page_no = 1
        for url in page_urls:
            pages[self._page_no(url)] = url
            last_page_no = max(last_page_no, self._page_no(url))

        page_no_limit = self._page_no_limit(page_urls)

        if last_page_no > page_no_limit:
            logging.info("total pages: %s,  urls: %s", last_page_no, page_urls)

        return [url for page_no, url in pages.items() if page_no <= page_no_limit]

    def _page_no(self, url):
        return int(dict(parse_qsl(urlparse(url).query)).get("pno", 1))

    def _goods_list_url(self, url, page_no):
        url = f"{url}?p_stype=1&dord=71&displaycolor=1&pno={page_no}"
        return url

    def _page_no_limit(self, page_urls):
        if not page_urls:
            return self.SHOP_BRAND_MAX_PAGE_NUMBERS

        url = page_urls[-1]
        return self.CATEGORY_MAX_PAGE_NUMBERS if "category" in url else self.SHOP_BRAND_MAX_PAGE_NUMBERS
