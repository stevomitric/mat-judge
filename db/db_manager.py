''' Database managment '''

import sqlite3, random, os

DB_PATH = 'db/'
DB_NAME = 'mat-judge.sqlite3'

# If databse file has not benn created
DB_DEFAULT = {
    'sub_id': random.randint(10**6, 10**7-1),
    'token_access': 0,
    'passive_submissions': 0,
    'ip_status_timeout': 100,
    'ip_submit_timeout': 5000,
}

class DB_Token:
    def __init__(self, db):
        self.db = db

    def get(self, token):
        curs = self.db.cursor()
        sql = "Select * from tokens where token='{}'".format(token)
        curs.execute(sql)
        data = curs.fetchone()
        curs.close()
        if data:
            return {
                'token': data[1],
                'owner': data[2],
                'access_level':  int(data[3]),
                'expiration': int(data[4])
            }
        return None

    def add(self, token, owner, access_level, expiration):
        access_level = int(access_level)
        expiration = str(expiration)
        sql = "INSERT INTO tokens(token, owner, access_level, expiration) VALUES('{}','{}',{},'{}')".format(token, owner, access_level, expiration)
        self.db.execute(sql)
        self.db.commit()

    def removeToken(self, token):
        sql = "DELETE from tokens where token='{}'".format(token)
        self.db.execute(sql)
        self.db.commit()

    def removeOwner(self, owner):
        sql = "DELETE from tokens where owner='{}'".format(owner)
        self.db.execute(sql)
        self.db.commit()

class DB_Testcases:
    def __init__(self, db):
        self.db = db

    def add(self, tc):
        ''' Adds 'tc' to the testcase list. tc must be a list of tuples. Returns ID of newly added testcase'''
        tc = str(tc).replace("'", '"')
        try:
            eval(tc)
        except:
            return -1
        curs = self.db.cursor()
        sql = "INSERT INTO testcases(testcase) VALUES('{}')".format(tc)
        curs.execute(sql)
        id = curs.lastrowid
        curs.close()
        self.db.commit()
        return id

    def get(self, id):
        ''' Gets testcase with given ID '''
        curs = self.db.cursor()
        sql = "SELECT testcase FROM testcases WHERE id='"+str(id)+"'"
        curs.execute(sql)
        data = curs.fetchone()
        curs.close()
        if not data:
            return -1
        return eval(data[0])

class DB:
    def __init__(self):
        self.db = self.connect()
        self.initTables()

        self.db_token = DB_Token(self.db)
        self.db_testcase = DB_Testcases(self.db)

    def connect(self):
        ''' Connects to the database and returns an sqlite3 connect object '''
        try:
            try:
                conn = sqlite3.connect(DB_PATH+DB_NAME, check_same_thread=False)
            except:
                conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            return conn
        except Exception as e:
            print("* FAILED TO CONNECT TO DB *")
            print(e)
        return None

    def reload(self):
        ''' Remove all data from the DB and init tables '''
        self.db.close()
        rm = [DB_PATH+DB_NAME, DB_NAME]
        for fl in rm:
            try:
                os.remove(fl)
            except:
                pass
        self.db = self.connect()
        self.initTables()

        self.db_token = DB_Token(self.db)
        self.db_testcase = DB_Testcases(self.db)

    def initTables(self):
        
        self.db.execute('''CREATE TABLE IF NOT EXISTS config (
                            id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                            sub_id integer NOT NULL DEFAULT {},
                            token_access integer NOT NULL DEFAULT {},
                            passive_submissions integer NOT NULL DEFAULT {},
                            ip_status_timeout integer NOT NULL DEFAULT {},
                            ip_submit_timeout integer NOT NULL DEFAULT {}
                        )'''.format(DB_DEFAULT["sub_id"], DB_DEFAULT["token_access"], DB_DEFAULT['passive_submissions'],
                                    DB_DEFAULT['ip_status_timeout'], DB_DEFAULT['ip_submit_timeout']))

        self.db.commit()
        self.db.execute('''CREATE TABLE IF NOT EXISTS tokens (
                            id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                            token text,
                            owner text,
                            access_level integer not NULL,
                            expiration text
                        )''')
        self.db.commit()
        self.db.execute('''CREATE TABLE IF NOT EXISTS testcases (
                            id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                            testcase text
                        )''')
        self.db.commit()

        ## chcek for the first row
        if not self.getConf():
            self.db.execute('''INSERT INTO config DEFAULT VALUES''')
            self.db.commit()

        print ("* Databse initialized *")

    def saveConf(self, field, value, type = int):
        if value == 'False' or value == 'false':
            value = 0
        if value == 'True' or value == 'true':
            value = 1
            
        if type == int:
            value = int(value)
        try:
            self.db.execute('''UPDATE config SET {}={} WHERE id=1'''.format(field, value))
            self.db.commit()
        except Exception as e:
            print ("Failed to write to the database: ", str(e))

    def getConf(self):
        curs = self.db.cursor()
        sql = '''SELECT sub_id, token_access, passive_submissions, ip_status_timeout, ip_submit_timeout from config'''
        curs.execute(sql)
        data = curs.fetchone()
        return data