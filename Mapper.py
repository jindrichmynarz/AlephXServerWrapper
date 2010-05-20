#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib, urllib2, libxml2, re, time, string, rdflib, unicodedata
from alephXServerWrapper import *
import rdflibWrapper

class Mapper():
  """Obecná třída pro mapování hodnot."""
  
  def __init__(self, doc, resourceURI, representationURI):
    """Na vstupu bere 1 argument - instanci třídy alephXServerWrapper.Record."""
    self.doc = doc # Na vstupu bere celý XML záznam (class Record)
    self.resourceURI = resourceURI
    self.representationURI = representationURI
    
  def mapData(self):
    """Vrací pole s tuples s predikáty a jejich objekty, subjektem je vždy zpracováváný dokument.
    Tuto metodu každá podtřída přepisuje."""
    return [(self.resourceURI, "predikát 1", "objekt 1"), (self.representationURI, "predikát 2", "objekt 2")]
   
  def getParsedDoc(self, url):
    """Na zadané URL nebo urllib2.Request vrátí naparsovaný XML dokument.""" 
    result = urllib2.urlopen(url)
    doc = result.read()
    result.close()
    doc = Record(libxml2.parseDoc(doc))
    return doc
     
  def validateURI(self, uri):
    """Zjišťuje, zdali je zadané URI dostupné."""
    try:
      urllib2.urlopen(uri)
      return True
    except urllib2.HTTPError:
      return False
      
  def searchAlephBase(self, baseUrl, baseCode, findCode, request):
    """Searches the Aleph X Services (running on baseUrl) with specified database code for the request, within the find code and returns the result."""
    url = "%s/X?op=find&base=%s&code=%s&request=%s" % (baseUrl, baseCode, findCode, urllib.quote(request.strip()))
    doc = self.getParsedDoc(url)
    error = doc.getXPath("find/error")
    if error == []:
      noRecords = doc.xpathEval("find/no_records")[0]
      setNumber = doc.xpathEval("find/set_number")[0]
      url = "%sX?op=present&base=%s&set_entry=1-%s&set_number=%s" % (baseUrl, baseCode, noRecords.lstrip("0"), setNumber)
      doc = self.getParsedDoc(url)
      return doc
    else:
      return False
      
  def stripAccents(self, string):
    """
      <http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string>
    """
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

class DCTypeMapper(Mapper):
  """Mapování typu dokumentu na DCMI Types, resp. typy z dalších ontologií (BIBO, YAGO)."""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    returnValue = None
    position6 = self.doc.getXPath("substring(//fixfield[@id='LDR'], 6, 1)")
    position7 = self.doc.getXPath("substring(//fixfield[@id='LDR'], 7, 1)")
    
    if position6 in ["a"]:
      return [(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["type"],
        rdflibWrapper.namespaces["dctype"]["Text"]
      )]
    if position6 in ["c"]:
      return [(
        self.resourceURI,
        rdflifWrapper.namespaces["dc"]["type"],
        rdflibWrapper.namespaces["yago"]["SheetMusic"]
      )]
    if position6 in ["d"]:
      return [(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["type"], 
        rdflibWrapper.namespaces["yago"]["SheetMusic"]
      ), (
        self.resourceURI,
        rdflibWrapper.namespaces["dc:type"],
        rdflibWrapper.namespaces["yago:Manuscript"]
      )]
    if position6 in ["e", "f", "g", "k"]:
      return [(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["type"],
        rdflibWrapper.namespaces["dctype"]["Image"]
      )]
    if position6 in ["i", "j"]:
      return [(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["type"], 
        rdflibWrapper.namespaces["dctype"]["Sound"]
      )]
    if position6 in ["p"] and position7 in ["c", "s"]:
      return [(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["type"], 
        rdflibWrapper.namespaces["dctype"]["Collection"]
      )]
    if position6 in ["t"]:
      return [(
        self.resourceURI,
        rdflibWrapper.namespaces["dc"]["type"],
        rdflibWrapper.namespaces["bibo"]["Manuscript"]
      )]
    
    
