#!/usr/bin/env python
#-*- coding:utf-8 -*-

from alephXServerWrapper import *
from Mapper import *


class Callback(Object):
  
  def __init__(self, baseName):
    self.results = [] # (subject, predicate, object)
    self.unmapped = [] # (XPath, value)
    self.baseName = baseName
    
  def commitData(self):
    """Saves self.results into RDFLib."""
    pass
    
  def writeUnmapped(self):
    """Saves unmapped data to output CSV."""
    timestamp = str(int(time.mktime(time.localtime())))  
    filename = "%s-%d.csv" % (self.baseName, timestamp)
    file = open(filename, "w")
    file.write("\n".join(map((lambda unmap: ";".join(unmap)), self.unmapped)))
    file.close()
    
  def main(self):
    """Main data extraction. Must be overwritten by a child class."""
    pass
    
  def run(self):
    """Runs the callback."""
    self.main()
    self.commitData()
    self.writeUnmapped()
  
  
class STK02Callback(Callback):
  
  def __init__(self, baseName="STK02"):
    Callback.__init__(self)
    
  def main(self):
    pass
    
    
class STK10Callback(Callback):
  
  def __init__(self, baseName="STK10"):
    Callback.__init__(self)
    
  def main(self):
    pass


class STK01Callback(Callback):
  
  def __init__(self, baseName="STK01"):
    Callback.__init__(self)
    
  def main(self):
    pass    
