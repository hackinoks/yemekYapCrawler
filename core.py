from useragents import user_agent_list
import scrapy
import random
import json
import atexit

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

recipesOld = {
    "yemekler": []
}
recipesNew = {
    "yemekler": []
}
recipesExtra = {
    "yemekler": {}
}

prefix = "https://www.nefisyemektarifleri.com/kategori/tarifler/"
MAX_PAGE = 3

old = open("old.json", "w")
new = open("new.json", "w")
extra = open("extra.json", "w")


def createJSON():
    json.dump(recipesOld, old, ensure_ascii=False)
    json.dump(recipesNew, new, ensure_ascii=False)
    json.dump(recipesExtra, extra, ensure_ascii=False)


class ErrbackSpider(scrapy.Spider):
    name = "errback_example"
    start_urls = [
        "corba-tarifleri",
        "kahvaltilik-tarifleri",
        "aperatifler-tarifler",
        "bakliyat-yemekleri",
        "et-yemekleri",
        "yumurta-yemekleri",
        "hizli-yemekler"
    ]

    custom_settings = {
        "CONCURRENT_REQUESTS": 1
    }

    def start_requests(self):
        for u in self.start_urls:
            for page in range(1, MAX_PAGE):
                url = prefix + u + "/page/" + str(page) + "/"
                user_agent = random.choice(user_agent_list)
                yield scrapy.Request(url, callback=self.parse_httpbin,
                                     errback=self.errback_httpbin,
                                     dont_filter=True,
                                     headers={'User-Agent': user_agent})

    def parse_httpbin(self, response):
        self.logger.info(
            'Got successful response from {}'.format(response.url))
        foodsOnPage = response.selector.xpath(
            '//div[@class="post-img-div"]/a/@href').getall()
        for foodUrl in foodsOnPage:
            user_agent = random.choice(user_agent_list)
            yield scrapy.Request(foodUrl, callback=self.parse_httpbinfood,
                                 errback=self.errback_httpbin,
                                 dont_filter=True,
                                 headers={'User-Agent': user_agent})

    def parse_httpbinfood(self, response):
        name = response.selector.xpath('//h1[@itemprop="name"]/text()').get()
        selectorIngredients = response.selector.xpath(
            '//div[@class="entry_content tagoninread"]/ul/li[@itemprop="ingredients"]/text()').getall()
        selectorRecipe = response.selector.xpath(
            '//div[@class="entry_content tagoninread"]/ol/li[@itemprop="ingredients"]/text()').getall()
        portion = response.selector.xpath(
            '//span[@itemprop="recipeYield"]/strong/text()').get()
        times = response.selector.xpath(
            '//div[@class="tarif_meta_box"]/span/strong/text()').getall()
        foodType = response.selector.xpath(
            '//a[@class="taxonomy category"]/text()').getall()
        recipesOld["yemekler"].append({
            "isim": name,
            "malzemeler": selectorIngredients,
            "adimlar": selectorRecipe,
            "kisilik": portion,
            "hazirlama": times[0],
            "pisirme": times[1],
            "tur": foodType[1]
        })

        recipesNew["yemekler"].append({
            name: {
                "malzemeler": selectorIngredients,
                "adimlar": selectorRecipe,
                "kisilik": portion,
                "hazirlama": times[0],
                "pisirme": times[1],
                "tur": foodType[1]
            }
        })

    def errback_httpbin(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)


atexit.register(createJSON)
