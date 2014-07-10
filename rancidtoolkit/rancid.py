#!/usr/bin/env python
#
# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Common functions for rancid configuration archive and (device-)platform
independant calling of functions
"""

import sys
import re
import os.path
from . import cisco
from . import juniper


class RancidConfig(object):
    """Locations and base directory for RANCID installation, initialize with
    defaults if none given
    Put your default values in the __init__ function.
    """

    LOCATIONS = list()
    BASE = ""

    def __init__(self, locations=None, rancid_base=""):
        super(RancidConfig, self).__init__()
        if locations is None and rancid_base == "":
            # FIXME dirty hack for local dev copy
            if sys.platform == "darwin":
                self.BASE = "/Users/lysis/share/rancid"
                self.LOCATIONS = ["darmstadt", "frankfurt", "wiesbaden",
                                  "amsterdam", "momus", "test", "hmwk",
                                  "tiz"]
            else:
                self.BASE = "/home/rancid/var"
                self.LOCATIONS = ["darmstadt", "frankfurt", "wiesbaden",
                                  "amsterdam", "momus", "tiz"]
        else:
            if type(locations) == list:
                self.LOCATIONS = locations
            elif type(locations) == str:
                self.LOCATIONS = [locations]
            if type(rancid_base) == str:
                self.BASE = rancid_base

    def setLocations(self, locations):
        self.LOCATIONS = locations

    def setRancidBase(self, rancid_base):
        self.rancid_base = rancid_base


class Rancid(object):
    """base class for Rancid functions"""

    LOCATIONS = list()
    rancid_base = ""

    def __init__(self, config=None):
        """ initialize with locations and RANCID base directory """
        super(Rancid, self).__init__()
        if type(config) != RancidConfig:
            config = RancidConfig()
        self.LOCATIONS = config.LOCATIONS
        self.rancid_base = config.BASE

    def readRouterDb(self):
        """ reads all available router.db files and returns result as list """
        ret = list()
        for loc in self.LOCATIONS:
            hand = False
            try:
                hand = open(self.rancid_base + "/" + loc + "/" + "/router.db")
            except:
                continue
            for line in hand:
                line = line[:-1]
                if line == "" or re.match("^#", line) or \
                        re.match("^\s+$", line):
                    continue
                ret.append(line + ":" + loc)
        return ret

    def getActiveDevices(self):
        """ return a list of dicts {hostname, vendor} for all active
        devices """
        ret = dict()
        devs = self.readRouterDb()
        for dev in devs:
            linesplit = dev.split(":")
            if linesplit[2] == "up":
                ret.update({linesplit[0]: linesplit[1]})
        return ret

    def filterActiveDevices(self, filter=""):
        """ filters all active devices according to dict filter
            if filter has a key "vendor" filter for vendor type
            if filter has a key "name" filter for regexp on hostname
        """
        devices = self.getActiveDevices()
        if type(filter) == dict:
            if 'vendor' in filter:
                filterdev = devices.copy()
                for dev in devices.keys():
                    if devices[dev].lower() != filter['vendor'].lower():
                        filterdev.pop(dev)
                devices = filterdev.copy()
            if 'name' in filter:
                filterdev = devices.copy()
                for dev in devices.keys():
                    if not re.search(filter['name'], dev):
                        filterdev.pop(dev)
                devices = filterdev.copy()
        return devices.keys()

    def getRancidEntry(self, device):
        """ returns a list with [hostname, vendor, state, location] for the
        given device name (first match search) or an empty list if no
        match is found """
        devs = self.readRouterDb()
        for dev in devs:
            if re.match("^" + device, dev):
                ret = dev.split(":")
                return ret[0:2] + [ret[3]]
        return []

    def getFilename(self, device):
        """ returns saved config filename for device """
        rancidEntry = self.getRancidEntry(device)
        if len(rancidEntry) == 0:
            return []
        filename = self.rancid_base + "/" + rancidEntry[2] + \
            "/configs/" + rancidEntry[0]
        if os.path.isfile(filename):
            fh = open(filename)
            firstline = fh.readline()
            fh.close()
        else:
            return []

        typere = re.search("RANCID-CONTENT-TYPE: (\w+)", firstline)
        routertype = ""
        if typere:
            routertype = typere.group(1)
        else:
            return []
        return [filename, routertype]

    def printableInterfaceList(self, device):
        """ returns a printable list of interfaces for device """
        try:
            (filename, routertype) = self.getFilename(device)
        except:
            return ["Cannot find device " + device +
                    " in rancid configuration."]

        intlist = dict()

        if routertype == "cisco":
            intlist = cisco.interfaces(filename)
        elif routertype == "force10":
            intlist = cisco.interfaces(filename)
        elif routertype == "juniper":
            intlist = juniper.interfaces(filename)
        else:
            print "Unknown type", routertype, "in", filename

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
                intstr = lastintid.group(1) + "/0" + lastintid.group(2)
            else:
                intstr = inttemp
            if unit:
                intstr = intstr + unit
            ret.append(intstr + ": " + intlist[interface])
        ret.sort()
        return ret

    def interfaceDescriptionList(self, device):
        """ returns a dict {interface: description} for all interfaces of
        device """
        try:
            (filename, routertype) = self.getFilename(device)
        except:
            return {"error": "Cannot find device " + device +
                    " in rancid configuration."}

        if routertype == "cisco":
            return cisco.interfaces(filename)
        elif routertype == "force10":
            return cisco.interfaces(filename)
        elif routertype == "juniper":
            return juniper.interfaces(filename)
        else:
            return {"error": "Unknown type " + routertype + " in " + filename}

    def interfaceAddressList(self, device, with_subnetsize=None):
        """ returns a dict {interface:{"ip": address, "ipv6": address}} for
        all interfaces of device """
        try:
            (filename, routertype) = self.getFilename(device)
        except:
            return {"error": "Cannot find device " + device +
                    " in rancid configuration."}

        if routertype == "cisco":
            return cisco.addresses(filename, with_subnetsize)
        elif routertype == "force10":
            return cisco.addresses(filename, with_subnetsize)
        elif routertype == "juniper":
            return juniper.addresses(filename, with_subnetsize)
        else:
            return {"error": "Unknown type " + routertype + " in " + filename}

    def printFilterSection(self, filename, filterstr):
        """ filters the config for filename according to filterstr and prints
        it in a nice way """
        if filename[1] == "juniper":
            sections = juniper.section(filename[0], filterstr)
            juniper.printSection(sections)
        else:
            sections = cisco.section(filename[0], ".* ".join(filterstr))
            cisco.printSection(sections)

    def printSection(self, vendor, section):
        """ prints section in a nice way """
        if vendor == "juniper":
            juniper.printSection(section)
        else:
            cisco.printSection(section)
