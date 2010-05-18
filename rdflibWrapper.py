#!/usr/bin/env python
#-*- coding:utf-8 -*-

import rdflib

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
