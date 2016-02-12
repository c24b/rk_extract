#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup as bs
import re
from urllib.parse import urlparse,urljoin, quote, quote_plus
# Asynchronous HTTP Requests in Python 3.2
#quite usefull when tons of urls have to be downloaded
from requests_futures.sessions import FuturesSession
import sqlite3


 
RE_INT = re.compile('([0-9+])', re.UNICODE)
def get_nb(results):
    m = [n.group() for n in re.finditer(RE_INT, results)]
    return int("".join(m))
class Database(object):
    def __init__(self):
        pass
            
class RakutenExtractor(object):
    def __init__(self):
        #define entry point for scrapping data
        self.genre_url = "http://directory.rakuten.co.jp/"
        self.brand_url = "http://event.rakuten.co.jp/brand/"
        self.search_url = "http://search.rakuten.co.jp/"
        
    def get_html(self, url):
        r = requests.get(self.brand_url)
        if r.status_code == 200:
            soup = bs(r.text, "lxml")
    def collect_brands(self):
        '''brands are defined by editorialisation work inside event
        brands are listed in a json format
        key of a brand is the english name'''
        self.brands = {}
        self.brand_url = "http://event.rakuten.co.jp/brand/"
        r = requests.get(self.brand_url)
        
        if r.status_code == 200:
            soup = bs(r.text, "lxml")
            #ici initially a list comprehension
            # but decomposed for clarety
            for b in soup.find_all("li"):
                #filtrer empty items
                # and items that are not brands
                if b.find("a") is not None and b.find("span", {"class":"brandNm"}) is not None:
                    brand_url = b.find("a").get("href")
                    name_en, name_jp = (b.find("span", {"class":"brandNm"}).text).split(u"（")
                    name_jp = name_jp.split(u"）")[0]
                    self.brands[name_en.lower()]= {"en": name_en, "jp": name_jp, "url":brand_url}
            return self.brands
            
    def collect_categories(self):
        ''' products categories are listed with their 
        corresponding mall_id inside 'genre'
        '''
        
        self.genre_url = "http://directory.rakuten.co.jp/category/"
        
        
        r = requests.get(self.cat_url)
        
        if r.status_code == 200:
            soup = bs(r.text, "lxml")
            soup.prettify('utf-16')
            #ici je déplie la liste pour plus de lisibilité
            #initialement deux list compréhension zippée
            #construction de la liste de ref dans un base
            #ici stockées dans l'objet
            self.categories = []
            genres = [(g.find("a").get("href"), g.text)  for g in soup.find_all("h2", {"class":"genreTtl"})]
            cats = soup.find_all("ul", {"class":"genreList"})
            
            for g, cat in zip(genres, cats):
                genre_url = g[0]
                genre_id = genre_url.split("/")[-2]
                genre_name  = g[1]
                for n in cat.find_all("li"):
                    cat_url  = n.find("a").get("href")
                    cat_name = n.text
                    cat_id = cat_url.split("/")[-2]
                    cat_info = {   "genre_name": genre_name, 
                        "genre_id":genre_id, 
                        "genre_url": genre_url, 
                        "cat_id": cat_id, 
                        "cat_name":cat_name, 
                        "cat_url":cat_url
                        }
                    self.categories.append(cat_info)
            return self.categories
    
    def search_by_type(self, genre="fashiongoods"):
        '''method to get all the corresponding category ids of a genre 
        to search into the specific mall
        return a list of mall_ids'''
        #check if this genre exists
        search = []
        for n in self.categories:
            if n["genre_id"] == genre:
                search.append((n["cat_url"], n["cat_id"]))
        
        if len(search) == 0:
            print ("genre '%s' not found" %genre)
            return None  
        else:
            return search
        
    def search_by_brand(self, brand="vuitton"):
        
        if brand.lower() in self.brands.keys():
            return self.brand[brand.lower()]
        else:
            self.found = False
            ## here we match brand with uncomplete name
            ## it's a very lazy way of searching
            ## eg. vuitton ==> louis vuitton
            ## obviously we could implement other matching system more refined
            ## but not Now
            for b, v in self.brands.items():
                for n in re.split(" |&|\.", b):
                    # n is at least a three letter words and not empty
                    if n != "" and len(n) > 2:
                        if brand == n:
                            print("brand %s matches with %s" %(b, brand))
                            return self.brands[b]
            print ("brand %s not found" %brand)
            return None
    
    def extract_page(self, response):
        '''download_url and extract'''
        self.download_html(response)
        res = self.get_page(self.page)
        print(len(res))
        return res
        
    def get_page(self, page):
        '''extract the 45 results in the page'''
        return [self.get_item(n) for n in page.find_all("div",{"class":"rsrSResultSect"})]

    def get_item(self, page):
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
                "brand": self.brand,
                "category": self.category_id
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
    
    def get_search_results(self):
        '''return global search results for one query given the page
        results_nb
        page_nb
        list of next_urls
        results for other categories of products
        '''
        
        
    def get_neighbours(self, page):
        ''' get neighbours give the nb of products found in other categories
        during search help enlarge the initial search
        '''
        product_type = self.page.find("ul",{"class":"rsrAsideArrowLi rsrGenreNavigation"})
        stats = {}
        for n in product_type.find_all('a'):
            if n.find("span") is not None:
                try:
                    stats[n.get("data-genreid")] = get_nb(n.find("span", {"class": "rsrRegNum"}).text)
                except:
                    stats[n.get("data-genreid")] = 0
        return stats
    
    def create_table():
        conn = sqlite3.connect('/tmp/example')
        c = conn.cursor()
        c.execute("""
            create table items (tid int primary key not NULL ,)""")
        conn.commit()
    
    def download_html(self, r):
        if r.status_code == 200:
            soup = bs(r.text, "lxml")
            soup.prettify('utf-8')
            self.page = soup
            return True
        else:
            return False
            
    def search(self,brand, category_id):
        self.brand = brand
        self.category_id = category_id
        self.search_url = "http://search.rakuten.co.jp/search/mall/%s/%i/" %(quote(brand),category_id) 
        r = requests.get(self.search_url)
        self.download_html(r)
        self.get_search_results()
        #download the first page
        first_page = self.get_page(self.page)
        #download the next_urls using asynchronous requests
        session = FuturesSession(max_workers=5)
        for url in self.next_urls:
            future = session.get(url)
            
        future.add_done_callback(self.extract_page)    
        
    
    
    '''
    def search(self, brand= None, genre= None):
        filters = [brand, genre]
        if any(filters):
            if all(filters):
                print("Search by brand and by genre")
                self.brand = self.search_by_brand(brand)
                if self.brand is not None:
                    self.genre = self.search_by_type(genre)
                    if self.genre is not None:
                        print(genre, self.genre)
                        
                else:
                    return False
            #search by brand and by genre    
            else:
                if brand is not None:
                    #by brand
                    print("Searching by brand")
                    if self.search_by_brand(brand):
                        
                        pass
                    else:
                        return False
                else:
                    #by genre
                    print("Searching by genre")
                    self.search_by_genre(genre)
        else:
            print("Please, provide a query a brand or a product")
            return False
    '''
if __name__== "__main__":
    r = RakutenExtractor()
    #~ r.collect_categories()
    #~ print r.search_by_genre("fashio")
    #r.collect_brands()
    #r.collect_categories()
    #print r.search(brand="hilfiger", genre="fashiongoods")
    #gucci/216131
    r.search("tommy hilfiger", 216131)
