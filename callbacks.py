#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
from Mapper import *
import rdflib
import rdflibWrapper

class Callback():
  
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
      (self.representationURI, rdflibWrapper.namespaces["dcterms"]["rigthsHolder"], rdflib.URIRef("http://www.techlib.cz")),
      (self.representationURI, "cc:attributionName", rdflib.Literal("Národní technická knihovna", lang="cs")),
      (self.representationURI, "cc:attributionURL", self.representationURI),
      (self.representationURI, "cc:license", rdflib.URIRef("http://creativecommons.org/licenses/by-nc-sa/3.0/cz/")),
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
    self.resourceURI = rdflib.URIRef(subject)
    self.representationURI = rdflib.URIRef(subject + ".rdf")
    self.results.append((
      self.representationURI,
      rdflibWrapper.namespaces["dc"]["identifier"],
      rdflib.Literal(sysno)
    ))
    
    # Last modified date
    lastModified = record.getXPath("//fixfield[@id='005']")[0]
    parseDate = re.search("^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})", lastModified)
    lastModified = "%s-%s-%s+%s:%s" % (parseDate.group(1), parseDate.group(2), parseDate.group(3), parseDate.group(4), parseDate.group(5))
    self.results.append((
      self.representationURI, 
      rdflibWrapper.namespaces["dcterms"]["modified"], 
      rdflib.Literal(lastModified, datatype = rdflibWrapper.namespaces["xsd"]["date"])
    ))
    
    # Short title
    shortTitle = record.getXPath('//varfield[@id="210"][@i1="1"]/subfield[@label="a"]')
    if not shortTitle == []:
      shortTitle = shortTitle[0]
      self.results.append((
        self.resourceURI, 
        rdflibWrapper.namespaces["bibo"]["shortTitle"],
        rdflib.Literal(shortTitle)
      ))
    
    # Publisher      
    publishers = record.getXPath('//varfield[@id="260"]/subfield[@label="b"] | //varfield[@id="720"][@i1="2"]/subfield[@label="a"]')
    if not publishers == []:
      for publisher in publishers:
        publisher = publisher.strip().strip(",").strip(";").strip(":").strip()
        self.results.append((
          self.resourceURI, 
          rdflibWrapper.namespaces["dc"]["publisher"],
          rdflib.Literal(publisher)
        ))
        # Namapovat vydavatele? PublisherMapper

    # Place of publication
    publicationPlace = record.getXPath('//varfield[@id="260"]/subfield[@label="a"]')
    if not publicationPlace == []:
      publicationPlace = publicationPlace[0]
      # Dodělat:
      #   - predikát?
      #   - zdali to nevypovídá spíše o vydavateli?
      # self.results.append((self.resourceURI, "", publicationPlace))
      
    # ISSN
    issns = record.getXPath('//varfield[@id="022"]/subfield[@label="a" or @label="l"]')
    if not issns == []:
      # Počítá s tím, že nakonec proběhne deduplikace triplů.
      for issn in issns:
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["bibo"]["issn"],
          rdflib.Literal(issn)
        ))

    # Date
    date = record.getXPath('//varfield[@id="260"]/subfield[@label="c"]')
    if not date == []:
      date = date[0]
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["date"],
        rdflib.Literal(date)
      ))
      # Vyčistit a dodělat rozmezí dat!
      
    # Titles
    titles = record.getXPath('//varfield[@id="222"][@i2="0"]/subfield[@label="a"] | //varfield[@id="245"][@i1="1"]/subfield[@label="a"] | //varfield[@id="246"]/subfield[@label="a"]')
    if not titles == []:
      for title in titles:
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["title"],
          rdflib.Literal(title)
        ))
    
    # Short title
    shortTitle = record.getXPath('//varfield[@id="210"][@i1="1"][@i2=" "]/subfield[@label="b"]')
    if not shortTitle == []:
      shortTitle = shortTitle[0]
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["bibo"]["shortTitle"],
        rdflib.Literal(shortTitle)
      ))
      
    # Language
    languages = LanguageMapper(record).mapData()
    if languages:
      [self.results.append(language) for language in languages]
    
    # ISSN links
    issnLinks = ISSNMapper(record).mapData()
    if issnLinks:
      [self.results.append(issnLink) for issnLink in issnLinks]
      
    # Online version of the journal
    onlineVersion = record.getXPath('//varfield[@id="856"][@i1="4"]/subfield[@label="u"]')
    if not onlineVersion == []:
      onlineVersion = onlineVersion[0]
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dcterms"]["hasVersion"],
        rdflib.URIRef(onlineVersion)
      ))
      # Validate onlineVersion URI?
      
  def addStaticTriplesBase(self):
    triples = [(
      self.resourceURI,
      rdflibWrapper.namespaces["rdf"]["type"], 
      rdflibWrapper.namespaces["bibo"]["Periodical"]
    ),]
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
