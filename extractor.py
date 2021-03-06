#!/usr/bin/env python3
#coding: utf-8
import requests
from bs4 import BeautifulSoup as bs
import re
from urllib.parse import urlparse,urljoin, quote, quote_plus
# Asynchronous HTTP Requests in Python 3.2
#quite usefull when tons of urls have to be downloaded
from requests_futures.sessions import FuturesSession
import pymongo
from langdetect import detect

RE_INT = re.compile('([0-9+])', re.UNICODE)

def get_nb(results):
    '''mini method to catch number'''
    try:
        m = [n.group() for n in re.finditer(RE_INT, results)]
        return int("".join(m))
    except ValueError:
        return None

class Database(object):
    def __init__(self, host="localhost", port=27017, database_name="rakuten"):
        self.HOST = host
        self.PORT = port
        self.client = ""
        self.DB = ""
        try:
            self.client = pymongo.MongoClient(self.HOST, self.PORT)
        except:
            self.client = pymongo.MongoClient()
        self.version = self.client.server_info()['version']
        self.t_version = tuple(self.version.split("."))
        self.db_name = database_name
        self.db = getattr(self.client,database_name)
class RkSearch(object):
    def __init__(self, **kwargs):
        DB = Database()
        self.db = DB.db
        self.query = kwargs
        
    def search_by_genre(self, genre="fashiongoods"):
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
        '''method to search by brand'''
        if brand.lower() in self.brands.keys():
            return self.brand[brand.lower()]
        else:
            self.found = False
            ## here we match brand with uncomplete name
            ## it's a very lazy way of searching
            ## eg. vuitton ==> louis vuitton
            ## obviously we could implement other matching system more refined
            ## TODO then
            for b, v in self.brands.items():
                for n in re.split(" |&|\.", b):
                    # n is at least a three letter words and not empty
                    if n != "" and len(n) > 2:
                        if brand == n:
                            print("brand %s matches with %s" %(b, brand))
                            return self.brands[b]
            print ("brand %s not found" %brand)
            return None
    def search_mall(self, tag=""):
        pass
    def search_by_cat(self, cat="レディースバッグ"):
        pass
    def search_by_tag(self, tag="レディースバッグ"):
        pass
    def search(self):
        
        pass
