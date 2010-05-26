#!/usr/bin/env python
#-*- coding:utf-8 -*-

import MySQLdb
from ConfigParser import ConfigParser
from getpass import getpass

config = ConfigParser()
config.read("config.ini")
password = getpass()

# Intialization
db = MySQLdb.connect(host=config.get("store", "host"), user=config.get("store", "user"), passwd=password, db=config.get("store", "db"))
cursor = db.cursor()

cursor.execute("DROP DATABASE rdfstore;")
cursor.execute("CREATE DATABASE rdfstore;")

if False:
  # Drop views
  cursor.execute("SHOW FULL TABLES WHERE Table_type='VIEW';")
  tables = cursor.fetchall()
  for table in tables:
    print "Dropping view %s" % (table[0])
    sql = "DROP VIEW %s;" % (table[0])
    cursor.execute(sql)

  # Drop tables
  cursor.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE';")
  tables = cursor.fetchall()
  for table in tables:
    print "Dropping table %s" % (table[0])
    sql = "DROP TABLE %s;" % (table[0])
    cursor.execute(sql)

db.close()
