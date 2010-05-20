#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
from Mapper import *
import rdflib
import rdflibWrapper

def report(message):
  """Helper debugging function"""
  print message
  # Potenciálně zapisování do logu pomocí package logging
  
class Callback():
  
  def __init__(self, baseName):
    self.results = [] # (subject, predicate, object)
    self.unmapped = [] # (XPath, value)
    self.baseName = baseName
    self.resourceURI = "" # URI for the resource
    self.representationURI = "" # URI for the representation
    
  def commitData(self):
    """Saves self.results into RDFLib."""
    rdflibWrapper.commitData(self.results)
    self.results = []
    
  def writeUnmapped(self):
    """Saves unmapped data to output CSV."""
    timestamp = str(int(time.mktime(time.localtime())))  
    filename = "%s-%d.csv" % (self.baseName, timestamp)
    file = open(filename, "w")
    file.write("\n".join(map((lambda unmap: ";".join(unmap)), self.unmapped)))
    file.close()
  
  def getIdentifiers(self, uriBase):
    sysno = self.record.getXPath("//fixfield[@id='001']")[0]
    subject = re.search("\d+$", sysno).group(0).lstrip("0")
    subject = "http://data.techlib.cz/resource/%s/%s" % (uriBase, subject)
    self.resourceURI = rdflib.URIRef(subject)
    self.representationURI = rdflib.URIRef(subject + ".rdf")
    self.results.append((
      self.representationURI,
      rdflibWrapper.namespaces["dc"]["identifier"],
      rdflib.Literal(sysno)
    ))
  
  def getLastModifiedDate(self):
    """Extracts the date of last modification"""
    lastModified = LastModifiedDateMapper(self.record, self.resourceURI, self.representationURI).mapData()
    if lastModified:
      self.results.append(lastModified[0])
  
  def getDataFromFixfield008(self):
    """Extract and map the data from fixfield 008"""
    fixfield008Results = Fixfield008Mapper(self.record, self.resourceURI, self.representationURI).mapData()
    if fixfield008Results:
      self.addTriples(fixfield008Results)

  def getPublicationDate(self):
    date = self.record.getXPath('//varfield[@id="260"]/subfield[@label="c"]')
    if not date == []:
      date = date[0]
      # Oříznout všechny nenumerické znaky?
      # Co se závorkami a otazníky?
      # date = re.search(".*(\d{4}).*", date) 
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["date"],
        rdflib.Literal(date)
      ))
      # Vyčistit a dodělat rozmezí dat!
  
  def getPublisher(self):
    publishers = self.record.getXPath('//varfield[@id="260"]/subfield[@label="b"] | //varfield[@id="720"][@i1="2"]/subfield[@label="a"]')
    if not publishers == []:
      for publisher in publishers:
        publisher = publisher.strip().rstrip(",").rstrip(";").rstrip(":").rstrip()
        bnodeID = rdflib.BNode()
        self.addTriples([(
          self.resourceURI, 
          rdflibWrapper.namespaces["dc"]["publisher"],
          rdflib.Literal(publisher)
        )])
    placeOfPublication = self.record.getXPath('//varfield[@id="260"]/subfield[@label="a"]')
    if not placeOfPublication == []:
      placeOfPublication = placeOfPublication[0].strip(":").strip(";").strip()
      self.addTriples([(
        self.resourceURI, 
        rdflibWrapper.namespaces["dc"]["publisher"],
        bnodeID
      ), (
        bnodeID,
        rdflibWrapper.namespaces["dbpedia"]["locatedIn"],
        rdflib.Literal(placeOfPublication)
      )])
      # Namapovat vydavatele? PublisherMapper
      
  def getUDC(self):
    udc = self.record.getXPath('//varfield[@id="080"]/subfield[@label="a"]')
    if not udc == []:
      udc = udc[0].strip()
      bnodeID = rdflib.BNode()
      self.addTriples([(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["subject"],
        bnodeID
      ), (
        bnodeID,
        rdflibWrapper.namespaces["rdf"]["value"],
        rdflib.Literal(udc)
      ), (
        bnodeID,
        rdflibWrapper.namespaces["dcam"]["memberOf"],
        rdflibWrapper.namespaces["dcterms"]["UDC"]
      )])
        
  def main(self):
    """Main data extraction. Must be overwritten by a child class."""
    pass
  
  def addTriples(self, triples):
    """Generic method for adding triples."""
    [self.results.append(triple) for triple in triples]
    
  def addStaticTriplesGlobal(self):
    """Method for adding triples that are stable for each database."""
    triples = [(
        self.representationURI, 
        rdflibWrapper.namespaces["dcterms"]["rigthsHolder"], 
        rdflib.URIRef("http://www.techlib.cz")
      ), (
        self.representationURI,
        rdflibWrapper.namespaces["cc"]["attributionName"],
        rdflib.Literal("Národní technická knihovna", lang="cs")
      ), (
        self.representationURI,
        rdflibWrapper.namespaces["cc"]["attributionName"],
        rdflib.Literal("National Technical Library", lang="en")
      ), (
        self.representationURI,
        rdflibWrapper.namespaces["cc"]["attributionURL"],
        self.representationURI
      ), (
        self.representationURI,
        rdflibWrapper.namespaces["cc"]["license"],
        rdflib.URIRef("http://creativecommons.org/licenses/by-nc-sa/3.0/cz/")
      ), (
        self.representationURI,
        rdflibWrapper.namespaces["dcterms"]["rightsHolder"],
        rdflib.URIRef("http://www.techlib.cz")
      ),
    ]
    self.addTriples(triples)
    
  def addStaticTriplesBase(self):
    """Method for adding triples that are stable for the specific database. Must be overwritten by a child class."""
    pass
    
  def run(self, record):
    """Runs the callback."""
    self.record = record
    self.main()
    self.addStaticTriplesGlobal()
    self.addStaticTriplesBase()
    self.commitData()
    self.writeUnmapped()
    if len(self.results) > 1000:
      self.commit()
  
  
