#!/usr/bin/env python
#-*- coding:utf-8 -*-

import rdflib
from rdflib.Graph import ConjunctiveGraph as Graph
from rdflib.store import Store, VALID_STORE
from report import report
from ConfigParser import ConfigParser
# from getpass import getpass

# Namespace initialization
namespaces = {
  "rdf" : rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
  "xsd" : rdflib.Namespace("http://www.w3.org/2001/XMLSchema#"),
  "owl" : rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
  "cc" : rdflib.Namespace("http://creativecommons.org/ns#"),
  "dc" : rdflib.Namespace("http://purl.org/dc/elements/1.1/"),
  "dcterms" : rdflib.Namespace("http://purl.org/dc/terms/"),
  "skos" : rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
  "dctype" : rdflib.Namespace("http://purl.org/dc/dcmitype/"),
  "yago" : rdflib.Namespace("http://www.mpii.de/yago/resource/"),
  "frbr" : rdflib.Namespace("http://purl.org/vocab/frbr/core#"),
  "bibo" : rdflib.Namespace("http://purl.org/ontology/bibo/"),
  "geo" : rdflib.Namespace("http://www.geonames.org/ontology#"),
  "dbpedia" : rdflib.Namespace("http://dbpedia.org/property/"),
  "sioc" : rdflib.Namespace("http://rdfs.org/sioc/ns#"),
  "dcam" : rdflib.Namespace("http://purl.org/dc/dcam/"),
  "marcrel" : rdflib.Namespace("http://www.loc.gov/loc.terms/relators/"), # Must be read from Google's cache, or from http://www.loc.gov/marc/relators/relacode.html
}
   
def connect():
  report("INFO: connecting RDFStore")
  config = ConfigParser()
  config.read("config.ini")
  # password = getpass()
  configString = "host=%s,user=%s,password=%s,db=%s" % (config.get("store", "host"), config.get("store", "user"), config.get("store", "password"), config.get("store", "db"))

  store = rdflib.plugin.get("MySQL", Store)("rdfstore")
  rt = store.open(configString, create=False)

  if rt == 0:
    store.open(configString, create=True)
  else:
    assert rt == VALID_STORE, "The store is valid"
  # Tato funkce by nejspíš měla vracet proměnnou "store" - connection na RDFLib DB
  return store

store = connect()

def commitData(triples): 
  """
    Commits triples to RDF store
  """
  report("INFO: rdflibWrapper.commitData")
  # default_graph_uri = "http://rdflib.net/rdfstore"
  
  graph = Graph(store) # Other optional argument: identifier = rdflib.URIRef(default_graph_uri)
  triples = list(set(triples)) # Deduplication of triples
  report("INFO: adding %d triples" % (len(triples)))
  for triple in triples:
    report("S:%s, P:%s, O:%s" % (str(triple[0]), str(triple[1]), str(triple[2])))
  
  map(lambda triple: graph.add(triple), triples) # Add triples to the graph

  graph.commit() # Commit newly added triples
