#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib
import urllib2
import libxml2
import re
import time

class Mapper():
  """Obecná třída pro mapování hodnot."""
  
  def __init__(self, doc):
    """Na vstupu bere 1 argument - instanci třídy alephXServerWrapper.Record."""
    self.doc = doc # Na vstupu bere celý XML záznam (class Record)
    
  def mapData(self):
    """Vrací pole s tuples s predikáty a jejich objekty, subjektem je vždy zpracováváný dokument.
    Tuto metodu každá podtřída přepisuje."""
    return [("predikát 1", "objekt 1"), ("predikát 2", "objekt 2")]
    
  def validateURI(self, uri):
    """Zjišťuje, zdali je zadané URI dostupné."""
    try:
      urllib2.urlopen(uri)
      return True
    except urllib2.HTTPError:
      return False


class DCMITypeMapper(Mapper):
  """Mapování typu dokumentu na DCMI Types"""
  
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
      return [("dc:type", "yago:Manuscript")]
    
    
class LanguageMapper(Mapper):
  
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
      uri = "http://purl.org/NET/marccodes/languages/%s" % (languageCode)
      valid = self.validateURI(uri)
      if valid:
        validCountryCodes.append(("dc:coverage", uri))
    
    return validLanguageCodes
   
   
class CountryMapper(Mapper):
  
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
        validCountryCodes.append(("dc:language", uri))
    
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
        
        response = urllib2.urlopen(req)
        doc = response.read()
        response.close()
        
        doc = libxml2.parseDoc(doc)
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

  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    # Extrahovat preferované znění v angličtině
    # Nepreferované znění v angličtině?
    prefLabel = self.doc.getPrefLabelEN()
    altLabels = self.doc.getNonprefLabelsEN()
    baseurl = "http://lookup.dbpedia.org/api/search.asmx/KeywordSearch?QueryClass=&MaxHits=1&QueryString="

    results = []
    # Mapování preferovaného znění hesla
    url = baseurl + urllib.quote(prefLabel)
    result = urllib2.urlopen(url)
    doc = result.read()
    result.close()
    
    # Mapování nepreferovaného znění hesla
    for altLabel in altLabels:
      url = baseurl + urllib.quote(altLabel)

class LCSHMapper(Mapper):

  def __init__(self, doc):
    Mapper.__init__(self, doc)
    
  def mapData(self):
    pass
    
    
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
