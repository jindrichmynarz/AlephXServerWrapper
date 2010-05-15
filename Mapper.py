#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib
import urllib2
import libxml2
import re
import time
import string
from alephXServerWrapper import *

class Mapper():
  """Obecná třída pro mapování hodnot."""
  
  def __init__(self, doc):
    """Na vstupu bere 1 argument - instanci třídy alephXServerWrapper.Record."""
    self.doc = doc # Na vstupu bere celý XML záznam (class Record)
    
  def mapData(self):
    """Vrací pole s tuples s predikáty a jejich objekty, subjektem je vždy zpracováváný dokument.
    Tuto metodu každá podtřída přepisuje."""
    return [("predikát 1", "objekt 1"), ("predikát 2", "objekt 2")]
   
  def getParsedDoc(self, url):
    """Na zadané URL nebo urllib2.Request vrátí naparsovaný XML dokument.""" 
    result = urllib2.urlopen(url)
    doc = result.read()
    result.close()
    doc = libxml2.parseDoc(doc)
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
    error = doc.xpathEval("find/error")
    if error == []:
      noRecords = doc.xpathEval("find/no_records")[0].content
      setNumber = doc.xpathEval("find/set_number")[0].content
      url = "%sX?op=present&base=%s&set_entry=1-%s&set_number=%s" % (baseUrl, baseCode, noRecords.lstrip("0"), setNumber)
      doc = self.getParsedDoc(url)
      return doc
    else:
      return False

class DCMITypeMapper(Mapper):
  """Mapování typu dokumentu na DCMI Types, resp. typy z dalších ontologií (BIBO, YAGO)."""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    returnValue = None
    position6 = self.doc.getXPath("substring(//fixfield[@id='LDR'], 6, 1)")
    position7 = self.doc.getXPath("substring(//fixfield[@id='LDR'], 7, 1)")
    
    if position6 in ["a"]:
      return [("dc:type", "dctypens:Text")]
    if position6 in ["c"]:
      return [("dc:type", "yago:SheetMusic")]
    if position6 in ["d"]:
      return [("dc:type", "yago:SheetMusic"), ("dc:type", "yago:Manuscript")]
    if position6 in ["e", "f", "g", "k"]:
      return [("dc:type", "dctypens:Image")]
    if position6 in ["i", "j"]:
      return [("dc:type", "dctypens:Sound")]
    if position6 in ["p"] and position7 in ["c", "s"]:
      return [("dc:type", "dctypens:Collection")]
    if position6 in ["t"]:
      return [("dc:type", "bibo:Manuscript")]
    
    
class LanguageMapper(Mapper):
  """Mapování na kódy jazyků."""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    # Získání language codes
    languageCodes = []
    
    extract = self.doc.getXPath("substring(//fixfield[@id='008'], 37, 2)")
    languageCodes.append(extract)
    
    extract = self.doc.getXPath("//varfield[@id='040']/subfield[@label='b']")
    if not extract == []:
      languageCodes.append(extract)
      
    extract = self.doc.getXPath("//varfield[@id='041']/subfield")
    if not extract == []:
      for subfield in extract:
        if subfield.noNsProp("label") in ["a", "b", "c", "d", "e", "f", "g", "h", "j"]:
          languageCodes.append(subfield)
        
    extract = self.doc.getXPath("//varfield[@id='242']/subfield[@label='y']")
    if not extract == []:
      languageCodes.append(extract)
      
    extract = self.doc.getXPath("//varfield[@id='775']/subfield[@label='e']")
    if not extract == []:
      languageCodes.append(extract)
      
    # Deduplikace language codes
    languageCodes = list(set(languageCodes))
    
    # Validace language codes
    validLanguageCodes = []
    for languageCode in languageCodes:
      # MARCCodes
      uri = "http://purl.org/NET/marccodes/languages/%s" % (languageCode)
      valid = self.validateURI(uri)
      if valid:
        validCountryCodes.append(("dc:language", uri))
      
      # Lexvo
      uri = "http://www.lexvo.org/id/iso639-3/%s" % (languageCode)
      valid = self.validateURI(uri)
      if valid:
        validCountryCodes.append(("dc:language", uri))
          
    return validLanguageCodes
   
   
class CountryMapper(Mapper):
  """Mapování na kódy států."""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):    
    # Získání country codes
    countryCodes = []

    extract = self.doc.getXPath("substring(//fixfield[@id='008'], 17, 2)")
    countryCodes.append(extract)

    extract = self.doc.getXPath("//fixfield[@id='044']/subfield[@label='a']")
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
        validCountryCodes.append(("dc:coverage", uri))
    
    return validCountryCodes
    
    
class GeographicAreaMapper(Mapper):
  """Mapování geografických oblastí na MARC Codes"""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    geographyAreaCode = self.doc.getXPath("//varfield[@id='043']/subfield[@label='a']")
    if not geographyAreaCode == []:
      uri = "http://purl.org/NET/marccodes/gacs/%s#location" % (geographyAreaCode[0])
      valid = self.validateURI(uri)
      if valid:
        return [("dc:coverage", uri)]
        

class PSHMapper(Mapper):
  """Mapování z preferovaných hesel PSH v bibliografických záznamech na URI těchto hesel"""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    pshTerms = self.doc.getXPath("//varfield[@id='650']/subfield[@label='a']")
    if not pshTerms == []:
      for pshTerm in pshTerms:
        # Dodělat: RDFLib dotaz na skos:prefLabel[@xml:lang='cs']
        pass
        
      
class AuthorMapper(Mapper):
  """Mapování jmen autorů z bibliografických záznamů na záznamy autoritní"""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    author = self.doc.getXPath("//varfield[@id='100']/subfield[@label='a']")
    if not author == []:
      author = author[0]
      # Dodělat: RDFLib dotaz na STK11
    