class RakutenExtractor(object):
    def __init__(self):
        #define entry point for scrapping data
        #general sitemap with entry level 0
        self.genre_url = "http://directory.rakuten.co.jp/"
        #brand entry
        self.brand_url = "http://event.rakuten.co.jp/brand/"
        #search entry
        self.search_url = "http://search.rakuten.co.jp/"
        #base url of a given category level 1
        self.cat_url = "http://directory.rakuten.co.jp/category/"
        #base url for a mall
        self.mall_url = "http://search.rakuten.co.jp/search/mall/-/"
        #base url sheam for a filtered search by mall and brand
        #self.url = "http://search.rakuten.co.jp/search/mall/%s/%i/" %(self.brand, self.mall_id)
        #DB = Database()
        #self.db = DB.db
        #self.collect()
        
        
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
            
    def collect_brands(self):
        '''brands are defined by editorialisation work inside event
        brands are listed in a dict (json format compatible) with corresponding langage
        '''
        self.brands = {"jap":{}, "en":{}}
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
                tags_en = [n for n in re.split(" |&|・", name_en)  if n!= ""]
                self.brands["jap"][name_jp] = {"url": brand_url, "tags": tags_jp, "en": name_en.lower()}
                self.brands["en"][name_en.lower()] = {"url": brand_url, "tags": tags_en, "jap": name_jp}
                
        return self.brands
    def collect(self):
        '''collect data from rk website and store it'''
        self.collect_brands()
        self.collect_typology()
        #~ for n in self.brands:
            #~ self.db.brands.insert(n)
        #~ for n in self.categories:
            #~ self.db.categories.insert(n)
        #~ for n in self.genres:
            #~ self.db.genres.insert(self.n)
        return self
    
    def store_results(self):
        pass

    
    def collect_typology(self):
        ''' 
        two levels are available on rk sitemap
        genre (level 0) generic and category (level1) specific
        return genres with corresponding categories
        and categories with the corresponding genre
        '''
        #genre are main categories level 0
        self.genres = []
        #categories are spécific market place level 1
        self.categories = []
        soup = self.parse(self.genre_url)

        genres = [(g.find("a").get("href"), (g.text).encode('utf-8'))  for g in soup.find_all("h2", {"class":"genreTtl"})]
        cats = soup.find_all("ul", {"class":"genreList"})
        
        for g, cat in zip(genres, cats):
            genre = {}
            genre["url"] = g[0]
            
            genre["id"] = genre["url"].split("/")[-2]
            genre["name"] = g[1].decode('utf-8')
            genre["tags"]  = re.split("・|ー| |&",genre["name"])
            genre["ids"] = []
            genre["categories"] = []
            for n in cat.find_all("li"):
                url = n.find("a").get("href")
                text = re.sub('\n|\(=>\)', "", n.text)
                tags = re.split("・|ー| |&",text)
                tags = [n for n in tags if n != ""]
                cat_id =  url.split("/")[-2]
                genre["ids"].append(cat_id)
                categ = {"url": url, "tags": tags, "name": text, "id": cat_id}
                genre["categories"].append(categ)
                categ["genre_id"] = genre["id"]
                self.categories.append(categ)
            self.genres.append(genre)
            self.categories.append(categ)
        return self

    def get_results(self, page):
        '''extract the 45 items from results in the page'''
        return [self.get_item(n) for n in page.find_all("div",{"class":"rsrSResultSect"})]

    def get_item(self,page):
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
    
    def search_mall_id(self, url):
        self.results = {}
        soup = self.parse(url, "utf-8")
        
        self.others = self.get_repartition(soup)
        top_mall_ids = soup.find("li", {"class":"recommendedTopLi"})
        return [a.get("data-genreid") for a  in top_mall_ids.find_all("a")]
            
            
        
    def search_by_brand(self, brand):
        '''method to search by brand return the mall ids with results repartition'''
        self.collect_brands()
        if detect(brand) == "ja":
            if brand in self.brands["jap"].keys():
                return self.search_mall_id(self.brands["jap"][brand]["url"])
            else:
                brand_t = re.split("・|ー| |&", brand)
                for k,v in self.brands["jap"].items():
                    for t in v["tags"]:
                        if t == brand:
                            return(self.search_mall_id(self.brands["jap"][k]["url"]))
                        for tag in brand_t:
                            if tag == t:
                                return(self.search_mall_id(self.brands["jap"][k]["url"]))
        else:
            if brand.lower() in self.brands["en"].keys():
                
                return(self.search_mall_id(self.brands["en"][brand.lower()]["url"]))
            else:
                brand_t = re.split("・|ー| |&", brand)
                for k,v in self.brands["en"].items():
                    for t in v["tags"]:
                        if t == brand:
                            return(self.search_mall_id(self.brands["en"][k]["url"]))
                        for tag in brand_t:
                            if tag == t:
                                return(self.search_mall_id(self.brands["en"][k]["url"]))
    def search_by_kw(self, kw):
        pass
    def search_by_id(self, cat_id):
        self.collect_typology()
        return [n["tags"] for n in self.categories if n["id"] == cat_id or n["tags"] for n in self.genres if n["id"] == cat_id]
    
    def get_search_results(self, brand=None, mall_id=None):
        
        '''return global search results for one query given the page
        results_nb
        page_nb
        results for other categories of products
        and return next_urls
        '''
        filters = [brand, mall_id]
        if any(filters) is False:
            return sys.exit("Provide at least one argument brand or mall_id")
        else:
            self.results = {}
            if all(filters):
                url = "http://search.rakuten.co.jp/search/mall/%s/%i/" %(brand,mall_id)
            else:
                if mall_id is not None :
                    url = "http://search.rakuten.co.jp/search/mall/-/%i/" %(mall_id)
                else:
                    url = "http://search.rakuten.co.jp/search/mall/%s/" %(brand)
        self.brand = brand
        self.category_id = mall_id
        page = self.parse(url, "utf-8")
        self.results["results_nb"] =  self.get_results_nb(page)
        self.results["page_nb"] = self.get_pagination(self.results_nb)
        self.results["stats"] = self.get_repartition(page)
        #first page already downloaded so DRY
        #and insert it directly into items
        self.db.items.insert(self.get_results(page))
        self.next_urls = [url+"?p="+str(x) for x in range(2, self.page_nb+1)]
        return self
        
    def get_pagination(self, nb, offset=45):
        '''calculate page nb offset'''
        self.page_nb = int(self.results_nb/offset)
        rest = self.results_nb%45
        if rest > 0:
            self.page_nb =  self.page_nb+1
        self.page_nb = int(self.results_nb/offset)
        rest = self.results_nb%offset
        if rest > 0:
            self.page_nb =  self.page_nb+1
        return self.page_nb
        
    def get_results_nb(self, page):
        '''scrap the nb of search result'''
        res = page.find("div",{"class":"rsrDispTxtBoxRight"}).b.next.next
        if res is not None:
            self.results_nb = get_nb(res)
        else:
            self.results_nb = 0 
        
        
    def get_repartition(self,soup):
        '''
        get repartition in categories and genre of a search results
        '''
        stats = {}
        try:
            product_type = soup.find("ul",{"class":"rsrGenreNavigation"})
            
            for n in product_type.find_all('a'):
                if n.find("span") is not None:
                    cat_id = n.get("data-genreid")
                    text = n.text.split("\n")[0]
                    nb = get_nb(n.find("span", {"class": "rsrRegNum"}).text)
                    stats[cat_id] = {"nb_results": nb, "tags":self.search_by_id(cat_id), "genre":text}
                    
        except AttributeError:
            pass
        
        return stats
    
    


if __name__== "__main__":
    r = RakutenExtractor()
    #r.collect()
    #r.collect_brands()
    #print(r.genres[-1]["id"])
    #print(r.categories[-1])
    #print(r.brands)
    #r.search_by_brand("の検索結果")
    r.collect()
    #print(r.categories[0])
    #print(r.genres[0])
    #print(r.search_by_brand("louis vuitton"))
    print(r.search_by_brand("ルイ ヴィトン"))
    #r.get_search_results("vuitton", 216131)
    #print(r.results)
    
    
