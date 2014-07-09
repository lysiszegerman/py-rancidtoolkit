#!/usr/bin/env python
# 
# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Common functions for rancid configuration archive and (device-)platform independant calling of functions
"""

import sys
import re
import os.path
import ParseConfig.Cisco
import ParseConfig.Juniper

class RancidConfig(object):
  """Locations and base directory for RANCID installation, initialize with defaults if none given
     Put your default values in the __init__ function.
  """
  
  LOCATIONS = list()
  BASE = ""
  
  def __init__(self, locations = None, rancid_base = ""):
    super(RancidConfig, self).__init__()
    if locations == None and rancid_base == "":
      if sys.platform == "darwin":
        self.BASE = "/Users/lysis/share/rancid"
        self.LOCATIONS = [ "darmstadt", "frankfurt", "wiesbaden", "amsterdam", "momus" , "test", "hmwk", "tiz" ]
      else:
        self.BASE = "/home/rancid/var"
        self.LOCATIONS = [ "darmstadt", "frankfurt", "wiesbaden", "amsterdam", "momus", "tiz" ]
    else:
      if type(locations) == list:
        self.LOCATIONS = locations
      elif type(locations) == str:
        self.LOCATIONS = [locations]
      if type(rancid_base) == str:
        self.BASE = rancid_base
    # if not initialized
  # def __init__

  def setLocations(self, locations):
    self.LOCATIONS = locations
  # def setLocation

  def setRancidBase(self, rancid_base):
    self.rancid_base = rancid_base
  # def setRancidBase

class Rancid(object):
  """base class for Rancid functions"""
  
  LOCATIONS = list()
  rancid_base = ""
  
  def __init__(self, config = None):
    """initialize with locations and RANCID base directory
    """
    super(Rancid, self).__init__()
    if type(config) != RancidConfig:
      config = RancidConfig()
    
    self.LOCATIONS = config.LOCATIONS
    self.rancid_base = config.BASE
  # def __init__

  def readRouterDb(self):
    """reads all available router.db files and returns result as list"""
    ret = list()
    for loc in self.LOCATIONS:
      hand = False
      try:
        hand = open(self.rancid_base+"/"+loc+"/"+"/router.db")
      except:
        continue
      # try
      for line in hand:
        line=line[:-1]
        if line == "" or re.match("^#", line) or re.match("^\s+$", line):
          continue
        ret.append(line+":"+loc)
      # for line
    # for loc
    return ret  
  # def readRouterDb

  def getActiveDevices(self):
    """return a list of dicts {hostname, vendor} for all active devices
    """
    ret = dict()
    devs = self.readRouterDb()
    for dev in devs:
      linesplit = dev.split(":")
      if linesplit[2] == "up":
        ret.update({linesplit[0]: linesplit[1]})
      # if linesplit
    # for dev
    return ret
  # def getAllDevices

  def filterActiveDevices(self, filter=""):
    """filters all active devices according to dict filter
       if filter has a key "vendor" filter for vendor type
       if filter has a key "name" filter for regexp on hostname
    """
    devices = self.getActiveDevices()
    if type(filter) == dict:
      if filter.has_key('vendor'):
        filterdev = devices.copy()
        for dev in devices.keys():
          if devices[dev].lower() != filter['vendor'].lower():
            filterdev.pop(dev)
        # for dev
        devices = filterdev.copy()
      # if vendor
      if filter.has_key('name'):
        filterdev = devices.copy()
        for dev in devices.keys():
          if not re.search(filter['name'], dev):
            filterdev.pop(dev)
        # for dev
        devices = filterdev.copy()
      # if device
    # if filter
    return devices.keys()
  # def GetActiveDevices

  def getRancidEntry(self, device):
    """returns a list with [hostname, vendor, state, location] for the given device name (first match search)
       or an empty list if no match is found
    """
    devs = self.readRouterDb()
    for dev in devs:
      if re.match("^"+device, dev):
        ret = dev.split(":")
        return ret[0:2]+[ret[3]]
      # if device
    # for line
    return []
  # def getRancifEntry

  def getFilename(self, device):
    """returns saved config filename for device
    """
    rancidEntry = self.getRancidEntry(device)
    if len(rancidEntry) == 0:
      return []
    # if
    filename = self.rancid_base+"/"+rancidEntry[2]+"/configs/"+rancidEntry[0]
    if os.path.isfile(filename):
      fh = open(filename)
      firstline = fh.readline()
      fh.close()
    else:
      return []
    # if os.path

    typere = re.search("RANCID-CONTENT-TYPE: (\w+)", firstline)
    routertype = ""
    if typere:
      routertype = typere.group(1)
    else:
      return []
    # if
    return [filename, routertype]
  # def getFilename

  def printableInterfaceList(self, device):
    """returns a printable list of interfaces for device
    """
    try:
      (filename, routertype) = self.getFilename(device)
    except:
      return ["Cannot find device "+device+" in rancid configuration."]

    intlist = dict()

    if routertype == "cisco":
      intlist = ParseConfig.Cisco.interfaces(filename)
    elif routertype == "force10":
      intlist = ParseConfig.Cisco.interfaces(filename)
    elif routertype == "juniper":
      intlist = ParseConfig.Juniper.interfaces(filename)
    else:
      print "Unknown type",routertype,"in",filename

    ret = []
    for interface in intlist.keys():
      unit = ""
      unitre = re.search("(\.[0-9]+)$", interface)
      inttemp = interface
      if unitre:
        unit = unitre.group(1)
        inttemp = re.sub(".[0-9]+$", "", interface)
      lastintid = re.search("^(.*)/([0-9])$", inttemp)
      if lastintid:
        intstr = lastintid.group(1)+"/0"+lastintid.group(2)
      else:
        intstr = inttemp
      if unit:
        intstr = intstr+unit
      ret.append(intstr+": "+intlist[interface])
    # for interface
    ret.sort()
    return ret
  # def printableInterfaceList

  def interfaceDescriptionList(self, device):
    """returns a dict {interface: description} for all interfaces of device
    """
    try:
      (filename, routertype) = self.getFilename(device)
    except:
      return {"error": "Cannot find device "+device+" in rancid configuration."}

    if routertype == "cisco":
      return ParseConfig.Cisco.interfaces(filename)
    elif routertype == "force10":
      return ParseConfig.Cisco.interfaces(filename)
    elif routertype == "juniper":
      return ParseConfig.Juniper.interfaces(filename)
    else:
      return {"error":"Unknown type "+routertype+" in "+filename}
  # def interfaceList

  def interfaceAddressList(self, device):
    """returns a dict {interface:{"ip": address, "ipv6": address}} for all interfaces of device
    """
    try:
      (filename, routertype) = self.getFilename(device)
    except:
      return {"error": "Cannot find device "+device+" in rancid configuration."}

    if routertype == "cisco":
      return ParseConfig.Cisco.addresses(filename)
    elif routertype == "force10":
      return ParseConfig.Cisco.addresses(filename)
    elif routertype == "juniper":
      return ParseConfig.Juniper.addresses(filename)
    else:
      return {"error":"Unknown type "+routertype+" in "+filename}
  # def interfaceAddressList
  
  def printFilterSection(self, filename, filterstr):
    """filters the config for filename according to filterstr and prints it in a nice way
    """
    if filename[1] == "juniper":
      sections = ParseConfig.Juniper.section(filename[0],filterstr)
      ParseConfig.Juniper.printSection(sections)
    else:
      sections = ParseConfig.Cisco.section(filename[0],".* ".join(filterstr))
      ParseConfig.Cisco.printSection(sections)
  # def printFilterSection

  def printSection(self, vendor, section):
    """prints section in a nice way
    """
    if vendor == "juniper":
      ParseConfig.Juniper.printSection(section)
    else:
      ParseConfig.Cisco.printSection(section)
  # def printSection
    
  
