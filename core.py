from statics import user_agent_list, ingredientFilter, nameFilter
import re
import scrapy
import random
import json
import atexit

from itertools import filterfalse

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

recipesOld = []
recipesNew = {
    "yemekler": {}
}
recipesExtra = {
    "yemekler": {}
}

foodTypes = []
foodNames = []

prefix = "https://www.nefisyemektarifleri.com/kategori/tarifler/"
MAX_PAGE = 30

old = open("old.json", "w")
new = open("new.json", "w")
extra = open("extra.json", "w")


# DO NOT USE DICTS ON FILTERS, HASH FUNCTION FUCKS OUR TURKISH CHARACTERS


def createJSON():
    json.dump(recipesOld, old, ensure_ascii=False)
    json.dump(recipesNew, new, ensure_ascii=False)
    recipesExtra["types"] = foodTypes
    json.dump(recipesExtra, extra, ensure_ascii=False)


def checkAfiyet(recipe):
    for filter in ["afiyet", "youtube", "instagram"]:
        if filter in recipe.lower():
            return False
    return True


def checkTurkish(s):
    return re.sub(r'[^A-Za-z0-9ğüşıöçİĞÜŞÖÇ\-\ ]', '', s)


def checkTurkishForName(s):
    return re.sub(r'[^A-Za-zğüşıöçİĞÜŞÖÇ\ ]', '', s)


def checkIngredients(s):
    return re.sub(r'[^A-Za-zğüşıöçİĞÜŞÖÇ\ ]', '', s)


def checkName(s):
    parsed = s.split(" ")
    for filter in nameFilter:
        for i in range(len(parsed)):
            if parsed[i].lower() == filter:
                parsed[i] = ""
    return checkTurkishForName(" ".join(parsed)).strip()


def removeSpaces(s):
    return re.sub(' +', ' ', s)


def removeParanthesis(s):
    return str(re.sub("[\(\[].*?[\)\]]", "", s)).strip()


def checkIngredientsForDb(ingredients):
    new = []
    for i in range(len(ingredients)):
        parsed = ingredients[i].split(" ")
        if len(parsed) > 5:
            continue
        for j in range(len(parsed)):
            if checkIngredients(parsed[j].lower()) in ingredientFilter:
                parsed[j] = None
        result = checkIngredients(
            " ".join(item for item in parsed if item)).strip().lower()
        if result != "":
            new.append(result)

    return new


def clearRecipe(recipe):
    return [checkTurkish(x) for x in recipe if checkAfiyet(x)]


