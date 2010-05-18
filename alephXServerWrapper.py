#!/usr/bin/env python
#-*- coding:utf-8 -*-

import math, urllib, urllib2, libxml2, time, os, sys, sqlite3, logging

failed = []

LOG_FILENAME = "alephXServerWrapper.log"
logging.basicConfig(filename = LOG_FILENAME, level = logging.DEBUG)

class XServer(object):

  def __init__(self, endpoint, debug = False):
    """Parametr 'endpoint' je URL Aleph X Serveru, 'debug' s hodnotou True povoluje výpisy"""
    
    self.endpoint = endpoint
    self.debug = debug


class Base(object):
 
  def __init__(self, xServer, baseID):
    self.xServer = xServer
    self.ID = baseID
 
  def getParsedRecord(self, docNum):
    """Získá záznam dokumentu v bázi 'base' se systémovým číslem 'docNum'"""
    
    params = {
      "op" : "find_doc",
      "base" : self.ID,
      "doc_num" : str(docNum)
    }
    url = self.xServer.endpoint + "?" + urllib.urlencode(params)
    request = urllib2.urlopen(url)
    record = request.read()
    request.close()
    
    return Record(libxml2.parseDoc(record))
    
  def isValidDocNum(self, docNum):
    """Zkontroluje, zdali dokument hledaného čísla v databázi existuje."""
        
    doc = self.getParsedRecord(docNum)
    errorCheck = doc.getXPath("//error")
    if errorCheck == []:
      return True
    else:
      return False
 
  def getRecordCount(self):
    """Zjistí počet záznamů v databázi."""
    
    exp = 10
    previous = 0
    current = 0
    
    while True:
      previous = current
      current = int(pow(2, exp))
      if not (self.isValidDocNum(current)):
        break
      exp += 1
      
    minimum = previous
    maximum = current
    mid = int(math.floor((minimum + maximum)/2))
    
    while (minimum < maximum):
      if minimum + 1 == maximum:
        if self.isValidDocNum(maximum):
          mid = maximum
          break
        else:
          mid = minimum
          break
      
      if self.isValidDocNum(mid):
        minimum = mid
      else:
        maximum = mid - 1
      mid = int(math.floor((minimum + maximum)/2))
    
    return mid

 
class Crawler(object):

  def __init__(self, base):
    self.status = False
    self.base = base
    """Sleep time for none-KeyboardInterrupt exception"""
    self.sleep = 5
    """Testing variable"""
    self.test = 0
 
  def crawl(self, callback, sleep = 0.05):
    """Postupně projde všechny záznamy v databázi a pro každý zavolá 'callback'"""
    logging.debug("Počáteční status: %s" % (self.status))
    if self.status == False:
      try:
        resume = file("crawlerStatus.txt", "r")
        self.status = int(resume.read())
        resume.close()
      except:  
        self.status = 1
      
    begin = int(self.status)
    baseLen = self.base.getRecordCount()
    logging.debug("Délka crawlované báze: %d" % (baseLen))
    baseRange = range(begin, baseLen + 1)
    try:
      for i in baseRange:
        time.sleep(sleep) # Slušný crawler čeká sekundu mezi požadavky!
        self.status = str(i)
        callback(self.base.getParsedRecord(i))
    except KeyboardInterrupt:
        self.saveStatus(i, True)        
    except:
        if self.test != i:
          self.saveStatus(i)
        time.sleep(self.sleep)
        self.sleep = self.sleep*5
        self.test = i
        self.crawl(callback)
        
    
  def saveStatus(self, i, keyboardInterrupt = False):
    """Uloží číslo aktuálně zpracovávaného záznamu"""
    last = file("crawlerStatus.txt", "w")
    last.write(str(i))
    last.close()
    if keyboardInterrupt == True:
      sys.exit(0)
    

