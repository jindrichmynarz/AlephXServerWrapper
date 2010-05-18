#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
import re, time

output = []

def makeTranslateTable(record):
   record = MarcARecord(record)
   if record.isPSH():
     print "ID záznamu: %s" % (record.getID()[0])
     prefLabelCS = record.getPrefLabelCS()
     print "INFO: heslo %s" % (prefLabelCS)
     
     sysno = record.getID()[0]
     sysno = re.search("\d+$", sysno).group(0).lstrip("0")
     uri = "http://data.techlib.cz/resource/psh/%s" % (sysno)
     print "INFO: URI %s" % (uri)
     
     output.append(";".join([prefLabelCS, uri]))
   else:
    print "INFO: není to PSH."
  
print "INFO: inicializace X Serveru"
a = XServer("http://aleph.techlib.cz/X", debug=True)
print "INFO: inicializace báze"
b = Base(a, "STK10")
print "INFO: inicializace crawleru"
c = Crawler(b)
print "INFO: začátek crawlování"
c.crawl(makeTranslateTable, sleep=0)

file = open("pshTranslateTable.csv", "w")
print "INFO: zápis výstupu"
file.write("\n".join(output))
file.close()
