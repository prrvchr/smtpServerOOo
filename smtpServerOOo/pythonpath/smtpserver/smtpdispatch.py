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

from com.sun.star.frame import XNotifyingDispatch

from com.sun.star.frame.DispatchResultState import SUCCESS
from com.sun.star.frame.DispatchResultState import FAILURE

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import getPathSettings

from .datasource import DataSource

from .wizard import Wizard

from .server import ServerWizard
from .server import ServerManager

from .merger import MergerWizard

from .spooler import SpoolerManager

from .sender import SenderManager

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_server_page
from .configuration import g_server_paths
from .configuration import g_merger_page
from .configuration import g_merger_paths

from .logger import logMessage
from .logger import getMessage

import traceback


class SmtpDispatch(unohelper.Base,
                   XNotifyingDispatch):
    def __init__(self, ctx, url, parent):
        self._ctx = ctx
        self._parent = parent
        self._listeners = []
        #self._datasource = DataSource(ctx)
        print("SmtpDispatch.__init__()")

    _datasource = None

    @property
    def DataSource(self):
        return SmtpDispatch._datasource

    # XNotifyingDispatch
    def dispatchWithNotification(self, url, arguments, listener):
        print("SmtpDispatch.dispatchWithNotification() 1")
        state, result = self.dispatch(url, arguments)
        struct = 'com.sun.star.frame.DispatchResultEvent'
        notification = uno.createUnoStruct(struct, self, state, result)
        print("SmtpDispatch.dispatchWithNotification() 2")
        listener.dispatchFinished(notification)
        print("SmtpDispatch.dispatchWithNotification() 3")

    def dispatch(self, url, arguments):
        print("SmtpDispatch.dispatch() 1")
        if self.DataSource is None:
            SmtpDispatch._datasource = DataSource(self._ctx)
        state = SUCCESS
        result = None
        if url.Path == 'server':
            state, result = self._showSmtpServer()
        elif url.Path == 'spooler':
            self._showSmtpSpooler()
        elif url.Path == 'mailer':
            state, result = self._showSmtpMailer(arguments)
        elif url.Path == 'merger':
            self._showSmtpMerger()
        return state, result
        print("SmtpDispatch.dispatch() 2")

    def addStatusListener(self, listener, url):
        pass

    def removeStatusListener(self, listener, url):
        pass

    def _showSmtpServer(self):
        try:
            print("_showSmtpServer()")
            state = FAILURE
            email = None
            msg = "Wizard Loading ..."
            wizard = Wizard(self._ctx, g_server_page, True, self._parent)
            manager = ServerManager(self._ctx, wizard, self.DataSource)
            controller = ServerWizard(self._ctx, manager)
            arguments = (g_server_paths, controller)
            wizard.initialize(arguments)
            msg += " Done ..."
            if wizard.execute() == OK:
                state = SUCCESS
                email = manager.Model.Email
                msg +=  " Retrieving SMTP configuration OK..."
            wizard.DialogWindow.dispose()
            wizard.DialogWindow = None
            print(msg)
            logMessage(self._ctx, INFO, msg, 'SmtpDispatch', '_showSmtpServer()')
            return state, email
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _showSmtpSpooler(self):
        try:
            print("SmtpDispatch._showSmtpSpooler() 1")
            manager = SpoolerManager(self._ctx, self.DataSource, self._parent)
            if manager.execute() == OK:
                print("SmtpDispatch._showSmtpSpooler() 2")
            manager.dispose()
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _showSmtpMailer(self, arguments):
        try:
            state = FAILURE
            for argument in arguments:
                if argument.Name == 'Path':
                    path = argument.Value
                    break
            else:
                path = getPathSettings(self._ctx).Work
            sender = SenderManager(self._ctx, path)
            url = sender.getDocumentUrl()
            if url is not None:
                if sender.showDialog(self.DataSource, self._parent, url) == OK:
                    state = SUCCESS
                    path = sender.Mailer.Model.Path
                sender.dispose()
            return state, path
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _showSmtpMerger(self):
        try:
            print("_showSmtpMerger()")
            msg = "Wizard Loading ..."
            wizard = Wizard(self._ctx, g_merger_page, True, self._parent)
            controller = MergerWizard(self._ctx, wizard)
            arguments = (g_merger_paths, controller)
            wizard.initialize(arguments)
            msg += " Done ..."
            if wizard.execute() == OK:
                msg +=  " Merging SMTP email OK..."
            wizard.DialogWindow.dispose()
            wizard.DialogWindow = None
            print(msg)
            logMessage(self._ctx, INFO, msg, 'SmtpDispatch', '_showSmtpMerger()')
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)
