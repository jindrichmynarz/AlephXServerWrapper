#!/bin/sh

# Clean the database
python dropTables.py;

# Create PSH translate table in the form: "skos:prefLabel"; PSH_ID
python makeTempPSHTranslateTable.py;

# Clear crawler status
rm crawlerStatus.txt;

# Crawl PSH base
python psh_crawler.py;

# Clear crawler status
rm crawlerStatus.txt;

# Crawl ISSN base
python issn_crawler.py

# Clear crawler status
rm crawlerStatus.txt;

# Crawl BIB base
python bib_crawler.py

