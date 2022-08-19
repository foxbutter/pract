# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Spy1StItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    name_jp = scrapy.Field()
    cat = scrapy.Field()
    url = scrapy.Field()
    img_url = scrapy.Field()


class SpiderPageItem(scrapy.Item):
    # define the fields for your item here like:
    platform = scrapy.Field()
    raw_html = scrapy.Field()
    url = scrapy.Field()
    page_type = scrapy.Field()
    meta = scrapy.Field()


class SpiderGoodsItem(scrapy.Item):
    #   `description_zh` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    #   `rank` int NOT NULL DEFAULT '999999999',
    #   `availability_status` tinyint unsigned NOT NULL DEFAULT '0' COMMENT '可用状态',
    platform = scrapy.Field()
    goods_no = scrapy.Field()
    shop = scrapy.Field()
    brand = scrapy.Field()
    category = scrapy.Field()
    name = scrapy.Field()
    gender = scrapy.Field()
    description = scrapy.Field()
    standard_price = scrapy.Field()
    price = scrapy.Field()
    material = scrapy.Field()
    made_in = scrapy.Field()
    time_sale_end_time = scrapy.Field()
    favorite_count = scrapy.Field()
    category_tags = scrapy.Field()
    rank = scrapy.Field()
    meta_url = scrapy.Field()
    updated_at = scrapy.Field()


class SpiderGoodsSkuItem(scrapy.Item):
    platform = scrapy.Field()
    goods_no = scrapy.Field()
    goods_sku_no = scrapy.Field()
    style = scrapy.Field()
    size = scrapy.Field()
    quantity = scrapy.Field()
    updated_at = scrapy.Field()


class SpiderGoodsSizeItem(scrapy.Item):
    platform = scrapy.Field()
    goods_no = scrapy.Field()
    caption = scrapy.Field()
    x = scrapy.Field()
    y = scrapy.Field()
    updated_at = scrapy.Field()


class SpiderGoodsSkuImgItem(scrapy.Item):
    platform = scrapy.Field()
    goods_no = scrapy.Field()
    goods_sku_no = scrapy.Field()
    style = scrapy.Field()
    url = scrapy.Field()
    updated_at = scrapy.Field()


class SpiderGoodsImgItem(scrapy.Item):
    platform = scrapy.Field()
    goods_no = scrapy.Field()
    url_rank = scrapy.Field()
    updated_at = scrapy.Field()
