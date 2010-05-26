#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
from Mapper import *
import rdflib
import rdflibWrapper
from report import report


class Callback():
  
  def __init__(self, baseName):
    self.results = [] # (subject, predicate, object)
    self.unmapped = [] # (XPath, value)
    self.baseName = baseName
    self.resourceURI = "" # URI for the resource
    self.representationURI = "" # URI for the representation
    self.pshTranslateDict = {} # Dict for translating PSH preferred labels to IDs
    
    # PSH translate table
    report("INFO: Initializing PSH translate table.")
    file = open("pshTranslateTable.csv", "r")
    pshTranslateTable = file.read()
    file.close()
    pshTranslateTable = pshTranslateTable.split("\n")
    for pshTranslateLine in pshTranslateTable:
      line = pshTranslateLine.split(";")
      self.pshTranslateDict[line[0]] = line[1]
    
  def commitData(self):
    """Saves self.results into RDFLib."""
    report("INFO: commiting data.")
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
    report("INFO: getting identifiers for %s" % (uriBase))
    sysno = self.record.getXPath("//fixfield[@id='001']")[0]
    report("INFO: got sysno %s" % (sysno))
    subject = re.search("\d+$", sysno).group(0).lstrip("0")
    subject = "http://data.techlib.cz/resource/%s/%s" % (uriBase, subject)
    report("INFO: got subject URI %s" % (subject))
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
    report("INFO: getDataFromFixfield008 method")
    report("INFO: \n\t resource URI %s,\n\t representation URI %s,\n\t record %s" % (self.resourceURI, self.representationURI, self.record))
    mapper = Fixfield008Mapper(self.record, self.resourceURI, self.representationURI)
    report("INFO: Fixfield008Mapper.mapData()")
    fixfield008Results = mapper.mapData()
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
    report("INFO: getting publisher")
    publishers = self.record.getXPath('//varfield[@id="260"]/subfield[@label="b"] | //varfield[@id="720"][@i1="2"]/subfield[@label="a"]')
    if not publishers == []:
      for publisher in publishers:
        report("INFO: publisher %s" % (publisher))
        publisher = publisher.strip().rstrip(",").rstrip(";").rstrip(":").rstrip()
        report("INFO: stripped publisher %s" % (publisher))
        self.addTriples([(
          self.resourceURI, 
          rdflibWrapper.namespaces["dc"]["publisher"],
          rdflib.Literal(publisher)
        )])
    placeOfPublication = self.record.getXPath('//varfield[@id="260"]/subfield[@label="a"]')
    if not placeOfPublication == []:
      placeOfPublication = placeOfPublication[0].strip(":").strip(";").strip()
      bnodeID = rdflib.BNode()
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
      report("INFO: UDC %s" % (udc))
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
      )
    ]
    self.addTriples(triples)
    
  def addStaticTriplesBase(self):
    """Method for adding triples that are stable for the specific database. Must be overwritten by a child class."""
    pass
    
  def run(self, record):
    """Runs the callback."""
    report("INFO: running the callback")
    self.record = record
    report("INFO: callback main extraction")
    self.main()
    report("INFO: callback adding global static triples")
    self.addStaticTriplesGlobal()
    report("INFO: callback adding base static triples")
    self.addStaticTriplesBase()
    # report("INFO: callback writing unmapped")
    # self.writeUnmapped()
    if len(self.results) > 1000:
      report("INFO: callback flushing the cache")
      self.commitData()
  
  