class LanguageMapper(Mapper):
  """Mapování na kódy jazyků."""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
  
  def mapData(self):
    # Získání language codes
    languageCodes = []
    
    extract = self.doc.getXPath("substring(//fixfield[@id='008'], 36, 3)")
    languageCodes.append(extract[0])
    
    extract = self.doc.getXPath("//varfield[@id='040']/subfield[@label='b']")
    if not extract == []:
      languageCodes.append(extract[0])
      
    extract = self.doc.doc.xpathEval("//varfield[@id='041']/subfield")
    if not extract == []:
      for subfield in extract:
        if subfield.noNsProp("label") in ["a", "b", "c", "d", "e", "f", "g", "h", "j"]:
          languageCodes.append(subfield.content)
        
    extract = self.doc.getXPath("//varfield[@id='242']/subfield[@label='y']")
    if not extract == []:
      languageCodes.append(extract[0])
      
    extract = self.doc.getXPath("//varfield[@id='775']/subfield[@label='e']")
    if not extract == []:
      languageCodes.append(extract[0])
      
    # Deduplikace language codes
    languageCodes = list(set(languageCodes))
    
    # Validace language codes
    validLanguageCodes = []
    for languageCode in languageCodes:
      # MARCCodes
      uri = "http://purl.org/NET/marccodes/languages/%s" % (languageCode)
      valid = self.validateURI(uri)
      if valid:
        validLanguageCodes.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["language"],
          rdflib.URIRef(uri)
        ))
      
      # Lexvo
      uri = "http://www.lexvo.org/id/iso639-3/%s" % (languageCode)
      valid = self.validateURI(uri)
      if valid:
        validLanguageCodes.append((
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["language"],
          rdflib.URIRef(uri)
        ))
    
    if not validLanguageCodes == []:
      return validLanguageCodes
    else:      
      return False


class CountryMapper(Mapper):
  """Mapování na kódy států."""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    self.results = []
    
  def mapData(self):    
    # Získání country codes
    countryCodes = []

    # ODLIŠIT, na koho se country codes vztahují!!!
    extract = self.doc.getXPath("substring(//fixfield[@id='008'], 16, 3)").rstrip("-") # <self.resourceURI> dc:publisher [dbpedia:locatedIn <URI_country> . ] .
    countryCodes.append(extract)

    extract = self.doc.getXPath("//fixfield[@id='044']/subfield[@label='a']") # <self.representationURI> dc:creator [dbpedia:locatedIn <URI_country> . ] .
    if not extract == []:
      countryCodes.append(extract[0])

    extract = self.doc.getXPath("//fixfield[@id='535']/subfield[@label='g']")
    if not extract == []:
      countryCodes.append(extract[0])
    
    extract = self.doc.getXPath("//fixfield[@id='775']/subfield[@label='f']")
    if not extract == []:
      countryCodes.append(extract[0])  
      
    extract = self.doc.getXPath("//fixfield[@id='851']/subfield[@label='g']")
    if not extract == []:
      countryCodes.append(extract[0])
    
    # Deduplikace country codes
    countryCodes = list(set(countryCodes))
    
    # Validace country codes pomocí try/except a http error
    validCountryCodes = []
    for countryCode in countryCodes:
      uri = "http://purl.org/NET/marccodes/countries/%s" % (validCountryCode)
      valid = self.validateURI(uri)
      if valid:
        uri += "#location"
        validCountryCodes.append((
          self.representationURI,
          rdflibWrapper.namespaces["dbpedia"]["locatedIn"],
          rdflib.URIRef(uri)
        ))
    
    if not validCountryCodes == []:
      return validCountryCodes
    else:
      return False

  def mapExtractedValues(self, predicate, code):
    uri = validateCode(code)
    if uri:
      self.results.append((
        predicate,
        rdflib.URIRef(uri)
      ))
    
  def validateCode(self, code):
    uri = "http://purl.org/NET/marccodes/countries/%s" % (validCountryCode)
    valid = self.validateURI(uri)
    if valid:
      return uri
    else:
      return False
    
       
