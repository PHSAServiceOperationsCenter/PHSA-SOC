#!/usr/bin/python
import datetime
import json
import mysql.connector as mariadb
#mariadb_connection = mariadb.connect(user='root', password='', database='demodb')

class reg(object):
    def __init__(self, cursor, row):
        for (attr, val) in zip((d[0] for d in cursor.description), row) :
            setattr(self, attr, val)

class Database:

    def __init__(self):
        host = 'localhost'
        user = 'root'
        password = ''
        database = 'demodb'
        connection = None
        cursor = None
        self.dbInit()

    def dbInit (self):
        self.connection = mariadb.connect(user='root', password='', database='demodb')
        self.cursor = self.connection.cursor()

    def set_record(self, data):
        cert_id = '12345'
        port = 'abcd' #[0]
        a = [cert_id, port]
        print (data)
        print ("INSERT INTO table VALUES %r;" % (tuple(a),))
        self.cursor.execute(sql, args)
        try:
            self.cursor.execute(sql)
            self.connection.commit()
        except:
            self.connection.rollback()

    def dictValuePad(key):
        return '%(' + str(key) + ')s'

    def get_record(self, query):
        try:
            rc = []
            print ("sql:%s" % (query));
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            items = []
            for row in rows:
              r = reg(self.cursor, row)
              try:
                cid = r.id
              except:
                cid = 0

              try:
                port = r.port
              except:
                port =""
              rc = [cid, port]

              try:
                ssl_cert = r.ssl_cert
              except:
                ssl_cert = 0

              try:
                keytype = r.keytype
              except:
                keytype =""

              try:
                keybits = r.keybits
              except:
                keybits = 0

              try:
                valid_from = r.valid_from
              except:
                valid_from =""

              try:
                valid_until = r.valid_until
              except:
                valid_until =""

              try:
                valid_until = r.valid_until
              except:
                valid_until =""

              try:
                status = r.status
              except:
                status =""
              items.append({'id':cid, 'port':port, 'ssl_cert':ssl_cert, 'keytype':keytype, 'keybits':keybits, 'valid_from':valid_from, 'valid_until':v                                 alid_until, 'status': status})
            self.set_record(items)
            return json.dumps({'items': items}, default=str) #rc

        except:
           data = {}
           return data

    # def query(self, query):
    #     cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)
    #     cursor.execute(query)
    #     return cursor.fetchall()

    def __del__(self):
        self.connection.close()


if __name__ == "__main__":
    db = Database()
    # CleanUp Operation
    query = "select * from certs;" # where status = 'new' limit 1" # "DELETE FROM basic_python_database"
    res = db.get_record(query)
    print ("Mark II")
    print(res)
    # db.insert(del_query)
    # # Data Insert into the table
    # query = """
    #     INSERT INTO basic_python_database
    #     (`name`, `age`)
    #     VALUES
    #     ('Mike', 21),
    #     ('Michael', 21),
    #     ('Imran', 21)
    #     """
    #
    # # db.query(query)
    # db.insert(query)

