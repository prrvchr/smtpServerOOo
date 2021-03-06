#!
# -*- coding: utf_8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

import uno
import unohelper

from unolib import createService

from collections import OrderedDict
import traceback


class ColumnModel(unohelper.Base):
    def __init__(self, ctx):
        self._width = 0
        self._factor = 1
        service = 'com.sun.star.awt.grid.DefaultGridColumnModel'
        self._model = createService(ctx, service)

# ColumnModel setter methods
    def initColumnModel(self, rowset, widths, titles, width, factor=1):
        self._width = width
        self._factor = factor
        # TODO: First we need to clear the default columns created 
        # TODO: when assigning GridDataModel.ColumnCount
        for index in range(self._model.getColumnCount() -1, -1, -1):
            self._model.removeColumn(index)
        # TODO: ColumnWidth should be assigned after all columns have 
        # TODO: been added to the GridColumnModel
        if widths:
            for name in widths:
                title = titles[name]
                self._createColumn(rowset, name, title)
            self._setSavedColumnWidth(widths)
        else:
            total = 0
            for name, title in titles.items():
                total += len(title)
                self._createColumn(rowset, name, title)
            self._setDefaultColumnWidth(total)

    def setColumnModel(self, rowset, titles, reset):
        total = 0
        added = False
        for index in range(self._model.getColumnCount() -1, -1, -1):
            column = self._model.getColumn(index)
            total += len(column.Title)
            if column.Identifier not in titles:
                self._model.removeColumn(index)
        if reset:
            total = 0
            self._model.removeColumn(0)
        columns = [column.Identifier for column in self._model.getColumns()]
        for name, title in titles.items():
            if name not in columns:
                total += len(title)
                self._createColumn(rowset, name, title)
                added = True
        if added:
            self._setDefaultColumnWidth(total)

# ColumnModel getter methods
    def getColumnModel(self):
        return self._model

    def getColumnWidth(self):
        widths = OrderedDict()
        for column in self._model.getColumns():
            widths[column.Identifier] = column.ColumnWidth
        return widths

# ColumnModel private methods
    def _createColumn(self, rowset, name, title):
        column = self._model.createColumn()
        column.Title = title
        column.Identifier = name
        index = rowset.findColumn(name)
        column.DataColumnIndex = index -1
        self._model.addColumn(column)

    def _setSavedColumnWidth(self, widths):
        for column in self._model.getColumns():
            name = column.Identifier
            flex = len(column.Title)
            column.ColumnWidth = widths[name]
            column.MinWidth = flex * 5
            if self._factor == 1:
                column.Flexibility = flex
            else:
                column.Flexibility = 0

    def _setDefaultColumnWidth(self, total):
        sum = 0
        last = self._model.getColumnCount() -1
        for column in self._model.getColumns():
            flex = len(column.Title)
            index = column.Index
            width = self._getColumnWidth(flex, total, last, index, sum)
            column.ColumnWidth = width
            column.MinWidth = flex * 5
            if self._factor == 1:
                column.Flexibility = flex
            else:
                column.Flexibility = 0
            sum += width

    def _getColumnWidth(self, flex, total, last, index, sum):
        if index == last:
            # TODO: To display a Grid without a scroll bar, 1 must be subtracted
            width = (self._width * self._factor) - sum -1
        else:
            width = self._width * self._factor * flex // total
        return width