class VIAFMapper(Mapper):
  """Mapování ze jmenných autoritních záznamů na VIAF."""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    fmt = self.doc.getXPath("//fixfield[@id='FMT']")[0]
    if fmt == "JA": # Pokud jde o jmennou autoritu
      authorName = self.doc.getXPath("//varfield[@id='100']/subfield[@label='a']")
      authorCode = self.doc.getXPath("//varfield[@id='100']/subfield[@label='7']")
      if (not authorName == []) and (not authorCode == []):
        authorName = authorName[0]
        authorCode = authorCode[0]
        
        headers = {"Accept" : "application/rdf+xml"}
        url = """http://viaf.org/search?query=local.mainHeadingEl+=+%22""" + authorCode + """%22&version=1.1&operation=searchRetrieve"""
        
        req = urllib2.Request(url, None, headers)
        doc = self.getParsedDoc(req)
        docContext = doc.xpathNewContext()
        docContext.xpathRegisterNs("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        docContext.xpathRegisterNs("skos", "http://www.w3.org/2004/02/skos/core#")
        docContext.xpathRegisterNs("foaf", "http://xmlns.com/foaf/0.1/")
        
        foafName = docContext.xpathEval("//foaf:name")
        foafName = foafName[0].content
        
        # Kontrola podle jména autora
        if foafName in authorName or authorName in foafName:
          conceptId = docContext.xpathEval("//skos:Concept/@rdf:about")
          match = re.match(".*(?=\.)", conceptId[0].content) # Odstraní příponu typu souboru
          conceptId = match.group()
          conceptId = "http://viaf.org/" + conceptId
          
          return [("owl:sameAs", conceptId)]


class DBPediaMapper(Mapper):
  """Mapování na zdroje v DBPedii."""
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
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
      results.append(("skos:exactMatch", match))
    
    # Mapování nepreferovaného znění hesla
    for altLabel in altLabels:
      url = baseurl + urllib.quote(altLabel)
      doc = self.getParsedDoc(url)
      match = self.checkMatch(altLabel, doc)
      if match:
        results.append(("skos:closeMatch", match))
    
    return results
    
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

  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    record = MarcARecord(self.doc)
    prefLabel = record.getPrefLabelEN()
    altLabels = record.getNonprefLabelsEN()
    
    result = []
    
    resultPrefLabel = self.getUrlForMatchingLabel(self.getSearchResults(prefLabel), prefLabel)
    if resultPrefLabel:
      result.append(("skos:exactMatch", resultPrefLabel))
    
    for altLabel in altLabels:
      resultAltLabel = self.getUrlForMatchingLabel(self.getSearchResults(altLabel), altLabel)
      if resultAltLabel:
        result.append(("skos:closeMatch", resultAltLabel))
        
    return result
    
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

  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    pass


class OpenLibraryMapper(Mapper):

  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    pass
    

class PublisherMapper(Mapper):
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
  
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
      url = "http://sigma.nkp.cz/X?op=present&base=NAK&set_entry=1-%s&set_number=%s" % (noRecords.lstrip("0"), setNumber)
      doc = self.getParsedDoc(url)
      xpath = "present/record/doc_number[metadata/oai_marc/varfield[@id='NAK'][normalize-space(child::text())='%s']]" % (publisher) # kontrola, zdali v poli NAK je hledaný nakladatel
      # DODĚLAT!
    else:
      return False


class SiglaMapper(Mapper):
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
  
  def mapData(self):
    # pracujeme s: http://sigma.nkp.cz/F/?func=file&file_name=find-b&local_base=ADR
    sigla = self.doc.xpathEval("varfield[@id='040']/subfield[@label='a']")
    if not sigla == []:
      sigla = sigla[0].content
      doc = self.searchAlephBase("http://sigma.nkp.cz", "ADR", "SIG", sigla)
      if doc:
        xpath = "present/record/doc_number[metadata/oai_marc/varfield[@id='SGL']/subfield[@label='a']/text()='%s']" % (sigla)
        docNum = doc.xpathEval(xpath)
        if not docNum == []:
          docNum = docNum[0].content.lstrip("0")
          uri = "http://sigma.nkp.cz/X?op=doc-num&base=ADR&doc-num=" + docNum
          return [("dc:creator", uri)]
        else:
          return False
      else:
        return False
    else:
      return False
    
    
class PSHQualifierMapper(Mapper):
  
  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
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
    return [("skos:broaderTransitive", qdict[qualifier])] # Co bude predikátem?
    

class ISSNMapper(Mapper):
  """ISSN to system number translation. Returns the URI of the previous version."""
  
  def __init__(self, doc, linkType):
    # linkType = {"previous" | "following" }
    Mapper.__init__(self, doc)
    self.type = linkType
    
  def mapData(self):
    if linkType == "previous":
      ISSN = self.doc.xpathEval("//varfield[@id='780']/subfield[@label='x']")
      predicate = "dbpedia:previous"
    if linkType == "following":
      ISSN = self.doc.xpathEval("//varfield[@id='785']/subfield[@label='x']")
      predicate = "dbpedia:following"
    else:
      raise ValueError("Incorrect ISSN link type.")
      
    if not ISSN == []:
      ISSN = ISSN[0].content
      doc = self.searchAlephBase("http://aleph.techlib.cz", "STK02", "SSN", ISSN.strip())
      if doc:
        sysno = doc.xpathEval("present/record/doc_number")
        if not sysno == []:
          sysno = sysno[0].content.lstrip("0")
          uri = "http://data.techlib.cz/resource/issn/%s" % (sysno)
          return [(predicate, uri)]
        else:
          return False
      else:
        return False
    else:
      return False
