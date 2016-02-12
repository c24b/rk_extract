#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup as bs
from requests_futures.sessions import FuturesSession
import re
import pymongo
import sys

RE_INT = re.compile('([0-9+])', re.UNICODE)
def get_nb(results):
    m = [n.group() for n in re.finditer(RE_INT, results)]
    return int("".join(m))

class MongoDB(object):
    def __init__(self, host, port, database_name):
        self.HOST = host
        self.PORT = port
        self.client = ""
        self.DB = ""
        uri = self.HOST+":"+str(self.PORT)
        
        try:
        
            self.client = pymongo.MongoClient(uri)
        
        except pymongo.errors.ConnectionFailure:
            logging.warning("Unable to connect using uri %s" %uri)
            sys.exit("InvalidUri : Unable to connect to MongoDB with url %s:%s" %(addr,port))
        
        self.version = self.client.server_info()['version']
        self.t_version = tuple(self.version.split("."))
        self.db_name = database_name
        self.db = getattr(self.client,database_name)
        
    
    def insert_items(self, data):
        return self.db.items.insert_many(data)
    def insert_search_result(self, data):
        return self.db.search.insert(data)
    def insert_brands(self, data):
        return self.brands.insert(data)
    def insert_categories(self, data):
        return self.categories.insert(data)
        
class RakutenSearch(object):
    