class Record(object):

  def __init__(self, doc):
    self.doc = doc
    
  def getXPath(self, xpath):
    """Vrátí pole výsledků pro XPath dotaz"""
    
    results = self.doc.xpathEval(xpath)
    output = []
    for result in results:
      output.append(result.content)
    return output
    
  def getMarc(self, field, subfield):
    """Vrátí pole výsledků pro hledané pole ('field') a podpole ('subfield')"""
 
    xpath = "//varfield[@id='%s']/subfield[@label='%s']" % (str(field), str(subfield))
    return self.getXPath(xpath)
    
        
class MarcARecord(Record):
 
  def __init__(self, record):
    Record.__init__(self, record.doc)
    
  def getID(self):
    """Vrátí ID záznamu"""
    return self.getXPath("//fixfield[@id='001']")
    
  def isPSH(self):
    """Určí, zdali jde o záznam PSH"""
    termID = self.getID()
    if termID:
      termID = termID[0]
      if "PSH" in termID:
        return True
    return False
    
  def getPrefLabelCS(self):
    """Vrátí preferované záhlaví hesla v češtině"""
    return self.getMarc("150", "a")[0]
    
  def getPrefLabelEN(self):
    """Vrátí preferované záhlaví hesla v angličtině"""
    return self.getMarc("750", "a")[0]
    
  def getNonprefLabelsCS(self):
    """Vrátí nepreferovaná záhlaví hesla v češtině"""
    return self.getXPath("//varfield[@id='450'][subfield[@label='9']='cze']/subfield[@label='a']")
    
  def getNonprefLabelsEN(self):
    """Vrátí nepreferovaná záhlaví hesla v angličtině"""
    return self.getXPath("//varfield[@id='450'][subfield[@label='9']='eng']/subfield[@label='a']")
    
  def getRelatedTerms(self):
    """Vrátí preferovaná záhlaví příbuzných hesel v češtině"""
    return self.getXPath("//varfield[@id='550'][not(subfield[@label='w'])]/subfield[@label='a']")
    
  def getNarrowerTerms(self):
    """Vrátí preferovaná záhlaví podřazených hesel v češtině"""
    return self.getXPath("//varfield[@id='550'][subfield[@label='w']='h']/subfield[@label='a']")
    
  def getBroaderTerms(self):
    """Vrátí preferovaná znění nadřazených hesel v češtině"""
    return self.getXPath("//varfield[@id='550'][subfield[@label='w']='g']/subfield[@label='a']")
    
 
