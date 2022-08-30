# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from spy1st.items import SpiderPageItem


class Spy1StPipeline:

    def open_spider(self, spider):
        # self.of = open("r.txt", "a", encoding="utf-8")
        return None

    def process_item(self, item, spider):
        # if not isinstance(item, Spy1StItem):
        #     return item
        #
        # self.of.write(str(item))
        print("...")
        return item

    def close_spider(self, spider):
        # self.of.close()
        return None


class SpiderGoodsPipeline:

    def open_spider(self, spider):
        # self.of = open("r.txt", "a", encoding="utf-8")
        pass

    def process_item(self, item, spider):
        # self.of.write(str(item))
        # urllib.request.urlretrieve(item.url)
        # if isinstance(item, SpiderGoodsItem):
        #     print(f"{type(item)} {dict(item)}")
        #
        # elif isinstance(item, SpiderGoodsSkuItem):
        #     print(f"{type(item)} {dict(item)}")
        #
        # elif isinstance(item, SpiderGoodsSkuImgItem):
        #     print(f"{type(item)} {dict(item)}")
        #
        # elif isinstance(item, SpiderGoodsSizeItem):
        #     print(f"{type(item)} {dict(item)}")
        #
        if isinstance(item, SpiderPageItem):
            kwargs = dict(item)
            print(f"{type(item)} {dict(item)}")
            print(f"{dict(item).get('raw_html')=}")

        # else:
        #     raise ValueError(item)
        return item

    def close_spider(self, spider):
        # self.of.close()
        pass
