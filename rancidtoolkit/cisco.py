#!/usr/bin/env python
#
# Written by Marcus Stoegbauer <ms@man-da.de>

"""
Cisco specific parsing of configuration files
"""

import re


def section(filename, section):
    """returns a list with all configuration within section from filename"""
    fh = open(filename)
    ret = []
    insec = False
    spaces = ""
    secret = []

    for line in fh:
        line = line[:-1]
        if re.match("^!", line):
            continue
        reobj = re.match("^(\s*)" + section, line, flags=re.I)
        if reobj:                       # match on section
            if insec:                     # already in section
                ret = ret + [secret]        # save the old section
            spaces = reobj.group(1)       # start a new section
            insec = True
            secret = []

        if insec:  # already in section
            secreobj = re.match("^" + spaces + "[^\s]", line)
            # not first line of section (which always matches the pattern) and
            if len(secret) > 0 and secreobj:
                # match old section is over, save section
                ret = ret + [secret]
                insec = False
            secret = secret + [line]      # save to current section
    return ret


def filterSection(section, filter):
    """filters section according to regexp terms in filter and outputs a list
    of all matched entries """
    ret = []
    for sec in section:
        secret = []
        for line in sec:
            line = line.lstrip()
            if re.match(filter, line, re.I):
                secret = secret + [line]
        ret = ret + [secret]
    return ret


def filterConfig(filename, secstring, filter):
    """extracts sections secstring from the entire configuration in filename
    and filters against regexp filter returns a list of all matches
    """
    return filterSection(section(filename, secstring), filter)


def interfaces(filename):
    """find interfaces and matching descriptions from filename and return dict
    with interface=>descr """
    parseresult = filterConfig(filename, "interface",
                               "^interface|^description")
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
            if not skipdescr:
                reobj = re.match("description (.*)", line)
                if reobj:
                    ret[intret] = reobj.group(1)
                else:
                    ret[intret] = ""
    return ret


def addresses(filename):
    """find ip addresses configured on all interfaces from filename and return
    dict with interface=>(ip=>address, ipv6=>address)"""
    parseresult = filterConfig(filename, "interface",
                               "^interface|^ip address|^ipv6 address")
    ret = dict()
    for sec in parseresult:
        intret = ""
        for line in sec:
            reobj = re.match("interface (.*)", line)
            if reobj:
                intret = reobj.group(1)
            if intret:
                # FIXME: exclude interfaces with shutdown configured
                reobj = re.match("(ip|ipv6) address (.*)", line)
                if reobj:
                    if not intret in ret:
                        ret[intret] = dict()
                    ret[intret].update({reobj.group(1):
                                        re.split('[\/ ]', reobj.group(2))[0]})
    return ret


def printSection(section):
    """prints section in a nice way"""
    if type(section) == list:
        for line in section:
            printSection(line)
    else:
        print section
