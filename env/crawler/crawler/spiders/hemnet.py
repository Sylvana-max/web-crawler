import scrapy
import time
import json
# from .decoder import Decoder
from scrapy import signals
from pydispatch import dispatcher

class QuotesSpider(scrapy.Spider):
    name = "hemnet"
    # *** Change this url for your prefered search from hemnet.se ***
    start_urls = ['https://www.hemnet.se/bostader?location_ids%5B%5D=17908&expand_locations=10000&item_types%5B%5D=bostadsratt']
    globalIndex = 0
    results = {}


    def __init__(self):
        dispatcher.connect(self.spider_closed, signals.spider_closed)


    # Getting individual item from the ad list with a 3 secs pause
    def parse(self, response):
        for ad in response.css("ul.normal-results > li.normal-results__hit > a::attr('href')"):
            adUrl = ad.get()
            time.sleep(3)
            yield scrapy.Request(url=adUrl, callback=self.parseAd)

    # Next page navigation method with a 2 secs pause
        nextPage = response.css("a.next_page::attr('href')").get()
        if nextPage is not None:
            time.sleep(2)
            yield response.follow(nextPage, callback=self.parse)


    # Getting the details of the individual link (ad)
    def parseAd(self, response):
        hemnetUrl = response.request.url
        address = response.css("div.property-info__primary-container > div.property-info__address-container > div.property-address > h1.qa-property-heading::text").get()
        area = response.css("div.property-info__primary-container > div.property-info__address-container > div.property-address > div.property-address__area-container > span.property-address__area::text").get()

        price = response.css("div.property-info__primary-container > div.property-info__price-container > p.property-info__price::text").get()
        if price != None:
            price = price.replace('kr', '')
            price = price.replace(u'\xa0', '')
        
        attrData = {}
        for attr in response.css("div.property-info__attributes-and-description > div.property-attributes > div.property-attributes-table > dl.property-attributes-table__area > div.property-attributes-table__row"):
            attrLabel = attr.css("dt.property-attributes-table__label::text").get()
            attrValue = attr.css("dd.property-attributes-table__value::text").get()
            if attrLabel != None:
                if attrLabel == "Förening":
                    attrValue = attr.css("dd.property-attributes-table__value > div.property-attributes-table__housing-cooperative-name > span.property-attributes-table__value::text").get()
                
                attrValue = attrValue.replace(u'\xa0', '')
                attrValue = attrValue.replace(u'\n', '')
                attrValue = attrValue.replace(u'\t', '')
                attrValue = attrValue.replace('kr/mån', '')
                attrValue = attrValue.replace('kr/år', '')
                attrValue = attrValue.replace('kr/m²', '')
                attrValue = attrValue.replace('m²', '')
                attrValue = attrValue.strip()

                attrData[attrLabel] = attrValue

        # Gets the description of the ad
        description = response.css("div.property-description > p::text").get()
        # for descr in :
        #     if descr != None and descr != "":
        #         description = description + "\n" + descr

        # The broker email is sometimes None, check the reason later
        # for brokerEmail in response.css("div.broker-card > div.broker-card__contact-container > div.qa-broker-email > button.gtm-tracking-broker-email").get():
        #     if brokerEmail != None:
        #         brokerEmail = Decoder.decodeEmail(brokerEmail)
        #         brokerEmail = brokerEmail.replace(u'\xa0', '')
        #         brokerEmail = brokerEmail.replace(u'\n', '')
        #         brokerEmail = brokerEmail.replace(u'\t', '')
        #         brokerEmail = brokerEmail.strip()

        self.results[self.globalIndex] = {
            "hemnetUrl": hemnetUrl,
            "address": address,
            "area": area,
            "price": price,
            "description": description,
            "attr": attrData,
            # "brokerEmail": brokerEmail
        }
        self.globalIndex = self.globalIndex + 1

    def spider_closed(self, spider):
        with open('hemnet.json', 'w') as fp:
            json.dump(self.results, fp)