class STK02Callback(Callback):
  
  def __init__(self, baseName="STK02"):
    Callback.__init__(self, baseName)
    
  def main(self):
    report("INFO: STK02 callback main method.")
    
    # Write URIs & identifiers
    report("INFO: STK02 getting identifiers")
    self.getIdentifiers("issn")
    
    # Mapping the fixfield 008
    report("INFO: STK02 mapping the fixfield 008")
    self.getDataFromFixfield008()
      
    # Last modified date
    report("INFO: STK02 getting the last modified date")
    self.getLastModifiedDate()   
    
    # Short title
    report("INFO: STK02 getting the short title")
    shortTitle = self.record.getXPath('//varfield[@id="210"][@i1="1"]/subfield[@label="a"]')
    if not shortTitle == []:
      shortTitle = shortTitle[0]
      report("INFO: short title is %s" % (shortTitle))
      self.results.append((
        self.resourceURI, 
        rdflibWrapper.namespaces["bibo"]["shortTitle"],
        rdflib.Literal(shortTitle)
      ))
    
    # Universal Decimal Classification
    report("INFO: STK02 getting the UDC")
    self.getUDC()
    
    # Publisher
    report("INFO: STK02 getting the publisher")    
    self.getPublisher()

    # Place of publication
    report("INFO: STK02 getting the place of publication")
    publicationPlace = self.record.getXPath('//varfield[@id="260"]/subfield[@label="a"]')
    if not publicationPlace == []:
      publicationPlace = publicationPlace[0]
      # Dodělat:
      #   - predikát?
      #   - zdali to nevypovídá spíše o vydavateli?
      # self.results.append((self.resourceURI, "", publicationPlace))
      
    # ISSN
    report("INFO: STK02 getting the ISSNs")
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
    report("INFO: STK02 getting the date")
    self.getPublicationDate()
    
    # Titles
    report("INFO: STK02 getting the titles")
    titles = self.record.getXPath('//varfield[@id="222"][@i2="0"]/subfield[@label="a"] | //varfield[@id="245"][@i1="1"]/subfield[@label="a"] | //varfield[@id="246"]/subfield[@label="a"]')
    if not titles == []:
      for title in titles:
        title = title.strip().rstrip(".")
        report("INFO: title %s" % (title))
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["title"],
          rdflib.Literal(title)
        ))
      
    # Language
    report("INFO: STK02 getting the language")
    languages = LanguageMapper(self.record, self.resourceURI, self.representationURI).mapData()
    if languages:
      [self.results.append(language) for language in languages]
    
    # ISSN links
    report("INFO: STK02 getting the ISSN")
    issnLinks = ISSNMapper(self.record, self.resourceURI, self.representationURI).mapData()
    if issnLinks:
      [self.results.append(issnLink) for issnLink in issnLinks]
      
    # Online version of the journal
    report("INFO: STK02 getting the online version URL")
    onlineVersion = self.record.getXPath('//varfield[@id="856"][@i1="4"]/subfield[@label="u"]')
    if not onlineVersion == []:
      onlineVersion = onlineVersion[0]
      report("INFO: journal has online version at %s" % (onlineVersion))
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dcterms"]["hasVersion"],
        rdflib.URIRef(onlineVersion)
      ))
      # Validate onlineVersion URI? bibo:uri datatype property?
      
  def addStaticTriplesBase(self):
    report("INFO: STK02 adding static triples")
    triples = [(
      self.resourceURI,
      rdflibWrapper.namespaces["rdf"]["type"], 
      rdflibWrapper.namespaces["bibo"]["Periodical"]
    ),]
    self.addTriples(triples)
    
    
