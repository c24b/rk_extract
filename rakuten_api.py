#!/usr/bin/env python3
#coding: utf-8
import requests
from bs4 import BeautifulSoup as bs
import re
from urllib.parse import urlparse,urljoin, quote, quote_plus
# Asynchronous HTTP Requests in Python 3.2
#quite usefull when tons of urls have to be downloaded
#from requests_futures.sessions import FuturesSession
import json, csv
from langdetect import detect
import pymongo
RE_INT = re.compile('([0-9+])', re.UNICODE)

def get_nb(results):
    '''mini method to catch number'''
    try:
        m = [n.group() for n in re.finditer(RE_INT, results)]
        return int("".join(m))
    except ValueError:
        return None

def check_lang(value):
    ''' if japanese True'''
    return bool(detect(value) == "ja")
    
def check_brand(self, target=""):
    '''
    simple check let's forget fron now about fuzzy search and ngrams
    here check if the brand is ok but shoult simply return or the correct_id
    or the url has unique key for database
    '''
    tag_brand = re.split("・|ー| |&|\(|\)|=|>", target.lower())
    tag_brand = [n for n in tag_brand if n !=""]
    if check_lang(target):
        lang = "jap"
    else:
        lang = "en"
    if bool(target in [n["name_"+lang] for n in self.brands]):
        return True
    elif len(tag_brand) > 1:
        for item in self.brands:
            if len(list(set(item["tags_"+lang] - set(tag_brand)))) < len(tag_brand):
                return True
    else:
        #TO DO: check similarity ratio for fuzzy search and a ratio of interverting 2 char
        return False
            
        
class Database(object):
    def __init__(self, host="localhost", port=27017, name="rakuten"):
        try:
            self.client = pymongo.MongoClient(host, port)
        except:
            self.client = pymongo.MongoClient()
        self.version = self.client.server_info()['version']
        self.t_version = tuple(self.version.split("."))
        self.db_name = name
        self.db = getattr(self.client,name)
        for n in ["products","brands", "categories", "malls", "stores"]:
            self.db[n].create_index([('id', pymongo.ASCENDING)],unique=True)
            setattr(self, n, self.db[n])
        
    def get_stats(self, filter="products"):
        items_nb = self.db[filter].count()
        pass
        
