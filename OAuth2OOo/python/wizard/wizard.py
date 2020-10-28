#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.ui.dialogs import XWizard
from com.sun.star.lang import XInitialization

from com.sun.star.lang import IllegalArgumentException
from com.sun.star.util import InvalidStateException
from com.sun.star.container import NoSuchElementException

from unolib import getDialog
from unolib import getInterfaceTypes

from .wizardmanager import WizardManager
from .wizardhandler import DialogHandler, ItemHandler

from .configuration import g_extension

from .logger import getMessage
g_message = 'wizard'

import traceback


class Wizard(unohelper.Base,
             XWizard,
             XInitialization):
    def __init__(self, ctx, auto=-1, resize=False, parent=None):
        try:
            self.ctx = ctx
            self._helpUrl = ''
            self._manager = WizardManager(self.ctx, auto, resize)
            dialog = DialogHandler(self.ctx, self._manager)
            self._dialog = getDialog(self.ctx, g_extension, 'Wizard', dialog, parent)
            item = ItemHandler(self.ctx, self._dialog, self._manager)
            self._manager.initWizard(self._dialog, item)
            print("Wizard.__init__()")
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    @property
    def HelpURL(self):
        return self._helpUrl
    @HelpURL.setter
    def HelpURL(self, url):
        self._helpUrl = url
        self._dialog.getControl('CommandButton5').Model.Enabled = url != ''
    @property
    def DialogWindow(self):
        return self._dialog

    # XInitialization
    def initialize(self, arguments):
        if not isinstance(arguments, tuple) or len(arguments) != 2:
            raise self._getIllegalArgumentException(0, 101)
        paths, controller = arguments
        if not isinstance(paths, tuple) or len(paths) < 1:
            raise self._getIllegalArgumentException(0, 102)
        unotype = uno.getTypeByName('com.sun.star.ui.dialogs.XWizardController')
        if unotype not in getInterfaceTypes(controller):
            raise self._getIllegalArgumentException(0, 103)
        self._manager.setPaths(paths)
        self._manager._controller = controller

    # XWizard
    def getCurrentPage(self):
        return self._manager.getCurrentPage()

    def enableButton(self, button, enabled):
        self._manager.enableButton(self._dialog, button, enabled)

    def setDefaultButton(self, button):
        self._manager.setDefaultButton(self._dialog, button)

    def travelNext(self):
        return self._manager.travelNext(self._dialog)

    def travelPrevious(self):
        return self._manager.travelPrevious(self._dialog)

    def enablePage(self, page, enabled):
        if page == self._manager._model.getCurrentPageId():
            raise self._getInvalidStateException(111)
        path = self._manager.getCurrentPath()
        if page not in path:
            raise self._getNoSuchElementException(112)
        index = path.index(page)
        self._manager.enablePage(index, enabled)

    def updateTravelUI(self):
        self._manager.updateTravelUI(self._dialog)

    def advanceTo(self, page):
        return self._manager.advanceTo(self._dialog, page)

    def goBackTo(self, page):
        return self._manager.goBackTo(self._dialog, page)

    def activatePath(self, index, final):
        if not self._manager.isMultiPaths():
            return
        if index not in range(self._manager.getPathsLength()):
            raise self._getNoSuchElementException(121)
        path = self._manager.getPath(index)
        page = self._manager._model.getCurrentPageId()
        if page != -1 and page not in path:
            raise self._getInvalidStateException(122)
        self._manager.activatePath(index, final)

    # XExecutableDialog -> XWizard
    def setTitle(self, title):
        self._dialog.setTitle(title)

    def execute(self):
        return self._manager.executeWizard(self._dialog)

    # Private methods
    def _getIllegalArgumentException(self, position, code):
        e = IllegalArgumentException()
        e.ArgumentPosition = position
        e.Message = getMessage(self.ctx, g_message, code)
        e.Context = self
        return e

    def _getInvalidStateException(self, code):
        e = InvalidStateException()
        e.Message = getMessage(self.ctx, g_message, code)
        e.Context = self
        return e

    def _getNoSuchElementException(self, code):
        e = NoSuchElementException()
        e.Message = getMessage(self.ctx, g_message, code)
        e.Context = self
        return e