class ErrbackSpider(scrapy.Spider):
    name = "errback_example"
    start_urls = [
        "aperatifler-tarifler/cig-kofte-tarifleri/etli-cig-kofte-tarifleri",
        "aperatifler-tarifler/cig-kofte-tarifleri/etsiz-cig-kofte-tarifleri",
        "bakliyat-yemekleri",
        "cocuk-yemekleri",
        "corba-tarifleri",
        "diger-tarifler/baharat-yapimi",
        "diger-tarifler/derin-dondurucuda-saklananlar",
        "diger-tarifler/dondurulmus-yemekler",
        "diger-tarifler/kis-hazirliklari-diger-tarifler",
        "diger-tarifler/pekmez-tarifleri",
        "diger-tarifler/recel-tarifleri",
        "diger-tarifler/salamura-tarifleri",
        "diger-tarifler/sos-tarifleri",
        "diger-tarifler/sut-urunleri",
        "diger-tarifler/tursu-tarifleri",
        "diyet",
        "et-yemekleri/balik-deniz-urunleri",
        "et-yemekleri/kebap-tarifleri",
        "et-yemekleri/kirmizi-et-yemekleri",
        "et-yemekleri/kofte-tarifleri-2",
        "et-yemekleri/sakatat-yemekleri",
        "et-yemekleri/tavuk-yemekleri",
        "hamurisi-tarifleri/borek-tarifleri",
        "hamurisi-tarifleri/corek-tarifleri-hamurisi-tarifleri",
        "hamurisi-tarifleri/ekmek-tarifleri-hamurisi-tarifleri",
        "hamurisi-tarifleri/kis-tarifleri",
        "hamurisi-tarifleri/krep-tarifleri-hamurisi-tarifleri",
        "hamurisi-tarifleri/manti-tarifleri",
        "hamurisi-tarifleri/pide-tarifleri",
        "hamurisi-tarifleri/pizza-tarifleri",
        "hamurisi-tarifleri/pogaca-tarifleri",
        "hizli-yemekler/durum-tarifleri",
        "hizli-yemekler/hamburger-tarifleri",
        "hizli-yemekler/tost-tarifleri",
        "icecek-tarifleri/hosaf-tarifleri",
        "icecek-tarifleri/sicak-icecekler",
        "icecek-tarifleri/soguk-icecekler",
        "kahvaltilik-tarifleri",
        "kurabiye-tarifleri/tatli-kurabiyeler",
        "kurabiye-tarifleri/tuzlu-kurabiyeler",
        "makarna-tarifleri",
        "pilav-tarifleri",
        "salata-meze-kanepe/kanepe-tarifleri",
        "salata-meze-kanepe/meze-tarifleri",
        "salata-meze-kanepe/salata-tarifleri",
        "sandvic-tarifleri-tarifler",
        "sebze-yemekleri/dolma-tarifleri"
        "sebze-yemekleri/ev-yemekleri",
        "sebze-yemekleri/kizartma-tarifleri",
        "sebze-yemekleri/sarma-tarifleri",
        "sebze-yemekleri/sulu-yemek-tarifleri",
        "sebze-yemekleri/zeytinyagli-tarifler",
        "tatli-tarifleri/cikolatali-tarifler",
        "tatli-tarifleri/dondurma-tarifleri",
        "tatli-tarifleri/dondurmali-tarifler",
        "tatli-tarifleri/donut-tatli-tarifleri",
        "tatli-tarifleri/geleneksel-tatlilar",
        "tatli-tarifleri/helva-tarifleri-tatli-tarifleri",
        "tatli-tarifleri/kek-tarifleri",
        "tatli-tarifleri/komposto-tarifleri",
        "tatli-tarifleri/lokum-tarifleri",
        "tatli-tarifleri/meyveli-tatlilar",
        "tatli-tarifleri/pasta-tarifleri",
        "tatli-tarifleri/serbetli-tatlilar",
        "tatli-tarifleri/sutlu-tatlilar",
        "tatli-tarifleri/tart-tarifleri",
        "yumurta-yemekleri"
    ]

    custom_settings = {
        "CONCURRENT_REQUESTS": 16
    }

    def start_requests(self):
        for u in self.start_urls:
            for page in range(1, MAX_PAGE + 1):
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
        name = str(response.selector.xpath(
            '//h1[@itemprop="name"]/text()').get()).split("(")[0].strip()
        name = removeSpaces(checkName(removeParanthesis(name)))
        if name in foodNames:
            return
        foodNames.append(name)
        selectorIngredients = response.selector.xpath(
            '//div[@class="entry_content tagoninread"]/ul/li[@itemprop="ingredients"]/text()').getall()
        selectorRecipe = response.selector.xpath(
            '//div[@class="entry_content tagoninread"]/ol/li[@itemprop="ingredients"]/text()').getall()
        selectorRecipe = clearRecipe(selectorRecipe)
        portion = response.selector.xpath(
            '//span[@itemprop="recipeYield"]/strong/text()').get()
        times = response.selector.xpath(
            '//div[@class="tarif_meta_box"]/span/strong/text()').getall()
        foodType = response.selector.xpath(
            '//a[@class="taxonomy category"]/text()').getall()
        recipesOld.append({
            "isim": name,
            "malzemeler": selectorIngredients,
            "malzemeler_db": checkIngredientsForDb(selectorIngredients),
            "adimlar": selectorRecipe,
            "kisilik": portion,
            "hazirlama": 0 if len(times) == 0 else times[0],
            "pisirme": times[1] if len(times) > 1 else 0,
            "tur": foodType[1]
        })

        recipesNew["yemekler"][name] = {
            "malzemeler": selectorIngredients,
            "adimlar": selectorRecipe,
            "kisilik": portion,
            "hazirlama": 0 if len(times) == 0 else times[0],
            "pisirme": times[1] if len(times) > 1 else 0,
            "tur": foodType[1]
        }

        if foodType[1] not in recipesExtra["yemekler"].keys():
            recipesExtra["yemekler"][foodType[1]] = {}
            recipesExtra["yemekler"][foodType[1]][name] = {
                "malzemeler": selectorIngredients,
                "malzemeler_db": checkIngredientsForDb(selectorIngredients),
                "adimlar": selectorRecipe,
                "kisilik": portion,
                "hazirlama": 0 if len(times) == 0 else times[0],
                "pisirme": times[1] if len(times) > 1 else 0,
            }
        else:
            recipesExtra["yemekler"][foodType[1]][name] = {
                "malzemeler": selectorIngredients,
                "malzemeler_db": checkIngredientsForDb(selectorIngredients),
                "adimlar": selectorRecipe,
                "kisilik": portion,
                "hazirlama": 0 if len(times) == 0 else times[0],
                "pisirme": times[1] if len(times) > 1 else 0,
            }
            if foodType[1] not in foodTypes:
                foodTypes.append(foodType[1])

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
