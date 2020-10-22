#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.auth import XRestDataParser

from unolib import getNamedValue
from unolib import KeyMap


class DataParser(unohelper.Base,
                 XRestDataParser):
    def __init__(self, ctx):
        self.ctx = ctx

    def parseResponse(self, response):
        data = KeyMap()
        #for key, value in pairs:
        #    if value is None:
        #        continue
        #    if key in self.keys:
        #        map = self.map.getValue(key)
        #        k = map.getValue('Map')
        #        v = self.provider.transform(k, value)
        #        data.setValue(k, v)
        print("DataParser.parseResponse() %s" % response)
        return data