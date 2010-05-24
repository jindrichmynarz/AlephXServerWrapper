#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
from Mapper import *
from callbacks import *
import rdflibWrapper

report("INFO: inicializace X Serveru")
a = XServer("http://aleph.techlib.cz/X", debug=True)

report("INFO: inicializace báze")
b = Base(a, "STK01")

report("INFO: inicializace crawleru")
crwlr = Crawler(b)

report("INFO: inicializace callbacku")
cbfx = STK01Callback()

report("INFO: začátek crawlování")
crwlr.crawl(cbfx, sleep=0)
