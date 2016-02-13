#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from beautifulsoup4 import BeautifulSoup as bs
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
        
    
class RakutenExtractor(object):
    ''' An extractor for Rakuten Website'''
    def __init__(self, **args):
        #TO DO: define entry point for extracting data
        #could be a brand, a category, a subcategory or a keyword
        # or a mix!
        self.query = args
        #define Backend
        self.db = MongoDB("localhost", 27017, "rakuten")
        #by brands defined by rakuten
        ### BRANDS ENTRY###
        self.brand_url = "http://event.rakuten.co.jp/brand/"
        ### CATEGORIES ENTRY ###
        self.sitemap_url = "http://directory.rakuten.co.jp"
        ### TAGS ENTRY ###
        #self.genre_url = "http://directory.rakuten.co.jp/category/%s"
    
    def get_url(self, url):
        '''simple download and basic parser'''
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
            #filter empty items
            # and items that are not brands
            if b.find("a") is not None and b.find("span", {"class":"brandNm"}) is not None:
                brand_url = b.find("a").get("href")
                name_en, name_jp = (b.find("span", {"class":"brandNm"}).text).split(u"（")
                name_jp = name_jp.split(u"）")[0]
                brands[name_en.lower()]= {"en": name_en, "jp": name_jp, "url":brand_url}
        return brands
    
    def get_brand(self, brand ="vuitton"):
        '''find the brand'''
        self.brands = self.get_brands()
        #TODO:
        #here we should initiate a first recollection
        # of brands stored in a ref db instead of collecting it each time
        # self.brands = self.db.brands.find()
        #
        #verify if brand exists
        if brand.lower() in self.brands.keys():
            return self.brand[brand.lower()]
        else:
            self.found = False
            ## TODO
            #here we match brand with uncomplete name
            ## it's a very lazy way of searching
            ## eg. vuitton ==> louis vuitton
            ## obviously with a DB system we could search in the jp version
            ## also making a match rule more wide with a ratio matching
            ## and more refined search operator such as in Whoosh
            for b, v in self.brands.items():
                for n in re.split(" |&|\.", b):
                    # n is at least a three letter words and not empty
                    if n != "" and len(n) > 2:
                        if brand == n:
                            print("brand %s matches with %s" %(b, brand))
                            self.brand = self.brands[b]
                            self.brand_search = "http://search.rakuten.co.jp/search/mall/%s/?grp=product&pc_search=Envoyer" %self.brand
                            return self
            print ("brand %s not found\n Launching dummy search" %brand)
            #if not launch a dummy search
            self.brand = quote(brand)
            self.brand_search = "http://search.rakuten.co.jp/search/mall/%s/?grp=product&pc_search=Envoyer" %self.brand
            return self.brand
            
    
    def get_cats(self):
        ''' collect every category references from the general directory of the website
        in a normalized dict and store main mall id
        {"fashiongoods":{"cat_url": ,"cat_name":,}}
        '''
        soup = self.get_url(self.sitemap_url)
        cats = {}
        for n in soup.find_all("h2",{"class":"genreTtl"}):
            cat_url = n.a.get("href")
            cat_id = cat_url.split("/")[-2]
            cat_name = n.text
            #TODO: here should create a keywords lists on subcats
            #to index and make search on tags available
            soup = self.get_url(cat_url)
            cat = soup.find("h1",{"class":"categoryTtl"})
            mall_url = cat.a.get("href")
            mall_id = mall_url.split("/")[-2]
            cats[cat_id] = {"cat_url": cat_url, "cat_name":cat_name, "mall_id":mall_id, "mall_url": mall_url}
        return cats
    
    def get_cat(self, cat):
        '''find specific cat and return the main mall url'''
        if cat in self.cats.keys():
            return self.cats[cat]
        else:
            return None     
    
    def get_malls(self, cat_id):
        '''collect every specialized mall for a given category
        eg: fashiongoods > women handbag
        '''
        soup = self.get_url(self.sitemap_url)
        cats = [n.a.get("href") for n in soup.find_all("h2",{"class":"genreTtl"})]
        subsection = soup.find_all("ul",{"class":"genreList"})
        for cat, section in zip(cats, subsection):
            if cat_id == category:
                #TODO: here should create a keywords lists on subcats
                #to index and make search on tags available
                for n in section.find_all('a'):
                    mall_url = n.a.get("href")
                    mall_id = mall_url.split("/")[-2]
                    mall_name = n.text
                    malls[mall_id] = {"mall_url":mall_url, "mall_name":mall_name, "cat_id":cat_id}
            return malls
        return None
   
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
                    # a shortcut search because DOM tree class 
                    #is different for each page
                    if "search/mall" in n.get("href"):
                        it_bag_list.append(n.get("href"))
        #TODO: asynchronous way of dowloading it
        #self.async(it_bag_list)
        if len(it_bag_list) > 0:
            for bag_url in it_bal_list:
                #download
                items = self.extract_products(bag_url) 
                #store
                print(items)
            return it_bag_list
        else:
            return False
    def search_brand(self, brand="gucci"):
        '''search for one brand in every category'''
        categories = self.get_cats()
        for cat in categories.keys():
            self.search(cat,brand)
        return 
        
        
    def search_cat(self, cat="fashiongoods"):
        ''' given a category slug search for every brand in this cat
        retrieve only stats for the moment
        TO DO: provide a method to collect products
        '''
        #TODO:
        #here we should initiate a first recollection
        # of cats stored in a ref db instead of collecting it each time
        # with get_cat or get_cats methods
        #
        self.brands = self.get_brands()
        if mall_url is not None:
            for brand in self.brands.keys():
                print(self.search(cat=cat, brand=brand))
                #store stats?
        else:
                
            #TODO: if not found should search into submalls using keywords
            # and matching with rate with a search_tag method
            return False
        
    def search(self, cat="fashiongoods", brand="gucci"):
        mall_url = self.get_cat(cat)
        mall_id = mall_url["mall_id"]
        #TO DO: here we could check that brand really exists
        #and match
        #but also work as it is
        cat_search = "http://search.rakuten.co.jp/search/mall/%s/%s/?grp=product" %(brand, mall_id)
        soup = self.get_url(cat_search)
        stats = self.search_stats(soup, cat_search)
        typology = self.get_typology(soup)
        del stats["next_urls"]
        print(stats, typology) 
        return stats["results_n"]
    
            
    def async_next(self, list_url):
        '''utility to dowload like async.io multiple url
        and send them to extract_nexts
        '''
        session = FuturesSession(max_workers=5)
        for url in list_url:
            future = session.get(url)
            future.add_done_callback(self.extract_nexts)
            
    def extract_nexts(self, future):
        response = future.result()
        if response.status_code == 200:
            soup = bs(response.text, "lxml")
            self.db.insert_items(self.extract_page(soup))
        else:
            pass
    
    def search_stats(self, soup, source_url):
        ''' retrieve the main results info of a given search
        html has already been dowloaded so we don't do it again
        we need source_url to build next pages
        search_results_nb
        pages_nb
        next_urls to download
        '''
        res = page.find("div",{"class":"rsrDispTxtBoxRight"}).b.next.next
        if res is not None:
            results_nb = get_nb(res)
        else:
            print("No results nb found")
            return False 
        page_nb = int(results_nb/45)
        rest = results_nb%45
        if rest > 0:
            page_nb =  page_nb+1
        next_urls = [source_url+"?p="+str(x) for x in range(2, page_nb+1)]
        return {"results_nb": results_nb, "pages_nb": page_nb, "next_urls": next_url}
        
    def extract_products(self, url):
        '''main function that download, extract and store results'''
        products = []
        soup = self.get_url(url)
        stats = self.search_stats(soup)
        first_products = self.extract_page(soup)
        self.async_next(stats["next_urls"])
        del stats["next_urls"]
        print(stats)
        return
        
    def extract_page(self, page):
        '''extract the 45 results in the page'''
        return [self.extract_item(n) for n in page.find_all("div",{"class":"rsrSResultSect"})]
    
    def extract_item(self, page):
        ''' an item correspond to a product description
        '''
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
        given a search results on a brand
        give a typology of product that the brand sells
        i.e in which category and subcategory the brand has most products
        represented gives a pretty good agnostic idea 
        '''
        product_type = page.find("ul",{"class":"rsrAsideArrowLi rsrGenreNavigation"})
        typology = {}
        for n in product_type.find_all('a'):
            if n.find("span") is not None:
                try:
                    res = get_nb(n.find("span", {"class": "rsrRegNum"}).text)
                except(ValueError,AttributeError):
                    res = 0
                typology[n.get("href")] = {"mall_id":n.get("data-genreid"), "results_nb": res}
        return typology
    def search_tag(self, tag=""):
        ''' facility to search within a genre or a tag prvided by rk 
        plateform and sitemap ''' 
        raise NotImplementedError
    
if __name__== "__main__":
    rk = RakutenExtractor()
    #for the exercice 
    rk.collect_luxury()
    # for the API implementation
    #search by brand every product
    
    #rk.search_brand("vuitton")
    #search by category every brand
    
    #rk.search_cat("fashiongoods")
    #search for a specific brand in a specific category
    #rk.search("fashiongoods", "vuitton")
    
    #Not implemented
    #rk.search_tag()