class RakutenAPI(object):
    def __init__(self):
        self.lang = None
        self.load_refs()
    def collect_refs(self, refs=["brands", "stores"]):
        e = RakutenExtractor()
        #by default stores is the maximum level of details
        for ref in refs:
            func = getattr(e, ref)
            func()
        return self.load_refs(refs)
    
    def load_refs(self, refs=["brands", "stores", "malls", "categories"]):
        DB = Database(name="rakuten_refs")
        self.db = DB.db
        #by default stores has the maximum level of details
        for ref in refs:
            try:
                setattr(self, ref, self.db[ref])
            except KeyError:
                print("Unknown parameter %s" %ref)
                pass
    
    def get_ids(self, query):
        '''get the corresponding id of a given tag or name
        TO DO forget fuzzy search with ngrams'''
        tag = [ v for k,v in list(query.items()) if k != "brand"][0]
        if tag =="その他":
            return []
        key = list(query.keys())[0]+"s"
        if self.lang is None:
            if detect(tag) == "ja":
                self.lang = "jap"
            else:
                self.lang = "en"
        
        if getattr(self, key) is None:
            self.collect_refs([key+"s"])
        if tag.isdigit():
            return self.db[key].find_one({"id": tag})
        
        for n in self.db[key].find():
            try:
                if tag  == n["name"]:
                    return [n["id"]]
            except KeyError:
                if tag  == n["id"]:
                    return [n["id"]]
            if tag in n["tags"]:
                return [n["id"]]
        return []
    
    def verify_brand(self, brand):
        brands = []
        if self.lang is None:
            if detect(brand) == "ja":
                self.lang = "jap"
            else:
                self.lang = "en"
        tag_brand = re.split("・|ー| |&", brand)
        for b in self.brands.find():
            if b["name_"+self.lang] == brand:
                return [brand]
            else:
                if brand in b["tags_"+self.lang]:
                    return True
                elif len(set(tag_brand) & set(b["tags_"+self.lang])) > 0:
                    return True
                else:
                    pass
        if len(brands) == 0:
            return False
        return True
            
    def parse_query(self, query):
        params_nb = len(query.keys())
        if  1 < params_nb > 2 :
            sys.exit("Rakuten API accepts 1 or 2 parameters only. Exit")
            return
        else:
            try:
                brand = query["brand"]
            except KeyError:
                brand = None
            if len([n for n in query.keys() if n in ["category","mall","store"]]) != 1:
                sys.exit("Invalid name of parameters")
            else:
                return(query, brand)
                 
    def search(self, **query):        
        '''ENTRY POINT'''
        self.query, self.brand = self.parse_query(query)
        print("Search", self.query)
        self.brand_ids = []
        self.tags_ids = []
        
        if self.brand is not None:
            if self.verify_brand(self.brand):
                self.brand_ids.append(self.brand)
        else:
            self.brands_ids = self.brands.distinct("id")
            
        if self.query is not None:
            self.tag_ids = self.get_ids(self.query)
        
        for brand in self.brand_ids:
            for tag in self.tag_ids:
                print(tag, brand)
                self.search_products(brand,tag, query)
    def geet_recommanded_cat(self, coup):
        pass
    def get_product_type(self, soup):
        '''
        get repartition in categories and genre of a search results
        '''
        stats = {}
        try:
            product_type = soup.find("ul",{"class":"rsrGenreNavigation"})
            for n in product_type.find_all("a"):
                cat_id = n.get("data-genreid")
                results_nb = re.sub("（⇒）", "more", n.span.span.text)
                tag =  re.sub("（⇒）", "", n.text)
                try:
                    results_nb = get_nb(results_nb)
                except:
                    pass
                print(results_nb, text)
                    #~ tag = n.text.split("\n")[0]
                    #~ if tag == "その他":
                        #~ pass
                    #~ else:
                        #~ nb = get_nb(n.find("span", {"class": "rsrRegNum"}).text)
                        #~ cat = self.db.stores.find_one({"name": tag})
                        #~ if cat is None:
                            #~ cat = self.db.malls.find_one({"name": tag})
                            #~ 
                        #~ 
                        #~ stats = {"nb_results": nb, "cat":cat, "tag":tag}
        except AttributeError:
            pass
        #~ 
        return stats 
    
    def search_products(self, brand_id, tag_id, query):
        def get_results_nb(page):
            '''scrap the nb of search result'''
            try:
                res = page.find("div",{"class":"rsrDispTxtBoxRight"}).b.next.next
                if res is not None:
                    results_nb = get_nb(res)
                else:
                    results_nb = 0 
            except AttributeError:
                results_nb = 0
            return results_nb
        
        def get_pagination(nb, offset=45):
            '''calculate page nb offset +1'''
            page_nb = int(nb/offset)
            if nb%offset > 0:
                page_nb =  page_nb+1
            return page_nb
        
       
            
        if brand_id is None and tag_id is not None:
            url = "http://search.rakuten.co.jp/search/mall/-/%s/" %(tag_id)
            
            
        elif brand_id is not None and tag_id is not None:
            url = "http://search.rakuten.co.jp/search/mall/%s/%s/" %(brand_id,tag_id)
            
            
        else:
            url = "http://search.rakuten.co.jp/search/mall/%s/" %(brand_id)
            
            
        soup = self.parse(url, "utf-8")
        results_nb =  get_results_nb(soup)
        stats = self.get_product_type(soup)
        if results_nb == 0:
            return
        else:
            print("Search with parameters %s gave %i results " %(query, results_nb))
            page_nb = get_pagination(results_nb)
            print(page_nb)
            products = self.extract_page(soup, tag_id, brand_id)
            for p in products:
                try:
                    self.db.products.insert(p)
                except pymongo.errors.DuplicateKeyError:
                    pass
            
            #insert products into product list
            for page in [url+"?p="+str(x) for x in range(2, page_nb+1)]:
                page = self.parse(url,"utf-8")
                products = self.extract_page(page, tag_id, brand_id)
                
                for p in products:
                    try:
                        self.db.products.insert(p)
                    except pymongo.errors.DuplicateKeyError:
                        pass
        return
            
    def parse(self, url, encoding=None):
        '''get the parsed html soup using BeautifulSoup
        with the correct encoding for japanese of some page of
        this peculiar website'''        
        r = requests.get(url)
        if encoding is None:
            r.encoding = 'euc_jisx0213'
        else:
            r.encoding = "utf-8"
        if r.status_code == 200:
            soup = bs(r.text, "lxml")
            soup.prettify('utf-8')
            return soup
        else:
            return sys.exit("Url %s is unreachable" %url)
                
    def extract_page(self, page, brand, tag):
        '''extract the 45 items from results in the page'''
        return [self.get_product(n, tag,brand) for n in page.find_all("div",{"class":"rsrSResultSect"})]
    
    def get_product(self,page,mall_id, brand):
        
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
                "url": page.a.get("href"),
                "id": None,
                "brand": str(brand).lower(),
                "tag_id": mall_id
                }
        try:
            item_text = page.find("span", {"class":"rsrSResultItemTxt"})
            item["url"]  = page.h2.find("a").get("href")
            item["title"] = page.h2.text
            item["description"] = page.find("p", {"class": "copyTxt"}).text
            item["id"] = item["url"].split("/")[-2]
        except AttributeError:
            pass
        try:
            item_photo = page.find("div", {"class":"rsrSResultPhoto"})
            item["photo_src"] = item_photo.find("img").get("src")
            item["page_url"] = item_photo.find("a").get("href")
        except AttributeError:
            pass
        try:
            #TO check
            item["price"] = get_nb(page.find("p", {"class":"price"}).a.text)
            item["currency"] = page.find("p", {"class":"price"}).span.text
            item["insurance"] = bool(page.find("p", {"class":"iconAsuraku"}) is not None)
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

