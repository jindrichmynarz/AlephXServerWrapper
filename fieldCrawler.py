import libxslt
import urllib2
import libxml2
import re
import sys
from operator import itemgetter
from alephXServerWrapper import *            
      
def fieldCrawler(database, recordCount, rootElements = ""):
  paramUrl = "http://aleph.techlib.cz/X?op=find_doc&base=%s&doc_num="
  xpath2count = {}
  xpathCount = []
  error = 0
  
  styledoc = libxml2.parseFile("fieldCrawler.xslt")
  style = libxslt.parseStylesheetDoc(styledoc)
  
  for i in range(recordCount):
    url = paramUrl % database + str(i + 1)
    if i % 50 == 0:
      print i
    try:
      xml = urllib2.urlopen(url)
      text = xml.read()
      if not "<error>" in text:
        parsedXml = libxml2.parseDoc(text)
        result = style.applyStylesheet(parsedXml, None)
        resultList = str(result).split("\n")
        uniqueXpath = set(resultList)
    
        for xpath in uniqueXpath:
          if xpath in xpath2count:
            xpath2count[xpath] += 1
          else:
            xpath2count[xpath] = 1
      else:
        error += 1     
    except KeyboardInterrupt:
      sys.exit()
    except:
      error += 1  
  
  records = i - error + 1
  
  for item in xpath2count.keys():
    if not "?xml" in item and item != "":
      stem = re.sub(rootElements, "", item)
      percentage = round((float(xpath2count[item])/records), 3)
      xpathCount.append((stem, percentage))
  
  sortedXpath = sorted(xpathCount, key=itemgetter(1, 0), reverse=True)
  output = file("%s.csv" %database, "w")
  output.write("XPath;Rate;\n")
  for item in sortedXpath:
    output.write("%s;%s;\n" %(item[0], item[1]))
    
  output.write("The count of records: %s\n" %records)  
  output.close()

xServerUrl = "http://aleph.techlib.cz/X" 
database = "STK10"
rootElements = "find-doc/record/metadata/oai_marc/"

x = XServer(xServerUrl)
db = Base(x, database)
recordCount = db.getRecordCount()

fieldCrawler(database, recordCount, rootElements)