class RakutenExtractor(object):
    ''' An extractor for Rakuten Website'''
    def __init__(self, **args):
        #define entry point for extracting data
        #could be a brand, a category, a subcategory or a keyword
        self.query = args
        
        #define Backend
        self.db = MongoDB("localhost", 27017, "rakuten")
        #by brands defined by rakuten
        self.brand_url = "http://event.rakuten.co.jp/brand/"
        self.brands = self.get_brands()
        
        #by main 'category' of product defined by rakuten
        #self.type_url = "http://directory.rakuten.co.jp"
        #every main categories urls
        #self.category_urls = self.get_categories()
        #by slug category composed by url
        #cat_url = self.select_category("fashiongoods")
        #by subcategory
        #self.sub_cats = self.select_subcats(cat_url)
        self.collect_luxury()
        #by qualified query
        #self.query = {"brand":None, "category":None, "genre": None, "keyword":None}
    def filter(self):
        print self.query.keys()
    
    def get_url(self, url):
        '''simple download and parser'''
        r = requests.get(url)
        if r.status_code == 200:
            soup = bs(r.text, "lxml").encode("utf-8")
            return soup
        else:
            return None
            
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
                brands[name_en.lower()]= {"en": name_en, "jp": name_jp, "url":brand_url}
        return brands

    def get_categories(self):
        ''' collect type references url that correspond to top category url
        from the general directory of the website
        
        '''
        soup = self.get_url(self.type_url)
        main_type = soup.find_all("h2",{"class":"genreTtl"})
        return [n.a.get("href") for n in main_type]
    
    def get_subcategory(self, cat):
        '''collect every subcategory of a given category'''
        soup = self.get_url(self.type_url)
        cats = [n.a.get("href") for n in soup.find_all("h2",{"class":"genreTtl"})]
        subsection = soup.find_all("ul",{"class":"genreList"})
        for cat, section in zip(cats, subsection):
            if cat == category:
                sections = section.find_all('a')
                return [n.a.get("href") for n in sections]
    def collect_luxury(self):
        ''' a shortcut for the exercise'''
        soup = self.get_url('http://www.rakuten.co.jp/category/fashiongoods/')
        luxe_section = soup.find("div", {"class":"riClfx rigSetHeightWrap riMaB20"})
        luxe_pages = [n.get("href") for n in luxe_section.find_all("a")]
        it_bag_list = []
        for url in luxe_pages:
            #print(url)
            soup = self.get_url(url)
            for n in soup.find_all("a"):
                if n is not None and n.get("href") is not None:
                    if "search/mall" in n.get("href"):
                        it_bag_list.append(n.get("href"))
        self.async(it_bag_list)
        return "Ok"
    
    def select_category(self, cat):
        '''
        select the main page of a given category
        '''
        for cat_url in self.categories:
            tag = cat_url.split("/")[-2]
            if tag == cat:
                soup = self.get_url(link_dir)
                cat = soup.find("h1",{"class":"categoryTtl"})
                return cat.a.get("href")
    
    def select_subcategory(self, cat):
        ''' given a main category collect every subcategory'''
        
        subsection = soup.find_all("ul",{"class":"genreList"})
        for cat_url, section in zip(cats, self.categories):
            tag = cat_url.split("/")[-2]
            if tag == cat:
                sections = section.find_all('a')
                return [n.a.get("href") for n in sections]
                
    def collect_main_mall(self, category):
        ''' given a category url retrieve the top mall'''
        soup = self.get_url(category)
        main_mall = soup.find_all("h2",{"class":"genreTtl"})
        return [n.a.get("href") for n in main_mall]
    
    def collect_submall(self, category):
        ''' given a main category collect every subcategory '''
        soup = self.get_url(self.type_url)
        cats = [n.a.get("href") for n in soup.find_all("h2",{"class":"genreTtl"})]
        subsection = soup.find_all("ul",{"class":"genreList"})
        for cat, section in zip(cats, subsection):
            if cat == category:
                sections = section.find_all('a')
                return [n.a.get("href") for n in sections]
    
    def async(self,list_url):
        session = FuturesSession(max_workers=3)
        for url in list_url:
            future = session.get(url)
            future.add_done_callback(self.extract_results)
    
    def async_next(self, list_url):
        session = FuturesSession(max_workers=5)
        for url in list_url:
            future = session.get(url)
            future.add_done_callback(self.extract_next)
            
    def extract_nexts(self, future):
        response = future.result()
        
        if response.status_code == 200:
            soup = bs(response.text, "lxml")
            self.db.insert_items(self.extract_page(soup))
            
    def extract_results(self, future):
        results = []
        response = future.result()
        if response.status_code == 200:
            soup = bs(response.text, "lxml")
            search_res = self.get_results(soup, response.url)
            first_page = self.extract_page(soup)
            results.append(first_page)
            
            self.db.insert_items(results)
            self.async_next(search_res["next_urls"])
            del search_res["next_urls"]
            self.db.insert_info(search_res)
            print("Ok")
            return
            
            
            #self.async_download(res["next_urls"])
    def extract_page(self, page):
        '''extract the 45 results in the page'''
        return [self.extract_item(n) for n in page.find_all("div",{"class":"rsrSResultSect"})]
    
    def extract_item(self, page):
        item = {"photo_src":None,
                "price":None,
                "page_url":None,
                "price": None,
                "review_nb":None,
                "review_page":None,
                "shop_name":None,
                "shop_url": None,
                "insurance":False,
                "paiement_mode": None,
                "product_info": None,
                "url": None,
                "id": None,
                }
        try:
            item_text = page.find("span", {"class":"rsrSResultItemTxt"})
            item["url"]  = page.find("h2").find("a").get("href")
            item["title"] = page.h2.text
            item["description"] = page.find("p", {"class": "copyTxt"}).text
            item["id"] = item["url"].split("/")[-2]
        except AttributeError:
            return item
        try:
            item_photo = page.find("div", {"class":"rsrSResultPhoto"})
            item["photo_src"] = item_photo.find("img").get("src")
            item["page_url"] = item_photo.find("a").get("href")
        except AttributeError:
            pass
        try:
            item_info = page.find("span", {"class":"rsrSResultItemInfo"})
            item["price"] = get_nb(item_info.find("p", {"class":"price"}).text)
            item["insurance"] = bool(item_info.find("p", {"class":"iconAsuraku"}) is not None)
            item["rewiew_nb"] = get_nb(page.find("p", {"class":"txtIconReviewNum"}).text)
        except AttributeError:
            pass
        try:
            shop_block = page.find("span", {"class":"txtIconShopName"})
            item["shop_name"] = shop_block.text
            item["shop_url"] = shop_block.a.get("href")
        except AttributeError:
            pass
        rank = page.find("div", {"class":"searchAccuracyMeasurement"})
        item_pos = int(rank.get("itemposition"))
        page_nb = int(rank.get("pagenumber"))
        item["position"] = str(item_pos)+"/"+str(page_nb)
        item["rank"] = item_pos+((page_nb-1)*45)
        return item
        
    def get_typology(self, page):
        '''
        given a first page 
        enhance categories information by
        retrieving the nb of results for each category concerned by this search
        '''
        product_type = page.find("ul",{"class":"rsrAsideArrowLi rsrGenreNavigation"})
        typology = {}
        for n in product_type.find_all('a'):
            if n.find("span") is not None:
                try:
                    res = get_nb(n.find("span", {"class": "rsrRegNum"}).text)
                except(ValueError,AttributeError):
                    res = 0
                typology[n.get("href")] = {"id":n.get("data-genreid"), "results_nb": res}
        return typology
        
    def get_results(self, page, url):
        '''
        given a first page
        retrive:
        - the total results_nb of item found, 
        - the pages_nb,
        - the next_urls list
        - the results_nb  of items for other categories
        '''
        res = page.find("div",{"class":"rsrDispTxtBoxRight"}).b.next.next
        if res is not None:
            self.results_nb = get_nb(res)
        else:
            self.results_nb = 0 
        self.page_nb = int(self.results_nb/45)
        rest = self.results_nb%45
        if rest > 0:
            self.page_nb =  self.page_nb+1
        self.next_urls = [url+"?p="+str(x) for x in range(2, self.page_nb+1)]
        self.typology = self.get_typology(page)
        search_results = {"results_nb": self.results_nb,
                            "page_nb": self.page_nb,
                            "next_urls": self.next_urls,
                            "typology": self.get_typology(page)
                            }
        return search_results

if __name__== "__main__":
    rk = RakutenExtractor()