class GeographicAreaMapper(Mapper):
  """Mapování geografických oblastí na MARC Codes"""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    geographyAreaCode = self.doc.getXPath("//varfield[@id='043']/subfield[@label='a']")
    if not geographyAreaCode == []:
      uri = "http://purl.org/NET/marccodes/gacs/%s#location" % (geographyAreaCode[0])
      valid = self.validateURI(uri)
      if valid:
        return [(
          self.resourceURI,
          rdflibWrapper.namespaces["dc"]["coverage"],
          rdflib.URIRef(uri)
        )]
      else:
        return False
    else:
      return False
        

class PSHMapper(Mapper):
  """Mapování z preferovaných hesel PSH v bibliografických záznamech na URI těchto hesel"""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    pshTerms = self.doc.getXPath("//varfield[@id='650']/subfield[@label='a']")
    if not pshTerms == []:
      for pshTerm in pshTerms:
        # Dodělat: RDFLib dotaz na skos:prefLabel[@xml:lang='cs']
        pass
        
      
class AuthorMapper(Mapper):
  """Mapování jmen autorů z bibliografických záznamů na záznamy autoritní na VIAF.org"""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self, authorType):
    # authorType = {"main" | "added"}
    if authorType == "main":
      xpath = "//varfield[@id='100']/subfield[@label='a']"
      predicate = rdflibWrapper.namespaces["dc"]["creator"]
    elif author == "added":
      xpath = "//varfield[@id='700']/subfield[@label='a']"
      predicate = rdflibWrapper.namespaces["dc"]["contributor"]
    else:
      raise ValueError("AuthorMapper.mapData: not acceptable authorType argument.")
      
    authors = self.doc.getXPath(xpath)
    if not authors == []:
      for author in authors:
        author = author.strip().rstrip(",").strip()
        author = "\"%s\"" % (urllib.quote(author))
        searchResults = self.searchAlephBase("http://aleph.techlib.cz", "STK11", "WAU", request)
        if searchResults:
          authorName = searchResults.getXPath("present/record/metadata/oai_marc[fixfield[@id='FMT']='JA']/varfield[@id='100']/subfield[@label='a']")
          authorCode = searchResults.getXPath("present/record/metadata/oai_marc[fixfield[@id='FMT']='JA']/varfield[@id='100']/subfield[@label='9']")
          if (not authorName == []) and (not authorCode == []):
            authorName = self.stripAccents(authorName[0]).strip().rstrip(",").strip()
            authorCode = authorCode[0].strip()
            
            headers = {"Accept" : "application/rdf+xml"}
            url = """http://viaf.org/search?query=local.mainHeadingEl+=+%22""" + authorCode + """%22&version=1.1&operation=searchRetrieve"""
            
            req = urllib2.Request(url, None, headers)
            doc = self.getParsedDoc(req)
            docContext = doc.xpathNewContext()
            docContext.xpathRegisterNs("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
            docContext.xpathRegisterNs("skos", "http://www.w3.org/2004/02/skos/core#")
            docContext.xpathRegisterNs("foaf", "http://xmlns.com/foaf/0.1/")
            
            foafName = docContext.xpathEval("//foaf:name")
            foafName = self.stripAccents(foafName[0].content)
            
            # Kontrola podle jména autora
            if foafName in authorName or authorName in foafName:
              conceptId = docContext.xpathEval("//skos:Concept/@rdf:about")
              match = re.match(".*(?=\.)", conceptId[0].content) # Odstraní příponu typu souboru
              conceptId = match.group()
              conceptURI = "http://viaf.org/" + conceptId
              
              return [(
                self.resourceURI,
                predicate,
                rdflib.URIRef(conceptURI)
              )]
            else:
              return False
          else:
            return False
        else:
          return False
    else:
      return False


class DBPediaMapper(Mapper):
  """Mapování na zdroje v DBPedii."""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    # Extract English preferred and non-preferred headings
    record = MarcARecord(self.doc)
    prefLabel = record.getPrefLabelEN()
    altLabels = record.getNonprefLabelsEN()
    baseurl = "http://lookup.dbpedia.org/api/search.asmx/KeywordSearch?QueryClass=&MaxHits=1&QueryString="

    results = []
    # Mapování preferovaného znění hesla
    url = baseurl + urllib.quote(prefLabel)
    doc = self.getParsedDoc(url)
    match = self.checkMatch(prefLabel, doc)
    if match:
      results.append((
        self.resourceURI,
        rdflibWrapper.namespaces["skos"]["exactMatch"],
        rdflib.URIRef(match)
      ))
    
    # Mapování nepreferovaného znění hesla
    for altLabel in altLabels:
      url = baseurl + urllib.quote(altLabel)
      doc = self.getParsedDoc(url)
      match = self.checkMatch(altLabel, doc)
      if match:
        results.append((
          self.resourceURI,
          rdflibWrapper.namespaces["skos"]["closeMatch"],
          rdflib.URIRef(match)
        ))

    if not results == []:
      return results
    else:
      return False
    
  def checkMatch(self, label, doc):
    # This style of XPath queries must be used because 
    # the default XML namespace is specified.
    labels = doc.xpathEval("//*[name()='Label']")
    if label == labels[0].content.lower():
      uris = doc.xpathEval("//*[name()='URI']")
      return uris[0]
    else:
      return False


class LCSHMapper(Mapper):

  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    record = MarcARecord(self.doc)
    prefLabel = record.getPrefLabelEN()
    altLabels = record.getNonprefLabelsEN()
    
    results = []
    
    resultPrefLabel = self.getUrlForMatchingLabel(self.getSearchResults(prefLabel), prefLabel)
    if resultPrefLabel:
      result.append((
        self.resourceURI,
        rdflibWrapper.namespaces["skos"]["exactMatch"],
        rdflib.URIRef(resultPrefLabel)
      ))
    
    for altLabel in altLabels:
      resultAltLabel = self.getUrlForMatchingLabel(self.getSearchResults(altLabel), altLabel)
      if resultAltLabel:
        result.append((
          self.resourceURI,
          rdflibWrapper.namespaces["skos"]["closeMatch"],
          rdflib.URIRef(resultAltLabel)
        ))

    if not results == []:
      return results
    else:
      return False
    
  def getSearchResults(self, label):
    baseurl = "http://id.loc.gov/authorities/label/"
    url = baseurl + label
    headers = {"Accept" : "application/rdf+xml"}
    req = urllib2.Request(url, None, headers)
    doc = self.getParsedDoc(req)
    return doc
    
  def getUrlForMatchingLabel(self, doc, label):
    docContext = doc.xpathNewContext()
    docContext.xpathRegisterNs("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    docContext.xpathRegisterNs("skos", "http://www.w3.org/2004/02/skos/core#")
    xpath = "rdf:RDF/rdf:Description[skos:prefLabel[translate(child::text(), '%s', '%s')='%s']]/@rdf:about" % (string.uppercase, string.lowercase, label.lower())
    prefs = docContext.xpathEval(xpath)
    if not prefs == []:
      uri = prefs[0].content
      return uri
    else:
      return False


class GeonamesMapper(Mapper):

  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    # dc:coverage, 651, 662, 751, 752
    # extract = self.doc.getXPath()
    pass


class OpenLibraryMapper(Mapper):

  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    pass
    

class PublisherMapper(Mapper):
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
  
  def mapData(self):
    # pracujeme s: http://sigma.nkp.cz/F/?func=file&file_name=find-b&local_base=NAK
    publisher = self.doc.xpathEval("//varfield[@id='260']/subfield[@label='b']")
    if publisher == []:
      return False
    else:
      publisher = publisher[0].content.strip().strip(",").strip(";").strip(":").strip()
      
  def searchPublisher(self, publisher):
    doc = self.searchAlephBase("http://sigma.nkp.cz", "NAK", "WNA", publisher)
    if doc:
      xpath = "present/record/doc_number[metadata/oai_marc/varfield[@id='NAK'][normalize-space(child::text())='%s']]" % (publisher) # kontrola, zdali v poli NAK je hledaný nakladatel
      publisher = doc.getXPath(xpath)
      # Dodělat!
    else:
      return False


class SiglaMapper(Mapper):
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
  
  def mapData(self):
    # pracujeme s: http://sigma.nkp.cz/F/?func=file&file_name=find-b&local_base=ADR
    sigla = self.doc.getXPath("//varfield[@id='040']/subfield[@label='a']")
    if not sigla == []:
      sigla = sigla[0]
      doc = self.searchAlephBase("http://sigma.nkp.cz", "ADR", "SIG", sigla)
      if doc:
        xpath = "present/record/doc_number[metadata/oai_marc/varfield[@id='SGL']/subfield[@label='a']/text()='%s']" % (sigla)
        docNum = doc.getXPath(xpath)
        if not docNum == []:
          docNum = docNum[0].lstrip("0")
          uri = "http://sigma.nkp.cz/X?op=doc-num&base=ADR&doc-num=" + docNum
          return [(
            self.representationURI,
            rdflibWrapper.namespaces["dc"]["creator"], 
            rdflib.URIRef(uri)
          )]
        else:
          return False
      else:
        return False
    else:
      return False
    
    
class PSHQualifierMapper(Mapper):
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def MapData(self):
    # použít dict pro překlad PSH kvalifikátorů na URI konceptů, které zastupují
    # Bude zapotřebí linkovat na PSH sklizené v rámci data.techlib.cz
    qdict = {
      'el': 'http://data.techlib.cz/resource/psh/1781',
      'ch': 'http://data.techlib.cz/resource/psh/5450',
      've': 'http://data.techlib.cz/resource/psh/11939',
      'zd': 'http://data.techlib.cz/resource/psh/12577',
      'ze': 'http://data.techlib.cz/resource/psh/13220',
      'vo': 'http://data.techlib.cz/resource/psh/12008',
      'gf': 'http://data.techlib.cz/resource/psh/3768',
      'as': 'http://data.techlib.cz/resource/psh/320',
      'en': 'http://data.techlib.cz/resource/psh/2395',
      'vt': 'http://data.techlib.cz/resource/psh/12314',
      'vv': 'http://data.techlib.cz/resource/psh/12156',
      'in': 'http://data.techlib.cz/resource/psh/6445',
      'et': 'http://data.techlib.cz/resource/psh/2086',
      'gl': 'http://data.techlib.cz/resource/psh/4439',
      'if': 'http://data.techlib.cz/resource/psh/6548',
      'pr': 'http://data.techlib.cz/resource/psh/8808',
      'ps': 'http://data.techlib.cz/resource/psh/9194',
      'pp': 'http://data.techlib.cz/resource/psh/8613',
      'ev': 'http://data.techlib.cz/resource/psh/1217',
      'na': 'http://data.techlib.cz/resource/psh/7769',
      'ts': 'http://data.techlib.cz/resource/psh/11453',
      'li': 'http://data.techlib.cz/resource/psh/6914',
      'pe': 'http://data.techlib.cz/resource/psh/8126',
      'te': 'http://data.techlib.cz/resource/psh/11322',
      'pl': 'http://data.techlib.cz/resource/psh/8308',
      'do': 'http://data.techlib.cz/resource/psh/1038', 
      'ob': 'http://data.techlib.cz/resource/psh/7979',
      'fy': 'http://data.techlib.cz/resource/psh/2910',
      'bi': 'http://data.techlib.cz/resource/psh/573',
      'hu': 'http://data.techlib.cz/resource/psh/5176',
      'hi': 'http://data.techlib.cz/resource/psh/5042',
      'fi': 'http://data.techlib.cz/resource/psh/2596',
      'an': 'http://data.techlib.cz/resource/psh/1',
      'gr': 'http://data.techlib.cz/resource/psh/4231',
      'ja': 'http://data.techlib.cz/resource/psh/6641',
      'ma': 'http://data.techlib.cz/resource/psh/7093',
      'sr': 'http://data.techlib.cz/resource/psh/10652',
      'sp': 'http://data.techlib.cz/resource/psh/10067',
      'sv': 'http://data.techlib.cz/resource/psh/9899',
      'st': 'http://data.techlib.cz/resource/psh/10355',
      'um': 'http://data.techlib.cz/resource/psh/11591',
      'sj': 'http://data.techlib.cz/resource/psh/9759',
      'so': 'http://data.techlib.cz/resource/psh/9508',
      'au': 'http://data.techlib.cz/resource/psh/116'
    }
    qualifier = self.doc.getXPath("//varfield[@id='150']/subfield[@label='x']")[0]
    return [(
      self.resourceURI,
      rdflibWrapper.namespaces["skos"]["broaderTransitive"],
      rdflib.URIRef(qdict[qualifier])
    )] # Co bude predikátem?
    

class ISSNMapper(Mapper):
  """ISSN to system number translation. Returns the URI of the previous version."""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    self.results = []
    
  def mapData(self):
    # ISSN předcházející verze
    result = self.mapISSN("//varfield[@id='780']/subfield[@label='x']", rdflibWrapper.namespaces["dbpedia"]["previous"])
      
    # ISSN následující verze
    result = self.mapISSN("//varfield[@id='785']/subfield[@label='x']", rdflibWrapper.namespaces["dbpedia"]["following"])
    
    # Navázané ISSN
    result = self.mapISSN("//varfield[@id='776']/subfield[@label='x']", rdflibWrapper.namespaces["dcterms"]["relation"])

    # Nespecifikovaný vztah na jiné ISSN
    result = self.mapISSN('//varfield[@id="787"]/subfield[@label="x"]', rdflibWrapper.namespaces["dcterms"]["relation"])
    
    # ISSN doplňkové verze  
    result = self.mapISSN('//varfield[@id="770"][@i1="0"]/subfield[@label="x"]', rdflibWrapper.namespaces["dcterms"]["hasPart"])
    
    # ISSN - doplněk
    result = self.mapISSN('//varfield[@id="770"][@i1="1"]/subfield[@label="x"]', rdflibWrapper.namespaces["frbr"]["supplement"])

    # ISSN - suplement/rodič 
    # '//varfield[@id="772"]/subfield[@label="x"]'
    
    # ISSN - sloučeno s ...
    # '//varfield[@id="785"][@i1="0"][@i2="7"]/subfield[@label="x"]'
    # '//varfield[@id="785"][@i1="1"][@i2="7"]/subfield[@label="x"]'
    
    # ISSN - vytvořeno sloučením
    # '//varfield[@id="780"][@i1="0"][@i2="4"]/subfield[@label="x"]'

    # ISSN - rozděleno do ...
    # '//varfield[@id="785"][@i1="0"][@i2="6"]/subfield[@label="x"]'
    
    # ISSN - má překlad
    result = self.mapISSN('//varfield[@id="767"][@i1="0"]/subfield[@label="x"]', rdflibWrapper.namespaces["frbr"]["translation"])
    
    # ISSN - je překladem
    result = self.mapISSN('varfield[@id="765"]/subfield[@label="x"]', rdflibWrapper.namespaces["bibo"]["translationOf"])

    if not self.result == []:
      return self.results
    else:
      return False
      
  def getISSNURI(self, ISSN):
    if not ISSN == []:
      ISSN = ISSN[0]
      doc = self.searchAlephBase("http://aleph.techlib.cz", "STK02", "SSN", ISSN.strip())
      if doc:
        sysno = doc.getXPath("present/record/doc_number")
        if not sysno == []:
          sysno = re.search("\d+$", sysno[0].content).group(0).lstrip("0")
          uri = "http://data.techlib.cz/resource/issn/%s" % (sysno)
          return uri
        else:
          return False
      else:
        return False
    else:
      return False
      
  def mapISSN(self, xpath, predicate):
    ISSN = self.doc.getXPath(xpath)
    issnURI = self.getISSNURI(ISSN)
    if issnURI:
      self.results.append((
        self.resourceURI,
        predicate,
        rdflib.URIRef(issnURI)
      ))
    else:
      return False

   
class LastModifiedDateMapper(Mapper):
  """Maps the last modified data from fixfield 005"""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    
  def mapData(self):
    lastModified = self.doc.getXPath("//fixfield[@id='005']")
    if not lastModified == []:
      lastModified = lastModified[0]
      parseDate = re.search("^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})", lastModified)
      lastModified = "%s-%s-%s+%s:%s" % (parseDate.group(1), parseDate.group(2), parseDate.group(3), parseDate.group(4), parseDate.group(5))
      return [(
        self.representationURI, 
        rdflibWrapper.namespaces["dcterms"]["modified"], 
        rdflib.Literal(lastModified, datatype = rdflibWrapper.namespaces["xsd"]["date"])
      )]
    else:
      return False
      
      
class Fixfield008Mapper(Mapper):
  """Maps the values from the fixfield 008."""
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    self.results = []
    
  def mapData(self):
    eight_21 = []
    eight_21.append(self.doc.getXPath("substring(//fixfield[@id='008'], 22, 1)"))
    predicate = rdflibWrapper.namespaces["rdf"]["type"]
    eight_21_dict = {
      "d" : rdflibWrapper.namespaces["yago"]["Database"],
      # "l" : "updating loose-leaf",
      "m" : rdflibWrapper.namespaces["bibo"]["Series"],
      "n" : rdflibWrapper.namespaces["bibo"]["Newspaper"],
      "p" : rdflibWrapper.namespaces["bibo"]["Periodical"],
      "w" : rdflibWrapper.namespaces["bibo"]["Website"],
    }
    self.mapExtractedValues(predicate, eight_21_dict, eight_21)
    
    eight_23 = []
    eight_23.append(self.doc.getXPath("substring(//fixfield[@id='008'], 24, 1)"))
    eight_23.append(self.doc.getXPath("substring(//fixfield[@id='008'], 25, 1)"))
    predicate = rdflibWrapper.namespaces["dc"]["format"]
    eight_23_dict = {
      "a" : rdflibWrapper.namespaces["yago"]["Microfilm"],
      "b" : rdflibWrapper.namespaces["yago"]["Microfiche"],
      # "c" : "microopaque",
      # "d" : "large print",
      # "e" : "newspaper print",
      "f" : rdflibWrapper.namespaces["yago"]["Braille"],
      "s" : rdflibWrapper.namespaces["yago"]["ElectronicText"],
    } # rdf:type dcterms:physicalMedium .
    self.mapExtractedValues(predicate, eight_23_dict, eight_23)
    
    if not self.results == []:
      return self.results
    else:
      return False
    
  def mapExtractedValues(self, predicate, valueDict, extractedValues):
    for extractedValue in extractedValues:
      try:
        self.results.append((
          self.representationURI,
          predicate, 
          valueDict[extractedValue]
        ))
      except KeyError:
          pass
          
          
class Varfield245SubfieldBMapper(Mapper):
  """
    Maps values from subfield $b in field 245.
  """
  
  def __init__(self, doc, resourceURI, representationURI):
    Mapper.__init__(self, doc, resourceURI, representationURI)
    self.results = []
    
  def mapData(self):
    extractedValue = self.doc.getXPath('//varfield[@id="245"]/subfield[@label="b"]')
    if not extractedValue == []:
      extractedValue = extractedValue[0]
      pass # To implement!
    else:
      return False

