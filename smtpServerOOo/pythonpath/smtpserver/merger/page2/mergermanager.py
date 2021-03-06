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

from com.sun.star.ui.dialogs.WizardTravelType import FORWARD
from com.sun.star.ui.dialogs.WizardTravelType import BACKWARD
from com.sun.star.ui.dialogs.WizardTravelType import FINISH

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .mergerview import MergerView
from .mergerhandler import AddressHandler
from .mergerhandler import RecipientHandler

from smtpserver import logMessage
from smtpserver import getMessage

import traceback


class MergerManager(unohelper.Base):
    def __init__(self, ctx, wizard, model, pageid, parent):
        self._ctx = ctx
        self._wizard = wizard
        self._model = model
        self._pageid = pageid
        self._handlers = []
        tables = self._model.getTables()
        self._view = MergerView(ctx, self, parent, tables)
        address = AddressHandler(self)
        recipient = RecipientHandler(self)
        self._model.initGrids(address, recipient, tables, self.initGrids)

    @property
    def Model(self):
        return self._model

    def isHandlerEnabled(self, handler):
        if handler in self._handlers:
            self._handlers.remove(handler)
            return False
        return True
    def _disableHandler(self, handler):
        if handler not in self._handlers:
            self._handlers.append(handler)

# XWizardPage
    @property
    def PageId(self):
        return self._pageid
    @property
    def Window(self):
        return self._view.getWindow()

    def activatePage(self):
        pass

    def commitPage(self, reason):
        return True

    def canAdvance(self):
        return self._model.getRecipientCount() > 0

# MergerManager setter methods
    def initGrids(self, table, tables):
        self._view.initGrids(self)
        if table in tables:
            # TODO: We must disable the handler "ChangeAddressBook" otherwise it activates twice
            self._disableHandler('ChangeAddressBook')
            self._view.setTable(table)

    def enableAddAll(self, enabled):
        self._view.enableAddAll(enabled)

    def enableRemoveAll(self, enabled):
        self._view.enableRemoveAll(enabled)
        self._wizard.updateTravelUI()

    def setAddressBook(self, table):
        self._model.setAddressBook(table, self.initAddress)

    def initAddress(self, columns, orders):
        self._view.initAddressColumn(columns)
        self._view.initAddressOrder(columns, orders)

    def initRecipient(self, columns, orders):
        self._view.initRecipientColumn(columns)
        self._view.initRecipientOrder(columns, orders)

    def setAddressColumn(self, titles, reset):
        self._model.setAddressColumn(titles, reset)

    def setAddressOrder(self, titles):
        ascending = self._view.getAddressSort()
        self._model.setAddressOrder(titles, ascending)

    def setRecipientColumn(self, titles, reset):
        self._model.setRecipientColumn(titles, reset)

    def setRecipientOrder(self, titles):
        ascending = self._view.getRecipientSort()
        self._model.setRecipientOrder(titles, ascending)

    def changeAddress(self, selected):
        self._view.enableAdd(selected)

    def changeRecipient(self, selected, index):
        self._view.enableRemove(selected)
        if selected:
            self._model.setDocumentRecord(index +1)

    def addItem(self):
        rows = self._view.getSelectedAddress()
        self._model.addItem(rows)

    def addAllItem(self):
        rows = range(self._model.getAddressCount())
        self._model.addItem(rows)

    def removeItem(self):
        rows = self._view.getSelectedRecipient()
        self._model.removeItem(rows)

    def removeAllItem(self):
        rows = range(self._model.getRecipientCount())
        self._model.removeItem(rows)