class PSHDB(object):
 
  def __init__(self, purge=False):
    self.connection = False
    self.cursor = False
    
    if purge:
      os.remove("psh.db")
    
    self.createDB()
 
  def clearRelations(self):
    print "INFO: čistění vztahů"""
    self.query("""DELETE FROM hierarchie;""")
    self.query("""DELETE FROM pribuznost;""")
    
  def createDB(self):
    """Vytvoří databázi"""
    # timestamp = str(int(time.mktime(time.localtime())))  
    self.db = "psh.db" # % (timestamp)
    self.connection = sqlite3.connect(self.db)
    self.cursor = self.connection.cursor()
    self.buildSchema()

  def buildSchema(self):
    """Pokud je databáze prázdná, vytvoří schéma"""
    self.cursor.execute("""SELECT * FROM sqlite_master""")
    if self.cursor.fetchall() == []:
      print "INFO: Vytváření DB schématu."
      queries = [
        """CREATE TABLE hesla (id_heslo VARCHAR(10) PRIMARY KEY, heslo VARCHAR(150));""",
        """CREATE TABLE ekvivalence (id_heslo VARCHAR(10) PRIMARY KEY, ekvivalent VARCHAR(150));""",
        """CREATE TABLE hierarchie (nadrazeny VARCHAR(10), podrazeny VARCHAR(10));""",
        """CREATE TABLE pribuznost (id_heslo VARCHAR(10), pribuzny VARCHAR(10));""",
        """CREATE TABLE varianta (id_heslo VARCHAR(10), varianta VARCHAR(150), jazyk VARCHAR(2));"""
      ]

      for query in queries:
        self.query(query)
    
  def query(self, query):
    """Provede v databázi dotaz"""
    self.cursor.execute(query)
    self.connection.commit()
 
  def dump(self):
    """Exportuje databázi v textovém SQL formátu"""
    with open('dump.sql', 'w') as f:
      for line in self.connection.iterdump():
        f.write('%s\n' % line)  
        
  def termToID(self, term):
    """Převede preferované znění hesla v češtině na ID hesla"""
    self.cursor.execute("""SELECT id_heslo FROM hesla WHERE heslo='%s';""" % (term.replace("'", "''")))
    try:
      id = self.cursor.fetchone()[0]
    except TypeError:
      print "ERROR:", term, self.cursor.fetchone()
      self.close()
      raise SystemExit
      
    print "INFO: %s přeloženo na %s" % (term, str(id))
    return id
    
  def close(self):
    """Uzavře databázi"""
    self.cursor.close()
    self.connection.close()
 
  def extractLabels(self, record):
    """Ze záznamu získá preferovaná a nepreferovaná záhlaví"""
    record = MarcARecord(record)
    if record.isPSH():
      termID = record.getID()[0]
      print "INFO: překlad, aktuální heslo %s" % (termID)

      labelCS = record.getPrefLabelCS()
      labelEN = record.getPrefLabelEN()
      nonprefLabelsCS = record.getNonprefLabelsCS()
      nonprefLabelsEN = record.getNonprefLabelsEN()

      # print "INFO: aktuální labelCS %s" % (labelCS)
      # print "INFO: aktuální labelEN %s" % (labelEN)
      self.query("""INSERT INTO hesla (id_heslo, heslo) VALUES ("%s", '%s');""" % (termID, labelCS.replace("'", "''")))
      self.query("""INSERT INTO ekvivalence (id_heslo, ekvivalent) VALUES ("%s", "%s");""" % (termID, labelEN))
      for nonprefLabelCS in nonprefLabelsCS:
        self.query("""INSERT INTO varianta (id_heslo, varianta, jazyk) VALUES ("%s", "%s", "%s");""" % (termID, nonprefLabelCS, "cs"))
      for nonprefLabelEN in nonprefLabelsEN:
        self.query("""INSERT INTO varianta (id_heslo, varianta, jazyk) VALUES ("%s", "%s", "%s");""" % (termID, nonprefLabelEN, "en"))
    
  def extractRelations(self, record):
    """Ze záznamu získá vztahy mezi hesly"""
    record = MarcARecord(record)
    if record.isPSH():
      termID = record.getID()[0]
      print "INFO: vztahy, aktuální heslo %s" % (termID)
      
      relatedTerms = record.getRelatedTerms()
      narrowerTerms = record.getNarrowerTerms()
      broaderTerms = record.getBroaderTerms()
    
      for relatedTerm in relatedTerms:
        idRelated = self.termToID(relatedTerm)
        self.query("""INSERT INTO pribuznost (id_heslo, pribuzny) VALUES ("%s", "%s");""" % (termID, idRelated))
      for narrowerTerm in narrowerTerms:
        idNarrower = self.termToID(narrowerTerm)
        self.query("""INSERT INTO hierarchie (nadrazeny, podrazeny) VALUES ("%s", "%s");""" % (termID, idNarrower))
      for broaderTerm in broaderTerms:
        idBroader = self.termToID(broaderTerm)
        self.query("""INSERT INTO hierarchie (nadrazeny, podrazeny) VALUES ("%s", "%s");""" % (idBroader, termID))
    
  def buildTranslateTable(self, crawler):
    """Naplní překladovou tabulku mezi preferovanými zněními hesel a jejich ID"""
    crawler.crawl(self.extractLabels)
    
  def buildRelations(self, crawler):
    """Naplní tabulky zachycující vztahy mezi hesly"""
    crawler.crawl(self.extractRelations)
