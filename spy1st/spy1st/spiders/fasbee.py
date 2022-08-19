import scrapy


class FasbeeSpider(scrapy.Spider):
    name = 'fasbee'
    allowed_domains = ['fas-bee.com']
    start_urls = ['http://fas-bee.com/']

    def parse(self, response):
        pass
