import json
import json
import logging
import random
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qsl

import scrapy

from spy1st.items import SpiderGoodsItem, SpiderGoodsSkuItem, SpiderGoodsSkuImgItem, SpiderGoodsSizeItem, \
    SpiderPageItem, SpiderGoodsImgItem
from spy1st.spiders import CustomSpider


class RakutenSpider(CustomSpider):
    name = 'rakuten'
    STOCKING_MAPPING = {
        "在庫なし": 0,
        "残りわずか": 1,
        "在庫あり": 4,
        "メーカー在庫あり(取り寄せ)": 0,
    }
    STANDARD_PRICE_PATTERN = re.compile(r"\D*([\d|,]+)円.*")
    SIZE_PATTERN = re.compile(r"\s*([\S|\s]+)\s*/\s*")

    # 指定当前爬虫的配置
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "spy1st.middlewares.Spy1StDownloaderMiddleware": 543,
        },
        "ITEM_PIPELINES": {
            'spy1st.pipelines.SpiderGoodsPipeline': 400,
        }
    }
    PROXY = "http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2333"

    def start_requests(self):
        # for v in Config.load().rakuten_all:
        # yield scrapy.Request(
        #     url=self._goods_list_url("https://brandavenue.rakuten.co.jp/ba/shop-celford/"),
        #     callback=self.parse,
        #     meta={"page_type": 1, "config": {"platform": const.PlatformType.PLATFORM_RAKUTEN}},
        # )
        # yield scrapy.Request(
        #     url=self._goods_list_url("https://brandavenue.rakuten.co.jp/brand-Eytys/"),
        #     callback=self.parse,
        #     meta={"page_type": 1, "config": {"platform": const.PlatformType.PLATFORM_RAKUTEN}},
        # )
        # yield scrapy.Request(
        #     url=self._goods_list_url("https://brandavenue.rakuten.co.jp/all-sites/cateb-0000000019/catem-0000000011/"),
        #     callback=self.parse,
        #     meta={"page_type": 1, "config": {"platform": const.PlatformType.PLATFORM_RAKUTEN}},
        # )
        yield scrapy.Request(
            url=self._goods_list_url("https://brandavenue.rakuten.co.jp/categorylist/"),
            callback=self.parse,
            meta={"page_type": 3, "shop_id": 999, "config": {"platform": 4}},
        )
        # yield scrapy.Request(
        #     url="https://brandavenue.rakuten.co.jp/item/DB1499/",
        #     callback=self.parse,
        #     meta={"page_type": 2, "shop_id": 999, "config": {"platform": 4}},
        # )
        print("!!!!!!!!!!!!!!!!!!!")

    def parse(self, response):
        methods = {
            1: (self._process_list,),
            2: (self._fetch_coordinate, self._extract_goods),
            3: (self._extract_cats,),
        }
        for method in methods[response.meta.get("page_type")]:
            for v in method(response):
                print("-------------------")
                yield v

    def _extract_cats(self, response):
        for dl in response.xpath("//li[@class='category_list_detail']/dl"):
            pc = dl.xpath("./dt/a/text()").extract_first()
            for cx in dl.xpath("./dd//li/a/text()").extract():
                print(f"{pc} > {cx}")
        print("end.............")

    def _extract_goods(self, response) -> object:
        # 解析goods/sku > item
        brand_domain = "brandavenue.rakuten.co.jp"
        item_domain = "item.rakuten.co.jp"

        return self._extract_goods_domain_brand(response)
        # domain = self._goods_detail_page_domain(response)

        # if brand_domain == domain:
        #     return self._extract_goods_domain_brand(response)
        #
        # if item_domain == domain:
        #     return self._extract_goods_domain_item(response)
        #
        # return []

    def _extract_goods_domain_brand(self, response):
        yield SpiderPageItem(
            platform=response.meta["config"].get("platform", 0),
            raw_html=response.body,
            url=response.url,
            page_type=response.meta["page_type"],
            meta=response.meta,
        )

        now = datetime.now()
        main_html = response.xpath("//main")

        shop_brand_categories_xpath = ".//div[@class='related-content']/ul//a"
        spu_no_meta = (
            main_html.xpath(".//div[@class='item-info']/div[@class='item-sku-actions']/@data-model")
            .extract_first(default="")
            .strip()
        )
        yuyue = (
            main_html.xpath(".//div[@class='item-info']//ul[@class='item-tags-list clearfix']")
            .extract_first(default="")
            .strip()
        )
        xxx = main_html.xpath(shop_brand_categories_xpath)
        if not xxx or not spu_no_meta or "予約" in yuyue:
            logging.info("the goods is not match spider configs: %s", xxx)
            return []

        desc_abouts = main_html.xpath(
            ".//div[@class='item-info']//div[@class='item-detail']//div[@class='item-detail-item']"
        ).extract()[0:2]
        x = "".join(desc_abouts).strip().replace("原産国", "原産地")
        specs = self._extract_specs(main_html)
        spu_no = f"{response.meta['shop_id']}_{spu_no_meta}"
        desc_abouts = main_html.xpath(
            ".//div[@class='item-info']//div[@class='item-detail']//div[@class='item-detail-item']"
        ).extract()[0:2]
        desc = '<div class="contbox">' + "".join(desc_abouts).strip().replace("原産国", "原産地") + '</div>'
        desc = self.remove_html_tag(desc, main_html.xpath(".//div[@class='item-info']//div[@class='item-detail']//div[@class='item-detail-item']"))

        yield SpiderGoodsItem(
            platform=4,
            goods_no=spu_no,
            shop=xxx[0].css("a::text").extract_first(default="").strip(),
            brand=xxx[1].css("a::text").extract_first(default=""),
            category=f"{xxx[2].css('a::text').extract_first(default='').strip()} > {xxx[3].css('a::text').extract_first(default='').strip()}",
            name=main_html.xpath(".//div[@class='item-info']//h1/text()").extract_first(default='').strip(),
            gender=json.dumps(specs.get("性別タイプ", [])),
            description=x,
            price=self._extract_prices(
                main_html, ".//div[@class='item-info']//div[@class='item-price']/p[@class='item-our-price']/span[1]"
            ),
            standard_price=self._extract_prices(
                main_html, ".//div[@class='item-info']//div[@class='item-price']/p[@class='item-listing-price']"
            ),
            material=specs.get("素材", ""),
            made_in=specs.get("原産国", ""),
            # time_sale_end_time = scrapy.Field()
            favorite_count=main_html.xpath(".//div[@class='favorite-count-text']/span/span/text()")
            .extract_first(default='')
            .strip()
            .replace("人", "")
            .replace(",", "")
            or 0,
            # category_tags = scrapy.Field()
            # rank = scrapy.Field()
            # page_id = scrapy.Field(),
            # updated_at=now,
            meta_url=response.url,
        )

        colors = main_html.xpath(
            ".//div[@class='item-info']//div[@class='item-sku-actions']//dl[@class='item-sku-actions-color']"
        )
        for color in colors:
            style_meta = color.xpath("./dt[@class='item-sku-actions-color-thumbnail']/img")
            style_str = style_meta.xpath("./@alt").extract_first(default='').strip()
            style_img_url = response.urljoin(style_meta.xpath("./@src").extract_first(default='').strip())
            for size_meta in color.xpath("./dd[@class='item-sku-actions-color-action']//li"):
                size = self._extract_sku_size(size_meta.xpath("./div[@class='item-sku-actions-info']/text()").extract())
                quantity = self._extract_sku_stock(
                    size_meta.xpath("./div[@class='item-sku-actions-info']/span/text()").extract()
                )
                sku_meta = (
                    size_meta.xpath("./div[@class='item-sku-actions-wishlist']/a/@id").extract_first(default='').strip()
                )
                sku_no = f"{response.meta['shop_id']}_{sku_meta}"
                yield SpiderGoodsSkuItem(
                    platform=4,
                    goods_sku_no=sku_no,
                    goods_no=spu_no,
                    style=style_str,
                    size=size,
                    quantity=quantity,
                    updated_at=now,
                )

                yield SpiderGoodsSkuImgItem(
                    platform=4,
                    goods_no=spu_no,
                    goods_sku_no=sku_no,
                    style=style_str,
                    url=style_img_url,
                    updated_at=now,
                )

        img_rank_map = dict()
        lis = main_html.xpath(".//div[@class='item-images-container']//ul/li")
        for rank, spu_img_sl in enumerate(lis):
            if rank < len(colors):
                continue
            spu_img = response.urljoin(spu_img_sl.xpath("./img/@src").extract_first(default="").strip())
            if img_rank_map.get(spu_img):
                continue
            img_rank_map[spu_img] = rank

        yield SpiderGoodsImgItem(
            platform=response.meta["config"].get("platform", 0),
            goods_no=spu_no,
            url_rank=json.dumps(img_rank_map),
            updated_at=now,
        )

        sizes_meta = main_html.xpath(
            ".//div[@class='item-info']//div[@class='item-detail']//div[@class='item-detail-item'][2]/div[@class='item-detail-content']/table//tr"
        )
        for cxys in sizes_meta[1:]:
            xys = cxys.xpath("./td/text()")
            captions = sizes_meta[0].xpath("./td/text()")
            for caption_meta, y in zip(captions[1:], xys[1:]):
                x = SpiderGoodsSizeItem(
                    platform=response.meta["config"].get("platform", 0),
                    goods_no=spu_no,
                    caption=caption_meta.extract().strip(),
                    x=xys[0].extract().strip(),
                    y=y.extract().strip(),
                    updated_at=now,
                )
                yield x

    def _extract_specs(self, desc_ss):
        specs = {}
        dtdd = desc_ss.xpath(
            ".//div[@class='item-info']//div[@class='item-detail']//div[@class='item-detail-item'][1]//div[@class='item-detail-content']/dl"
        )
        for dt, dd in zip(dtdd.xpath(".//dt"), dtdd.xpath(".//dd")):
            key = dt.css("dt::text").extract_first(default="").strip()
            n = "".join(dd.css("dd::text").extract())

            if key == "性別タイプ":
                val = self._extract_genders(n)
            elif "素材" == key:
                val = n
            elif key == "原産国":
                val = n
            else:
                continue

            specs[key] = val

        return specs

    def _extract_genders(self, g):
        GENDER_MAPPING = {
            "メンズ": 1,
            "レディース": 2,
            "キッズ": 3,
        }
        return [GENDER_MAPPING.get(g.strip(), 0)]

    def _extract_goods_domain_item(self, response):
        # purchase_table_xpath = response.xpath(
        #     "//*[@id='rakutenLimitedId_aroundCart']/parent::*/parent::*/parent::*/parent::*"
        # )
        categories_xpath = response.xpath("//*[@class='rGenreTreeDiv']/a")

        # category = response.css(".c-catalog-body__caption::text").extract_first("")
        # brand = response.css(".c-catalog-body__title::text").extract_first("")
        # shop = (response.url.split("/")[2:3] + [""])[0]
        # if response.meta["config"] and not response.meta["config"].validate(category, brand, shop):
        #     logging.info("the goods is not match spider configs: %s", href)
        #     return
        print(f"{categories_xpath.extract()=}")
        return []

    def _fetch_coordinate(self, response):
        return []

    def _process_list(self, response):
        print(f"process list: {response.url=}")
        other_pages_xpath = "//div[@id='paragraph']//ul[@class='tlb_paging']//a/@href"
        urls = [response.urljoin(href) for href in response.xpath(other_pages_xpath).extract()]
        for url in self._other_pages(urls):
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "page_type": 1,
                    "config": response.meta["config"],
                },
            )

        for n in response.xpath("//div[@id='paragraph']//li[@data-ratid]"):
            # href = n.css(".//div[@class='content title']//a/@href").extract_first("")
            href = n.xpath(".//a/@href").extract_first("")
            if not href:
                continue

            # <div class="favorite dui-menu-item" data-shop-id="279405" data-id="12002919" ...
            # data-track-itemid

            # if not ZozoPage.expired(PageType.DETAIL, url):
            #     logging.info("goods detail not expired: %s", url)
            #     continue

            shop_item_id = n.xpath("./@data-ratid").extract_first("").strip()
            yield scrapy.Request(
                url=self.get_pure_url(href),
                callback=self.parse,
                meta={
                    "page_type": 2,
                    "shop_id": shop_item_id.split("/")[0],
                    "shop_spu": shop_item_id,
                    "config": response.meta["config"],
                },
            )

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
            logging.info("total pages cnt >= %s,  urls: %s", last_page_no, page_urls)

        urls = [url for page_no, url in pages.items() if page_no <= page_no_limit]
        return urls

    def _page_no(self, url):
        return int(dict(parse_qsl(urlparse(url).query)).get("page", 1))

    def _page_no_limit(self, page_urls):
        if not page_urls:
            return self.SHOP_BRAND_MAX_PAGE_NUMBERS

        url = page_urls[-1]
        return self.CATEGORY_MAX_PAGE_NUMBERS if "category" in url else self.SHOP_BRAND_MAX_PAGE_NUMBERS

    def _goods_list_url(self, url):
        # return f"{url}&s=5&used=0&p_stype=1&dord=71&displaycolor=1"
        return f"{url}?sort=2&inventory_flg=1&sale=0&used=0&displaycolor={random.randint(10000, 1000000)}"

    def _goods_detail_page_domain(self, response):
        return urlparse(response.url).hostname

    def _extract_prices(self, main_html, xpath_):
        price = main_html.xpath(xpath_).extract_first(default='').strip()
        if not price:
            return ""

        matched = self.STANDARD_PRICE_PATTERN.match(price)

        return matched.group(1).replace("円", "").replace(",", "") if matched else ""

    def _extract_sku_size(self, size_str_ls):
        for x in size_str_ls:
            matched = self.SIZE_PATTERN.match(x)
            if matched:
                return matched.group(1).strip()
        return ""

    def _extract_sku_stock(self, stock_str_ls):
        return self.STOCKING_MAPPING.get(stock_str_ls[-1].strip(), 0)
