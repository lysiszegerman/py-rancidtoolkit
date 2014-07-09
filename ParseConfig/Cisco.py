#!/usr/bin/env python
# 
# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Cisco specific parsing of configuration files
"""

import re
import os.path
from Rancid import *

def section(filename,section):
  """returns a list with all configuration within section from filename
  """
  fh = open(filename)
  ret = []
  insec = False
  spaces = ""
  secret = []
  #
  for line in fh:
    line=line[:-1]
    if re.match("^!", line):
      continue
    # if comment
    #
    reobj = re.match("^(\s*)"+section, line, flags=re.I)
    if reobj:                       # match on section
      if insec:                     # already in section
        ret = ret + [secret]        # save the old section
      # if insec
      spaces = reobj.group(1)       # start a new section
      insec = True
      secret = []
    # if reobj
    #
    if insec:                       # already in section
      secreobj = re.match("^"+spaces+"[^\s]", line)
      if len(secret) > 0 and secreobj: # not first line of section (which always
                                       # matches the pattern) and match
        ret = ret + [secret]           # old section is over, save section
        insec = False                  
      # if secreobj
      secret = secret + [line]      # save to current section
    # if insec
  # for line
  return ret
# def section

def filterSection(section,filter):
  """filters section according to regexp terms in filter and outputs a list of all matched entries
  """
  ret = []
  for sec in section:
    secret = []
    for line in sec:
      line = line.lstrip()
      if re.match(filter,line,re.I):
        secret = secret + [line]
    # for line
    ret = ret + [secret]
  # for sec
  return ret
# def filterSection

def filterConfig(filename, secstring, filter):
  """extracts sections secstring from the entire configuration in filename and filters against regexp filter
     returns a list of all matches
  """
  return filterSection(section(filename, secstring), filter)
# def parse

def interfaces(filename):
  """find interfaces and matching descriptions from filename and return dict with interface=>descr
  """
  parseresult = filterConfig(filename, "interface", "^interface|^description")
  ret = dict()
  skipdescr = False
  for sec in parseresult:
    intret = ""
    for line in sec:
      reobj = re.match("interface (.*)", line)
      if reobj:
        skipdescr = False
        if re.match("Vlan", reobj.group(1)):
          skipdescr = True
        else:
          intret = reobj.group(1)
        # not re.match
      # reobj
      if not skipdescr:
        reobj = re.match("description (.*)", line)
        if reobj:
            ret[intret] = reobj.group(1)
          # if skipdescr
        else:
          ret[intret] = ""
        # if reobj
      # if not skipdescr
    # for line
  # for sec
  return ret
# interfaceCisco

def addresses(filename):
  """find ip addresses configured on all interfaces from filename and return dict with interface=>(ip=>address, ipv6=>address)
  """
  parseresult = filterConfig(filename, "interface", "^interface|^ip address|^ipv6 address")
  ret = dict()

  for sec in parseresult:
    intret = ""
    for line in sec:
      reobj = re.match("interface (.*)", line)
      if reobj:
        intret = reobj.group(1)
      # reobj
      if intret:
        # FIXME: exclude interfaces with shutdown configured
        reobj = re.match("(ip|ipv6) address (.*)", line)
        if reobj:
          if not ret.has_key(intret):
            ret[intret] = dict()
          ret[intret].update({reobj.group(1): re.split('[\/ ]', reobj.group(2))[0]})
        # if reobj
      # if intret
    # for line
  # for sec
  return ret
# addresses

def printSection(section):
  """prints section in a nice way"""
  if type(section) == list:
    for line in section:
      printSection(line)
  else:
    print section
# def printSection

