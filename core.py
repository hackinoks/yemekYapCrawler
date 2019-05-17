import useragents

import scrapy
import random

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class ErrbackSpider(scrapy.Spider):
    name = "errback_example"
    start_urls = [
        "https://www.nefisyemektarifleri.com/kremali-domates-corbasi-5922589/"
    ]

    def start_requests(self):
        for u in self.start_urls:
            yield scrapy.Request(u, callback=self.parse_httpbin,
                                    errback=self.errback_httpbin,
                                    dont_filter=True,
                                    headers={'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'})

    def parse_httpbin(self, response):
        self.logger.info('Got successful response from {}'.format(response.url))
        selectorStuff = response.selector.xpath('//div[@class="entry_content tagoninread"]/ul/li[@itemprop="ingredients"]/text()').getall()
        selectorIngredients = response.selector.xpath('//div[@class="entry_content tagoninread"]/ol/li[@itemprop="ingredients"]/text()').getall()

        return {selectorStuff, selectorIngredients}


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