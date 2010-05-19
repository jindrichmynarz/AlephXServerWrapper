#!/usr/bin/env python
#-*- coding:utf-8 -*-

import rdflib
from rdflib.Graph import ConjunctiveGraph as Graph
from rdflib.store import Store, VALID_STORE

# Namespace initialization
namespaces = {
  "rdf" : rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
  "xsd" : rdflib.Namespace("http://www.w3.org/2001/XMLSchema#"),
  "owl" : rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
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
}

def connect():
  configString = "host=localhost,user=username,password=password,db=rdfstore" # Přesunout do config souboru, který bude přístupný na zadání hesla. Můžeme udělat až po ELAGu.

  store = rdflib.plugin.get("MySQL", Store)("rdfstore")
  rt = store.open(configString, create=False)

  if rt == 0:
    store.open(configString, create=True)
  else:
    assert rt == VALID_STORE, "The store is valid"
  # Tato funkce by nejspíš měla vracet proměnnou "store" - connection na RDFLib DB
    
def commitData(triples):  
  default_graph_uri = "http://rdflib.net/rdfstore" # K čemu tohle slouží?
  graph = Graph(store, identifier=rdflib.URIRef(default_graph_uri)) # Graph se bude vytvářet pokaždé?
  triples = list(set(triples)) # Deduplication of triples
  map(lambda triple: graph.add(triple), triples) # Add triples to the graph
  graph.commit() # Commit newly added triples
