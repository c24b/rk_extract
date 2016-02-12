#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pymongo
import sys

class MongoDB(object):
    def __init__(self,  database_name, host="localhost", port=27017):
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
        self.db_name = database_name
        self.db = getattr(self.client,database_name)
        
    
        
    
