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

import unohelper

from com.sun.star.awt import XContainerWindowEventHandler

from com.sun.star.awt.Key import RETURN

import traceback


class WindowHandler(unohelper.Base,
                    XContainerWindowEventHandler):
    def __init__(self, manager):
        self._manager = manager

    # XContainerWindowEventHandler
    def callHandlerMethod(self, window, event, method):
        try:
            handled = False
            # TODO: During WizardPage initialization the listener must be disabled...
            enabled = self._manager.isHandlerEnabled(method)
            if method == 'ChangeDataSource':
                print("MergerHandler.callHandlerMethod() ChangeDataSource *************** %s" % enabled)
                if enabled:
                    control = event.Source
                    datasource = control.getSelectedItem()
                    self._manager.changeDataSource(datasource)
                handled = True
            elif method == 'ChangeTable':
                print("MergerHandler.callHandlerMethod() ChangeTable *************** %s" % enabled)
                if enabled:
                    control = event.Source
                    table = control.getSelectedItem()
                    self._manager.changeTables(table)
                handled = True
            elif method == 'ChangeColumn':
                print("MergerHandler.callHandlerMethod() ChangeColumn *************** %s" % enabled)
                if enabled:
                    control = event.Source
                    selected = control.getSelectedItemPos() != -1
                    column = control.getSelectedItem()
                    self._manager.changeColumns(selected, column)
                handled = True
            elif method == 'ChangeQuery':
                print("MergerHandler.callHandlerMethod() ChangeQuery *************** %s" % enabled)
                if enabled:
                    control = event.Source
                    query = control.getText()
                    self._manager.changeQuery(query)
                handled = True
            elif method == 'ChangeEmail':
                print("PageHandler.callHandlerMethod() ChangeEmail ***************")
                control = event.Source
                imax = control.ItemCount -1
                position = control.getSelectedItemPos()
                self._manager.changeEmail(imax, position)
                handled = True
            elif method == 'ChangeIndex':
                print("PageHandler.callHandlerMethod() ChangePrimaryKey ***************")
                control = event.Source
                enabled = control.getSelectedItemPos() != -1
                self._manager.changeIndex(enabled)
                handled = True
            elif method == 'NewDataSource':
                self._manager.newDataSource()
                handled = True
            elif method == 'AddEmail':
                print("PageHandler.callHandlerMethod() AddEmail ***************")
                self._manager.addEmail()
                handled = True
            elif method == 'RemoveEmail':
                print("PageHandler.callHandlerMethod() RemoveEmail ***************")
                self._manager.removeEmail()
                handled = True
            elif method == 'MoveBefore':
                print("PageHandler.callHandlerMethod() MoveBefore ***************")
                self._manager.moveBefore()
                handled = True
            elif method == 'MoveAfter':
                print("PageHandler.callHandlerMethod() MoveAfter ***************")
                self._manager.moveAfter()
                handled = True
            elif method == 'AddIndex':
                self._manager.addIndex()
                handled = True
            elif method == 'RemoveIndex':
                self._manager.removeIndex()
                handled = True
            elif method == 'EditQuery':
                print("PageHandler.callHandlerMethod() EditQuery ***************")
                control = event.Source
                query = control.getText().strip()
                exist = query in control.getItems()
                self._manager.editQuery(query, exist)
                handled = True
            elif method == 'EnterQuery':
                if event.KeyCode == RETURN:
                    print("PageHandler.callHandlerMethod() EnterQuery ***************")
                    control = event.Source
                    query = control.getText().strip()
                    exist = query in control.getItems()
                    self._manager.enterQuery(query, exist)
                handled = True
            elif method == 'AddQuery':
                self._manager.addQuery()
                handled = True
            elif method == 'RemoveQuery':
                self._manager.removeQuery()
                handled = True
            return handled
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    def getSupportedMethodNames(self):
        return ('ChangeDataSource',
                'ChangeTable',
                'ChangeColumn',
                'ChangeQuery',
                'ChangeEmail',
                'ChangeIndex',
                'NewDataSource',
                'AddEmail',
                'RemoveEmail',
                'MoveBefore',
                'MoveAfter',
                'AddIndex',
                'RemoveIndex',
                'EditQuery',
                'EnterQuery',
                'AddQuery',
                'RemoveQuery')
