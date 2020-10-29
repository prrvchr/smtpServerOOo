#!
# -*- coding: utf_8 -*-

import uno
import unohelper

from com.sun.star.awt import XDialogEventHandler
from com.sun.star.awt import XItemListener

import traceback


class DialogHandler(unohelper.Base,
                    XDialogEventHandler):
    def __init__(self, manager):
        self._manager = manager

    # XDialogEventHandler
    def callHandlerMethod(self, dialog, event, method):
        handled = False
        if method == 'Help':
            handled = True
        elif method == 'Previous':
            self._manager.travelPrevious(dialog)
            handled = True
        elif method == 'Next':
            self._manager.travelNext(dialog)
            handled = True
        elif method == 'Finish':
            self._manager.doFinish(dialog)
            handled = True
        return handled

    def getSupportedMethodNames(self):
        return ('Help', 'Previous', 'Next', 'Finish')


class ItemHandler(unohelper.Base,
                  XItemListener):
    def __init__(self, dialog, manager):
        self._dialog = dialog
        self._manager = manager

    # XItemListener
    def itemStateChanged(self, event):
        page = event.ItemId
        self._manager.changeRoadmapStep(self._dialog, page)

    def disposing(self, event):
        pass