class STK10Callback(Callback):
  
  def __init__(self, baseName="STK10"):
    Callback.__init__(self, baseName)
  
  def insertSKOSRelations(self, terms, predicate):
    if not terms == []:
      for term in terms:
        try:
          termTranslated = self.pshTranslateDict[term]
          self.results.append((
            self.resourceURI,
            rdflibWrapper.namespaces["skos"][predicate],
            rdflib.URIRef(termTranslated)
          ))
        except KeyError:
          report("[ERROR] term %s doesn't have a translation." % (term))
  
  def main(self):
    # Write URIs & identifiers
    self.getIdentifiers("psh")
    
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
    Callback.__init__(self, baseName)
    
  def main(self):
    report("INFO: beginning STK01 callback")
    self.getIdentifiers("bib")
    self.getLastModifiedDate()
    
    # Mapping the fixfield 008
    report("INFO: STK01 mapping the fixfield 008")
    self.getDataFromFixfield008()
    
    # KPWin sysno
    report("INFO: STK01 getting KPWin sysno")
    kpwSysno = self.record.getXPath('//fixfield[@id="KPW"]')
    if not kpwSysno == []:
      kpwSysno = kpwSysno[0]
      self.results.append((
        self.representationURI,
        rdflibWrapper.namespaces["dc"]["identifier"],
        rdflib.Literal(kpwSysno)
      ))

    # Date
    report("INFO: STK01 getting publication date")
    self.getPublicationDate()
    
    # Publisher
    report("INFO: STK01 getting publisher")
    self.getPublisher()    
      
    # Main title
    report("INFO: STK01 getting main title")
    mainTitle = self.record.getXPath('//varfield[@id="245"]/subfield[@label="a"]')
    if not mainTitle == []:
      mainTitle = mainTitle[0].strip().rstrip("/").rstrip("=").rstrip(":").rstrip(".").rstrip(";").rstrip() # A few attemps to clean dirty data
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["title"],
        rdflib.Literal(mainTitle)
      ))
      
    # Main author entry
    report("INFO: STK01 getting main author entry")
    mainAuthor = self.record.getXPath('//varfield[@id="100"][@i1="1"]/subfield[@label="a"]')
    if not mainAuthor == []:
      mainAuthor = mainAuthor[0].strip().rstrip(",")
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["creator"],
        rdflib.Literal(mainAuthor)
      ))
    
    # VIAF main author mapper
    report("INFO: STK01 beginning VIAF author mapper")
    viafAuthor = AuthorMapper(self.record, self.resourceURI, self.representationURI).mapData("main")
    if viafAuthor:
      self.results.append(viafAuthor[0])
      
    # Universal Decimal Classification
    report("INFO: STK01 getting UDC")
    self.getUDC()
    
    # Number of pages
    report("INFO: STK01 getting number of pages")
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
    report("INFO: STK01 getting ISBN")
    isbn = self.record.getXPath('//varfield[@id="020"]/subfield[@label="a"]')
    if not isbn == []:
      isbn = isbn[0]
      report("INFO: found ISBN %s" % (isbn))
      isbn = re.search("([\dX-]+)(?=\s?)", isbn)
      if isbn:
        isbn = isbn.group(1).strip()
        report("INFO: stripped ISBN %s" % (isbn))
        predicateDict = {
          10 : rdflibWrapper.namespaces["bibo"]["isbn10"],
          13 : rdflibWrapper.namespaces["bibo"]["isbn13"]
        }
        isbnLength = len(isbn.strip("-"))
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
    report("INFO: STK01 getting document form")
    fmt = self.record.getXPath('//fixfield[@id="FMT"]')
    if not fmt == []:
      fmt = fmt[0]
      fmtDict = {
        "BK" : rdflibWrapper.namespaces["bibo"]["Book"],
        "DS" : rdflibWrapper.namespaces["bibo"]["Thesis"],
        # "ER" : "elektronic resource",
        "HF" : rdflibWrapper.namespaces["yago"]["HistoricalDocument"],
        "RS" : rdflibWrapper.namespaces["bibo"]["Article"],
        "SE" : rdflibWrapper.namespaces["bibo"]["Journal"],
      }
      try:
        documentForm = fmtDict[fmt]
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["rdf"]["type"],
          documentForm
        ))
      except KeyError:
        # FMT string not found
        report("FMT string not found")
      
    # Call number
    report("INFO: STK01 getting call number")
    callNumber = self.record.getXPath('//varfield[@id="990"]/subfield[@label="g"]')
    if not callNumber == []:
      callNumber = callNumber[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["bibo"]["locator"],
        rdflib.Literal(callNumber)
      ))
      
    # Edition statement
    report("INFO: STK01 getting edition statement")
    editionStatement = self.record.getXPath('//varfield[@id="250"]/subfield[@label="a"]')
    if not editionStatement == []:
      editionStatement = editionStatement[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["bibo"]["number"],
        rdflib.Literal(editionStatement)
      ))
      
    # Note
    report("INFO: STK01 getting note")
    notes = self.record.getXPath('//varfield[@id="500" or @id="502"]/subfield[@label="a"]')
    if not notes == []:
      for note in notes:
        note = note.strip()
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["description"],
          rdflib.Literal(note, lang="cs")
        ))
      
    # Added name entry
    report("INFO: STK01 getting added name entry")
    addedNameEntries = self.record.getXPath('//varfield[@id="700"][@i1="1"]/subfield[@label="a"]')
    if not addedNameEntries == []:
      for addedNameEntry in addedNameEntries:
        addedNameEntry = addedNameEntry.strip().rstrip(",")
        report("INFO: STK01 got added name entry %s" % (addedNameEntry))
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["contributor"],
          rdflib.Literal(addedNameEntry)
        ))
    
    # VIAF added author mapper
    report("INFO: STK01 getting VIAF for added author entry")
    viafAuthor = AuthorMapper(self.record, self.resourceURI, self.representationURI).mapData("added")
    if viafAuthor:
      self.addTriples(viafAuthor)
      
    # Library of Congress Classification
    report("INFO: STK01 getting LCC")
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
    report("INFO: STK01 getting bibliography note")
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
    report("INFO: STK01 getting edition")
    editions = self.record.getXPath('//varfield[@id="490"]/subfield[@label="a"]')
    if not editions == []:
      for edition in editions:
        edition = edition.strip()
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["bibo"]["edition"],
          rdflib.Literal(edition)
        ))
    
    # Contributors
    report("INFO: STK01 getting contributors")
    contributors = self.record.getXPath('//varfield[@id="245"]/subfield[@label="c"]')
    if not contributors == []:
     contributors = contributors[0].strip().strip("by").strip().rstrip(".").replace("  ", " ").split(", ") # Vain attempt to clean the data.
     for contributor in contributors:
       self.results.append((
         self.resourceURI,
         rdflibWrapper.namespaces["dc"]["contributor"],
         rdflib.Literal(contributor)
       ))
      
    # Alternate title
    report("INFO: STK01 getting alternate title")
    alternateTitle = self.record.getXPath('//varfield[@id="246"][@i1="3"][@i2="0"]/subfield[@label="a"]')
    if not alternateTitle == []:
      alternateTitle = alternateTitle[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dbpedia"]["alternateTitle"],
        rdflib.Literal(alternateTitle)
      ))
    
    # PSH subject term
    report("INFO: STK01 getting PSH subject terms")
    pshTerms = self.record.getXPath('//varfield[@id="650"][@i1="0"][@i2="7"]/subfield[@label="a"]')
    if not pshTerms == []:
      for pshTerm in pshTerms:
        pshTerm = pshTerm.strip()
        report("INFO: got PSH %s" % (pshTerm))
        try:
          pshURI = self.pshTranslateDict[pshTerm]
        except KeyError:
          report("ERROR: cannot find the translation for PSH %s" % (pshTerm))
          raise SystemExit
          
        self.results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["subject"],
          rdflib.URIRef(pshURI)
        ))
    
    # Sequence number in edition
    report("INFO: STK01 getting sequence number in edition")
    editionNumber = self.record.getXPath('//varfield[@id="490"]/subfield[@label="v"]')
    if not editionNumber == []:
      editionNumber = editionNumber[0].strip()
      self.results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["dbpedia"]["numberEdition"],
        rdflib.Literal(editionNumber)
      ))
    
    # Added entry - corporation
    report("INFO: STK01 getting added entry for corporation")
    corporationAddedEntry = self.record.getXPath('//varfield[@id="710"]/subfield[@label="a"]')
    if not corporationAddedEntry == []:
      corporationAddedEntry = corporationAddedEntry[0].strip()
      bnodeID = rdflib.BNode()
      self.addTriples([(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["creator"],
        bnodeID
      ), (
        bnodeID,
        rdflibWrapper.namespaces["rdf"]["value"],
        rdflib.Literal(corporationAddedEntry)
      ), (
        bnodeID,
        rdflibWrapper.namespaces["rdf"]["type"],
        rdflibWrapper.namespaces["yago"]["Corporation"]
      )]) 
          
  def addStaticTriplesBase(self):
    triples = [(
      self.representationURI,
      rdflibWrapper.namespaces["rdf"]["type"],
      rdflibWrapper.namespaces["dcterms"]["BibliographicResource"]
    )]
    self.addTriples(triples)