class STK02Callback(Callback):
  
  def __init__(self, baseName="STK02"):
    Callback.__init__(self)
    
  def main(self):
    # Write URIs & identifiers
    self.getIdentifiers("issn")
    
    # Mapping the fixfield 008
    self.getDataFromFixfield008()
      
    # Last modified date
    self.getLastModifiedDate()   
    
    # Short title
    shortTitle = self.record.getXPath('//varfield[@id="210"][@i1="1"]/subfield[@label="a"]')
    if not shortTitle == []:
      shortTitle = shortTitle[0]
      self.results.append((
        self.resourceURI, 
        rdflibWrapper.namespaces["bibo"]["shortTitle"],
        rdflib.Literal(shortTitle)
      ))
    
    # Universal Decimal Classification
    self.getUDC()
    
    # Publisher      
    self.getPublisher()

    # Place of publication
    publicationPlace = self.record.getXPath('//varfield[@id="260"]/subfield[@label="a"]')
    if not publicationPlace == []:
      publicationPlace = publicationPlace[0]
      # Dodělat:
      #   - predikát?
      #   - zdali to nevypovídá spíše o vydavateli?
      # self.results.append((self.resourceURI, "", publicationPlace))
      
    # ISSN
    issns = self.record.getXPath('//varfield[@id="022"]/subfield[@label="a" or @label="l"]')
    if not issns == []:
      # Počítá s tím, že nakonec proběhne deduplikace triplů.
      for issn in issns:
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["bibo"]["issn"],
          rdflib.Literal(issn)
        ))

    # Date
    self.getPublicationDate()
    
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
    shortTitle = self.record.getXPath('//varfield[@id="210"][@i1="1"][@i2=" "]/subfield[@label="b"]')
    if not shortTitle == []:
      shortTitle = shortTitle[0]
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["bibo"]["shortTitle"],
        rdflib.Literal(shortTitle)
      ))
      
    # Language
    languages = LanguageMapper(self.record, self.resourceURI, self.representationURI).mapData()
    if languages:
      [self.results.append(language) for language in languages]
    
    # ISSN links
    issnLinks = ISSNMapper(self.record).mapData()
    if issnLinks:
      [self.results.append(issnLink) for issnLink in issnLinks]
      
    # Online version of the journal
    onlineVersion = self.record.getXPath('//varfield[@id="856"][@i1="4"]/subfield[@label="u"]')
    if not onlineVersion == []:
      onlineVersion = onlineVersion[0]
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dcterms"]["hasVersion"],
        rdflib.URIRef(onlineVersion)
      ))
      # Validate onlineVersion URI? bibo:uri datatype property?
      
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
    self.pshTranslateDict = {}
  
  def insertSKOSRelations(self, terms, predicate):
    if not terms == []:
      for term in terms:
        try:
          termTranslated = self.pshTranslateDict[term]
          self.results.append((
            self.resourceURI,
            rdflibWrapper.namespaces["skos"][predicate]
            rdflib.URIRef(termTranslated)
          ))
        except KeyError:
          report("[ERROR] term %s doesn't have a translation." % (term))
  
  def main(self):
    # Write URIs & identifiers
    self.getIdentifiers("issn")
    
    # Last modified date
    self.getLastModifiedDate()   
      
    # Sigla of the creator    
    sigla = SiglaMapper(self.record, self.resourceURI, self.representationURI).mapData()
    if sigla:
      self.results.append(sigla[0])
    
    marcARecord = MarcARecord(self.record)
    if marcARecord.isPSH():
      # Preferred label in Czech
      prefLabelCS = marcARecord.getPrefLabelCS()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["skos"]["prefLabel"],
        rdflib.Literal(prefLabelCS, lang="cs")
      ))
      
      # Preferred label in English
      prefLabelEN = marcARecord.getPrefLabelEN()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["skos"]["prefLabel"],
        rdflib.Literal(prefLabelEN, lang="en")
      ))
    
      # Non-preferred labels in Czech
      nonprefLabelsCS = marcARecord.getNonprefLabelsCS()
      for nonprefLabelCS in nonprefLabelsCS:
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["skos"]["altLabel"],
          rdflib.Literal(nonprefLabelCS, lang="cs")
        ))
        
      # Non-preferred labels in English
      nonprefLabelsEN = marcARecord.getNonprefLabelsEN()
      for nonprefLabelEN in nonprefLabelsEN:
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["skos"]["altLabel"],
          rdflib.Literal(nonprefLabelEN, lang="en")
        ))
        
      # Pro následující je zapotřebí dodělat překlad prefLabel => ID (resp. URI), jako externí tabulku/CSV/SQLite bázi?
      file = open("pshTranslateTable.csv", "r")
      pshTranslateTable = file.read()
      file.close()
      pshTranslateTable = pshTranslateTable.split("\n")
      for pshTranslateLine in pshTranslateTable:
        line = pshTranslateLine.split(";")
        self.pshTranslateDict[line[0]] = line[1]
        
      # Related terms
      relatedTerms = marcARecord.getRelatedTerms()
      self.insertSKOSRelations(relatedTerms, "related")
      
      # Narrower terms
      narrowerTerms = marcARecord.getNarrowerTerms()
      self.insertSKOSRelations(narrowerTerms, "narrower")
      
      # Broader terms
      broaderTerms = marcARecord.getBroaderTerms()
      self.insertSKOSRelations(broaderTerms, "broader")
    
  def addStaticTriplesBase(self):
    triples = [(
      self.resourceURI,
      rdflibWrapper.namespaces["rdf"]["type"],
      rdflibWrapper.namespaces["skos"]["Concept"]
    )]
    self.addTriples(triples)


