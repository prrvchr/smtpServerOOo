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

from com.sun.star.uno import Exception as UnoException

from com.sun.star.ui.dialogs.WizardTravelType import FORWARD
from com.sun.star.ui.dialogs.WizardTravelType import BACKWARD
from com.sun.star.ui.dialogs.WizardTravelType import FINISH
from com.sun.star.ui.dialogs.ExecutableDialogResults import OK
from com.sun.star.mail.MailServiceType import SMTP
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from .servermodel import ServerModel
from .serverview import ServerView
from .send import SendView

from unolib import createService
from unolib import getDialog

from smtpserver import logMessage
from smtpserver import getMessage
g_message = 'pagemanager'


import traceback


class ServerManager(unohelper.Base):
    def __init__(self, ctx, wizard, datasource, email=''):
        self._ctx = ctx
        self._search = True
        self._loaded = False
        self._connected = False
        self._wizard = wizard
        self._model = ServerModel(ctx, datasource, email)
        self._views = {}
        self._dialog = None
        self._refresh = False
        self._new = False
        self._updated = False
        self._enabled = True
        print("PageManager.__init__() %s" % self._model.Email)

    @property
    def Model(self):
        return self._model
    @property
    def View(self):
        pageid = self.Wizard.getCurrentPage().PageId
        return self.getView(pageid)
    @property
    def Wizard(self):
        return self._wizard

    @property
    def HandlerEnabled(self):
        return self._enabled
    def disableHandler(self):
        self._enabled = False
    def enableHandler(self):
        self._enabled = True

    def getPageStep(self, id):
        return self._model.getPageStep(id)

    def getView(self, pageid):
        if pageid in self._views:
            return self._views[pageid]
        print("PageManager.getView ERROR **************************")
        return None

    def getWizard(self):
        return self.Wizard

    def initPage(self, pageid, window):
        view = ServerView(self._ctx, window)
        self._views[pageid] = view
        if pageid == 1:
            view.initPage1(self.Model)

    def activatePage(self, pageid):
        if pageid == 1:
            self._loaded = False
            self.Wizard.activatePath(1, False)
        elif pageid == 2:
            self._setPageTitle(pageid, 0)
            self.Wizard.activatePath(1, False)
            self.Wizard.enablePage(1, False)
            self.getView(pageid).activatePage2(self.Model)
            self._refresh = True
            self._loaded = False
            self.Model.getSmtpConfig(self.updatePage2, self.updateModel)
        elif pageid == 3:
            self.setPageTitle(pageid)
            if self._refresh:
                self._refresh = False
                self._loaded = True
                self.getView(pageid).activatePage3(self.Model)
        elif pageid == 4:
            self._connected = False
            self.getView(pageid).activatePage4(self.Model)
            context = self.getView(3).getConnectionContext(self.Model)
            authenticator = self.getView(3).getAuthenticator()
            self.Model.smtpConnect(context, authenticator,
                                   self.updatePage4, self.updatePageStep)

    def updatePage2(self, value, offset=0):
        if self.Wizard.DialogWindow is not None:
            self.getView(2).updatePage2(self.Model, value, offset)

    def updatePage4(self, value):
        if self.Wizard.DialogWindow is not None:
            self.getView(4).updatePage4(self.Model, value)

    def updateModel(self, user, servers, offline):
        print("PageManager.updateModel() 1: %s" % self.Wizard.getCurrentPage().PageId)
        if self.Wizard.DialogWindow is not None:
            # TODO: The order of assignment is important (ie: the user before the servers)
            self.Model.User = user
            self.Model.Servers = servers
            self.Model.Offline = offline
            self._search = False
            print("PageManager.updateModel() 2")
            self.setPageTitle(2)
            self.Wizard.enablePage(1, True)
            self.Wizard.activatePath(self._getActivePath(), True)
            self.Wizard.updateTravelUI()

    def updatePageStep(self, step):
        if self.Wizard.DialogWindow is not None:
            self._connected = step > 3
            self.getView(4).setPage4Step(step)
            self.Wizard.updateTravelUI()

    def canAdvancePage(self, pageid):
        advance = False
        if pageid == 1:
            advance = self._isEmailValid(pageid)
        elif pageid == 2:
            advance = not self._search
        elif pageid == 3:
            advance = all((self._loaded,
                           self._isHostValid(pageid),
                           self._isPortValid(pageid),
                           self._isLoginValid(pageid),
                           self._isPasswordValid(pageid)))
        elif pageid == 4:
            advance = self._connected
        return advance

    def commitPage(self, pageid, reason):
        if pageid == 1:
            self.Model.Email = self.View.getEmail()
        elif pageid == 2:
            self._search = True
        elif pageid == 3:
            if reason == FINISH:
                self._saveConfiguration()
        elif pageid == 4:
            if reason == FINISH:
               self._saveConfiguration()
        return True

    def setPageTitle(self, pageid):
        self._setPageTitle(pageid, self.Model.Offline)

    def updateTravelUI(self):
        self.Wizard.updateTravelUI()

    def changeConnection(self, control):
        index = self.View.getControlIndex(control)
        self.View.setConnectionSecurity(self.Model, index)

    def changeAuthentication(self, control):
        index = self.View.getControlIndex(control)
        if index == 0:
            self.View.enableLogin(False)
            self.View.enablePassword(False)
        elif index == 3:
            self.View.enableLogin(True)
            self.View.enablePassword(False)
        else:
            self.View.enableLogin(True)
            self.View.enablePassword(True)
        self.View.setAuthenticationSecurity(self.Model, index)
        self.updateTravelUI()

    def previousServerPage(self):
        self.Model.previousServerPage(self.View.getServer())
        self.View.updatePage3(self.Model)

    def nextServerPage(self):
        self.Model.nextServerPage(self.View.getServer())
        self.View.updatePage3(self.Model)

    def sendMail(self):
        parent = self.Wizard.DialogWindow.getPeer()
        self._dialog = SendView(self._ctx, self, parent)
        if self._dialog.execute() == OK:
            self.updatePage4(0)
            self.getView(4).setPage4Step(1)
            recipient = self._dialog.getRecipient()
            subject = self._dialog.getSubject()
            message = self._dialog.getMessage()
            context = self.getView(3).getConnectionContext(self.Model)
            authenticator = self.getView(3).getAuthenticator()
            self.Model.smtpSend(context, authenticator,
                                self.Model.Email, recipient, subject, message,
                                self.updatePage4, self.updatePageStep)
        self._dialog.dispose()
        self._dialog = None

    def updateDialog(self):
        self._dialog.enableButtonSend(self.Model)

    def _saveConfiguration(self):
        user, server = self.getView(3).getConfiguration(self.Model)
        self.Model.saveConfiguration(user, server)

    def _setPageTitle(self, pageid, offline):
        title = self.getView(pageid).getPageTitle(self.Model, pageid, offline)
        self.Wizard.setTitle(title)

    def _getActivePath(self):
        return self.Model.Offline

    def _isEmailValid(self, pageid):
        return self.getView(pageid).isEmailValid(self.Model.isEmailValid)

    def _isHostValid(self, pageid):
        return self.getView(pageid).isHostValid(self.Model.isHostValid)

    def _isPortValid(self, pageid):
        return self.getView(pageid).isPortValid(self.Model.isPortValid)

    def _isLoginValid(self, pageid):
        return self.getView(pageid).isLoginValid(self.Model.isStringValid)

    def _isPasswordValid(self, pageid):
        return self.getView(pageid).isPasswordValid(self.Model.isStringValid)
