#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as bs
from requests_futures.sessions import FuturesSession
import re
import pymongo
import sys
from database import MongoDB

RE_INT = re.compile('([0-9+])', re.UNICODE)

def get_nb(results):
    m = [n.group() for n in re.finditer(RE_INT, results)]
    return int("".join(m))


class RakutenExtractor(object):
    def __init__(self, scope, filters):
        #activate the extraction filters
        self.filters(args)
        self.site_map_url = "http://directory.rakuten.co.jp/"
        self.brands_url = "http://event.rakuten.co.jp/brand/"
        self.DB = MongoDB("rakuten")
        self.get_scope(scope)
        
    def get_url(self, url):
        '''simple download and parser'''
        r = requests.get(url)
        if r.status_code == 200:
            soup = bs(r.text, "lxml").encode("utf-8")
            return soup
        else:
            return None
            
    def get_scope(self, scope):
        '''
        collecting references using site architecture:
        - categories
        - genres
        - brands
        * scope from rk site map structure:
            - category
            listed in site map:
            'http://directory.rakuten.co.jp/'
            e.g: 
            category_url: http://directory.rakuten.co.jp/category/media/
            category_id: media
            category_page: http://www.rakuten.co.jp/category/media/
            - genre called 'genre' in rk:
            inside category a list of generic mall
            e.g:
                genre_name: "CD・DVD・楽器"
                genre_url : "http://search.rakuten.co.jp/search/mall/-/100554/"
                genre_id : 100554
            - mall a list of specific malls in rk:
                mall_name = "DVD"
                mall_url = "http://search.rakuten.co.jp/search/mall/-/101354/"
                mall_id = 100554
        * scope from rk brands listings:
        - brand:
            - jap_name
            - en_name
            - brand_url
        '''
        if args["brands"]:
            self.get_brands()
        elif args["categories"]:
            self.get_categories()
        elif args["genre"]:
            self.get_genres()
        elif args["malls"]:
            self.get_subtype()
        else:
            pass
            
    def filters(self, **args):
        '''extraction filters based on qualified user query
        3 type of filters are available:
        - brand
        - category
        - keyword
        '''
        print set(set(args) & set(["query", "brand", "keyword"]))
    
    def get_brands(self):
        '''
        collect and store a dict of normalized brands:
        brands = { "louis vuitton":
                    {
                        "en":"louis vuitton",
                        "jp":"",
                        url:""
                    },
                ...
                }
        '''
        brands = {}
        soup = self.get_url(self.brand_url)
        #here initially a list comprehension
        # but decomposed for clarety
        for b in soup.find_all("li"):
            #filtrer empty items
            # and items that are not brands
            if b.find("a") is not None and b.find("span", {"class":"brandNm"}) is not None:
                brand_url = b.find("a").get("href")
                name_en, name_jp = (b.find("span", {"class":"brandNm"}).text).split(u"（")
                name_jp = name_jp.split(u"）")[0]
                brands[name_en.lower()]= {"en_name": name_en, "jp_name": name_jp, "url":brand_url}
        self.db["brands"].insert_many(brands)
        self.brands = self.db["brands"].find({},{"_id":0})
        return self.brands
        
    def get_categories(self):
        ''' collect type references url that correspond to top category url
        from the general directory of the website
        '''
        soup = self.get_url(self.site_map_url)
        main_type = soup.find_all("h2",{"class":"genreTtl"})
        cat_urls = [n.a.get("href") for n in main_type]
        cat_ids = [n.a.get("href") for n in main_type]
        return [
        
                ]
