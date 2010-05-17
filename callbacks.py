#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
from Mapper import *


class Callback(Object):
  
  def __init__(self, baseName):
    self.results = [] # (subject, predicate, object)
    self.unmapped = [] # (XPath, value)
    self.baseName = baseName
    self.resourceURI = "" # URI for the resource
    self.representationURI = "" # URI for the representation
    
  def commitData(self):
    """Saves self.results into RDFLib."""
    pass
    
  def writeUnmapped(self):
    """Saves unmapped data to output CSV."""
    timestamp = str(int(time.mktime(time.localtime())))  
    filename = "%s-%d.csv" % (self.baseName, timestamp)
    file = open(filename, "w")
    file.write("\n".join(map((lambda unmap: ";".join(unmap)), self.unmapped)))
    file.close()
    
  def main(self, record):
    """Main data extraction. Must be overwritten by a child class."""
    pass
  
  def addTriples(self, triples):
    """Generic method for adding triples."""
    [self.results.append(triple) for triple in triples]
    
  def addStaticTriplesGlobal(self):
    """Method for adding triples that are stable for each database."""
    triples = [
      (self.representationURI, "dcterms:rigthsHolder", "http://www.techlib.cz"),
      (self.representationURI, "cc:attributionName", "Národní technická knihovna"),
      (self.representationURI, "cc:attributionURL", self.representationURI),
      (self.representationURI, "cc:license", "http://creativecommons.org/licenses/by-nc-sa/3.0/cz/"),
    ]
    self.addTriples(triples)
    
  def addStaticTriplesBase(self):
    """Method for adding triples that are stable for the specific database. Must be overwritten by a child class."""
    pass
    
  def run(self):
    """Runs the callback."""
    self.main()
    self.addStaticTriplesGlobal()
    self.addStaticTriplesBase()
    self.commitData()
    self.writeUnmapped()
  
  
class STK02Callback(Callback):
  
  def __init__(self, baseName="STK02"):
    Callback.__init__(self)
    
  def main(self, record):
    sysno = record.getXPath("//fixfield[@id='001']")[0]
    subject = re.search("\d+$", sysno).group(0).lstrip("0")
    subject = "http://data.techlib.cz/resource/issn/%s" % (subject)
    self.resourceURI = subject
    self.representationURI = subject + ".rdf"
    self.results.append((self.representationURI, "dc:identifier", sysno))
    
    # Last modified date
    lastModified = record.getXPath("//fixfield[@id='005']")[0]
    parseDate = re.search("^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})", lastModified)
    lastModified = "%s-%s-%s+%s:%s" % (parseDate.group(1), parseDate.group(2), parseDate.group(3), parseDate.group(4), parseDate.group(5))
    self.results.append((self.representationURI, "dcterms:modified", lastModified)) # Jak přidat anotaci XSD type?
    
    # Short title
    shortTitle = record.getXPath('//varfield[@id="210"][@i1="1"]/subfield[@label="a"]')
    if not shortTitle == []:
      shortTitle = shortTitle[0]
      self.results.append((self.resourceURI, "bibo:shortTitle", shortTitle))
    
    # Publisher      
    publisher = record.getXPath('//varfield[@id="260"]/subfield[@label="b"]')
    if not publisher == []:
      publisher = publisher[0]
      self.results.append((self.resourceURI, "dc:publisher", publisher))
      # Namapovat vydavatele? PublisherMapper

    # Place of publication
    publicationPlace = record.getXPath('//varfield[@id="260"]/subfield[@label="a"]')
    if not publicationPlace == []:
      publicationPlace = publicationPlace[0]
      # Dodělat:
      #   - predikát?
      #   - zdali to nevypovídá spíše o vydavateli?
      # self.results.append((self.resourceURI, "", publicationPlace))

  def addStaticTriplesBase(self):
    triples = [
      (self.resourceURI, "rdf:type", "bibo:Periodical"),
    ]
    self.addTriples(triples)
    
    
class STK10Callback(Callback):
  
  def __init__(self, baseName="STK10"):
    Callback.__init__(self)
    
  def main(self, record):
    pass
    
  def addStaticTriplesBase(self):
    pass


class STK01Callback(Callback):
  
  def __init__(self, baseName="STK01"):
    Callback.__init__(self)
    
  def main(self, record):
    pass
    
  def addStaticTriplesBase(self):
    pass