class STK01Callback(Callback):
  
  def __init__(self, baseName="STK01"):
    Callback.__init__(self)
    
  def main(self):
    self.getIdentifiers("bib")
    self.getLastModifiedDate()
    
    # Mapping the fixfield 008
    self.getDataFromFixfield008()
    
    # KPWin sysno
    kpwSysno = self.record.getXPath('//fixfield[@id="KPW"]')
    if not kpwSysno == []:
      kpwSysno = kpwSysno[0]
      self.results.append((
        self.representationURI,
        rdflibWrapper.namespaces["dc"]["identifier"],
        rdflib.Literal(kpwSysno)
      ))

    # Date
    self.getPublicationDate()
    
    # Publisher      
    self.getPublisher()    
      
    # Main title
    mainTitle = self.record.getXPath('//varfield[@id="245"]/subfield[@label="a"]')
    if not mainTitle == []:
      mainTitle = mainTitle[0].strip().rstrip("/").rstrip("=").rstrip(":").rstrip(".").rstrip(";").rstrip() # A few attemps to clean dirty data
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["title"],
        rdflib.Literal(mainTitle)
      ))
      
    # Main author entry
    mainAuthor = self.record.getXPath('//varfield[@id="100"][@i1="1"]/subfield[@label="a"]')
    if not mainAuthor == []:
      mainAuthor = mainAuthor[0].strip().rstrip(",")
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["creator"],
        rdflib.Literal(mainAuthor)
      ))
    
    # VIAF main author mapper
    viafAuthor = AuthorMapper(self.record, self.resourceURI, self.representationURI).mapData("main")
    if viafAuthor:
      self.results.append(viafAuthor[0])
      
    # Universal Decimal Classification
    self.getUDC()
    
    # Number of pages
    physicalDescription = self.record.getXPath('//varfield[@id="300"]/subfield[@label="a"]')
    if not physicalDescription == []:
      physicalDescription = physicalDescription[0]
      noPages = re.search("(\d+)(?=\ss.)", physicalDescription) # An empty attempt to parse evil physical description string
      if noPages:
        noPages = int(noPages.group(1))
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["bibo"]["numPages"],
          rdflib.Literal(noPages)
        ))
        
    # ISBN
    isbn = self.record.getXPath('//varfield[@id="020"]/subfield[@label="a"]')
    if not isbn == []:
      isbn = isbn[0]
      isbn = re.search("([\dX-]+)(?=\s?)", isbn)
      if isbn:
        isbn = isbn.group(1).strip()
        predicateDict = {
          10 : rdflibWrapper.namespace["bibo"]["isbn10"],
          13 : rdflibWrapper.namespace["bibo"]["isbn13"]
        }
        isbnLength = isbn.strip("-")
        try:
          predicate = predicateDict[isbnLength]
        except KeyError:
          predicate = rdflibWrapper.namespaces["bibo"]["isbn"]
          
        self.results.append((
          self.resourceURI,
          predicate,
          rdflib.Literal(isbn)
        ))      
    
    # Document form
    fmt = self.record.getXPath('//fixfield[@id="FMT"]')
    if not fmt == []:
      fmt = fmt[0]
      fmtDict = {
        "BK" : rdflibWrapper.namespace["bibo"]["Book"],
        "DS" : rdflibWrapper.namespace["bibo"]["Thesis"],
        # "ER" : "elektronic resource",
        "HF" : rdflibWrapper.namespace["yago"]["HistoricalDocument"],
        "RS" : rdflibWrapper.namespace["bibo"]["Article"],
        "SE" : rdflibWrapper.namespace["bibo"]["Journal"],
      }
      try:
        documentForm = fmtDict[fmt]
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespace["rdf"]["type"],
          documentForm
        ))
      except KeyError:
        # FMT string not found
        
    # Call number
    callNumber = self.record.getXPath('//varfield[@id="990"]/subfield[@label="g"]')
    if not callNumber == []:
      callNumber = callNumber[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["bibo"]["locator"],
        rdflib.Literal(callNumber)
      ))
      
    # Edition statement
    editionStatement = self.record.getXPath('//varfield[@id="250"]/subfield[@label="a"]')
    if not editionStatement == []:
      editionStatement = editionStatement[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dbpedia"]["numberEdition"]
        rdflib.Literal(editionStatement)
      ))
      
    # Note
    note = self.record.getXPath('//varfield[@id="500"]/subfield[@label="a"]')
    if not note == []:
      note = note[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespace["dc"]["description"],
        rdflib.Literal(note, lang="cs")
      ))
      
    # Added name entry
    addedNameEntries = self.record.getXPath('//varfield[@id="700"][@i1="1"]/subfield[@label="a"]')
    if not addedNameEntries == []:
      for addedNameEntry in addedNameEntries:
        addedNameEntry = addedNameEntry[0].strip().rstrip(",")
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["contributor"],
          rdflib.Literal(addedNameEntry)
        ))
    
    # VIAF added author mapper
    viafAuthor = AuthorMapper(self.record, self.resourceURI, self.representationURI).mapData("added")
    if viafAuthor:
      self.addTriples(viafAuthor)
      
    # Library of Congress Classification
    lccs = self.record.getXPath('//varfield[@id="LCC"]/subfield[@label="a"] | //varfield[@id="050"]/subfield[@label="a"]')
    if not lccs == []:
      for lcc in lccs:
        bnodeID = rdflib.BNode()
        lcc = lcc.strip()
        self.addTriples([(
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["subject"],
          bnodeID
        ), (
          bnodeID,
          rdflibWrapper.namespaces["rdf"]["value"],
          rdflib.Literal(lcc)
        ), (
          bnodeID,
          rdflibWrapper.namespaces["dcam"]["memberOf"],
          rdflibWrapper.namespaces["dcterms"]["LCC"]
        )])
    
    # Bibliography note
    bibliographyNote = self.record.getXPath('//varfield[@id="504"]/subfield[@label="a"]')
    if not bibliographyNote == []:
      bnodeID = rdflib.BNode()
      bibliographyNote = bibliographyNote[0].strip()
      self.addTriples([(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["description"],
        bnodeID
      ), (
        bnodeID,
        rdflibWrapper.namespaces["rdf"]["type"],
        rdflibWrapper.namespaces["yago"]["Bibliography"]
      ), (
        bnodeID,
        rdflibWrapper.namespaces["rdf"]["value"],
        rdflib.Literal(bibliographyNote, lang="cs")
      )])
      
    # Edition
    editions = self.record.getXPath('//varfield[@id="490"]/subfield[@label="a"]')
    if not editions == []:
      for edition in editions:
        edition = edition.strip()
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["bibo"]["edition"],
          rdflib.Literal(edition)
        ))
        
  def addStaticTriplesBase(self):
    triples = [(
      self.representationURI,
      rdflibWrapper.namespaces["rdf"]["type"],
      rdflibWrapper.namespaces["dcterms"]["BibliographicResource"]
    )]
    self.addTriples(triples)
