#!/usr/bin/env python
import sys
import getopt
import mysql.connector

from libnmap.process import NmapProcess


class GetXML(object):
    def __init__(self, remoteSite):
      self.remoteSite = remoteSite

    def fetchNmapData(self):
        nm = NmapProcess(self.remoteSite, options='--script ssl-cert')
        nm.run()
        return nm.stdout
            
    def __del__(self):
        pass
        #self.dbCur.close()
        #self.dbConn.close()

if __name__ == "__main__":
    try: 
        nmapInput = sys.argv[1]
    except:
        print ("*** missing Nmap XML file ***")

    xml_object = GetXML("localhost", "root", "",  "demodb", nmapInput)
    #self.dbConn = mysql.connector.connect(host="localhost", user="root", passwd="",  database="demodb")
    rc = xml_object.fetchNmapData()
    print(rc)