class RakutenExtractor(object):
    '''Generic Extractor for building the db references'''
    def __init__(self):
        #define entry point for scrapping data
        #category entry
        self.genre_url = "http://directory.rakuten.co.jp/"
        #mall entry
        self.cat_url = "http://directory.rakuten.co.jp/category/"
        #brand entry
        self.brand_url = "http://event.rakuten.co.jp/brand/"
        #self.collect()
        DB = Database(name="rakuten_refs")
        self.DB = DB.db
        
    def parse(self, url, encoding=None):
        '''get the parsed html soup using BeautifulSoup
        with the correct encoding for japanese of this peculiar website'''
        r = requests.get(url)
        if encoding is None:
            r.encoding = 'euc_jisx0213'
        else:
            r.encoding = "utf-8"
        if r.status_code == 200:
            soup = bs(r.text, "lxml")
            soup.prettify('utf-8')
            return soup
        else:
            return sys.exit("Url %s is unreachable" %url)
    
    def build(self):
        '''rebuild the entire dataset references'''
        self.collect_brands()        
        self.collect_categories()
        self.collect_malls()
        self.collect_stores()
        
    def collect_brands(self):
        '''brands are defined by editorialisation work inside event on a specific topic
        brands are listed in a dict (json format compatible) key is the english name
        '''
        self.brands = []
        soup = self.parse(self.brand_url)
        #here initially a list comprehension
        # but decomposed for clarety
        for b in soup.find_all("li"):
            #filtrer empty items
            # and items that are not brands
            if b.find("a") is not None and b.find("span", {"class":"brandNm"}) is not None:
                brand_url = b.find("a").get("href")
                brand_url = "/".join(brand_url.split("/")[:-2])
                name_en, name_jp = (b.find("span", {"class":"brandNm"}).text).split(u"（")
                name_jp = name_jp.split(u"）")[0]
                tags_jp = [n for n in re.split("・|ー| ", name_jp) if n!= ""]
                tags_en = [n for n in re.split(" |&|・", name_en.lower())  if n!= ""]
                brand = {   "id":name_en, 
                            "url": brand_url,
                            "name_en":name_en, 
                            "name_jap": name_jp, 
                            "tags_jap": tags_jp, 
                            "tags_en": tags_en}
                self.brands.append(brand)
                try:
                    self.DB["brands"].insert(brand)
                except pymongo.errors.DuplicateKeyError:
                    pass
        return self.brands
            
        
    def collect_categories(self):
        '''collect every categories such as fashion good'''
        self.cats = []
        soup = self.parse(self.genre_url)
        for g in soup.find_all("h2", {"class":"genreTtl"}):
            slug, catname = g.find("a").get("href").split("/")[-2], g.text
            tags = [n for n in re.split("・|ー| |&", catname) if n!=""]
            #self.cats.append({"id":slug, "name":catname, "tags":tags})
            cat = {"id":slug, "name":catname, "tags":tags}
            try:
                self.DB["categories"].insert(cat)
            except pymongo.errors.DuplicateKeyError:
                pass
            self.cats.append(cat)
        return self.cats
        
    def collect_malls(self):
        '''collect every malls'''
        self.malls = []
        
        soup = self.parse(self.genre_url)
        for cat,mall in zip(self.cats, soup.find_all("ul", {"class":"genreList"})):
            for c in mall.find_all("li"):
                m ={}
                m["id"] = get_nb(c.find("a").get("href"))
                m["name"] = c.find("a").text.replace("(=>)", "")
                m["tags"] = [n for n in re.split("・|ー| |&", m["name"]) if n !=""]
                m["cat_id"] = cat["id"]
                m["cat"] = cat
                #self.malls.append(m)
                try:
                    self.DB["malls"].insert(m)
                except pymongo.errors.DuplicateKeyError:
                    pass
        #~ with open('malls.json', 'w') as f:
            #~ json.dump(self.malls, f, ensure_ascii=False, indent=4, sort_keys = True)
        #~ return self.malls
    
    def collect_stores(self):
        print(''' collect every stores''')
        self.stores = []
        
        for mall in self.DB.malls.find():
            url = self.cat_url+mall["cat_id"]
            soup = self.parse(url)
            #tags of cat
            for mall2 in soup.find_all("ul", {"class":"genreList"}):
                for c in mall2.find_all("li"):
                    s = {}
                    s["id"] = get_nb(c.find("a").get("href"))
                    s["name"] = c.find("a").text.replace("(=>)", "")
                    s["tags"] = [n for n in re.split("・|ー| |&", s["name"]) if n !=""]
                    s["cat"] = self.DB.categories.find_one({"id":mall["cat_id"]})
                    s["mall"] = mall
                    try:
                        self.DB["stores"].insert(s)
                    except pymongo.errors.DuplicateKeyError:
                        pass
        return self.stores
                
        
if __name__== "__main__":
    #Create the reference database
    #refs = RakutenExtractor()
    #refs.build()
    r = RakutenAPI()
    #generic extraction of every brands for category fashion goods
    #r.search(category="fashiongoods")
    #extraction of fashion goods with louis vuitton's brands
    #r.search(brand="louis vuitton", category="fashiongoods")
    #extraction of luxury bags of rebecca taylor in japanese
    #r.search(brand="レベッカテイラ",  mall="ブランド雑貨")
    #extraction of every brand for women bag
    r.search(mall="レディースバッグ", brand="louis vuitton")
    #r.search(store="110933", brand="ルイ・ヴィトン")
    
