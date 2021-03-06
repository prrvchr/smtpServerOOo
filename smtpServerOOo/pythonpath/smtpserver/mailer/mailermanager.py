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

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import createService
from unolib import executeShell

from .mailermodel import MailerModel
from .mailerview import MailerView

from smtpserver import logMessage
from smtpserver import getMessage
g_message = 'mailermanager'

import time
from threading import Condition
import traceback


class MailerManager(unohelper.Base):
    def __init__(self, ctx, manager, datasource, parent, path, recipients=()):
        self._ctx = ctx
        self._lock = Condition()
        self._manager = manager
        self._model = MailerModel(ctx, datasource, path)
        self._view = MailerView(ctx, self, parent)
        self._model.getSenders(self.initSenders)
        self._view.setRecipient(recipients)

    @property
    def Model(self):
        return self._model

    def initSenders(self, senders):
        with self._lock:
            if not self._view.isDisposed():
                # Set the Senders ListBox
                self._view.setSenders(senders)
                self._canSend()

    def initView(self, document):
        with self._lock:
            if not self._view.isDisposed():
                self._model.setUrl(document.URL)
                # Set the Save Subject CheckBox and if needed the Subject TextField
                state = self._model.getDocumentUserProperty(document, 'SaveSubject')
                self._view.setSaveSubject(int(state))
                if state:
                    subject = self._model.getDocumentSubject(document)
                    self._view.setSubject(subject)
                # Set the Save Attachments CheckBox and if needed the Attachments ListBox
                state = self._model.getDocumentUserProperty(document, 'SaveAttachments')
                self._view.setSaveAttachments(int(state))
                if state:
                    attachments = self._model.getDocumentAttachemnts(document, 'Attachments')
                    self._view.setAttachments(attachments)
                # Set the Attachment As PDF CheckBox
                state = self._model.getDocumentUserProperty(document, 'AttachmentAsPdf')
                self._view.setAttachmentAsPdf(int(state))
                # Set the View Document in HTML CommandButton
                self._view.enableButtonViewHtml()
                self._canSend()
            document.close(True)

    def show(self):
        return self._view.execute()

    def dispose(self):
        with self._lock:
            self._view.dispose()

    def addSender(self, sender):
        self._view.addSender(sender)
        self._canSend()

    def removeSender(self):
        # TODO: button 'RemoveSender' must be deactivated to avoid multiple calls  
        self._view.enableRemoveSender(False)
        sender, position = self._view.getSelectedSender()
        status = self.Model.removeSender(sender)
        if status == 1:
            self._view.removeSender(position)
            self._canSend()

    def editRecipient(self, email, exist):
        enabled = self._model.validateRecipient(email, exist)
        self._view.enableAddRecipient(enabled)
        self._view.enableRemoveRecipient(exist)

    def addRecipient(self):
        self._view.addRecipient()
        self._canSend()

    def removeRecipient(self):
        self._view.removeRecipient()
        self._canSend()

    def enterRecipient(self, email, exist):
        if self._model.validateRecipient(email, exist):
            self._view.addToRecipient(email)
            self._canSend()

    def viewHtmlDocument(self):
        document = self._model.getDocument()
        url = self._model.saveDocumentAs(document, 'html')
        document.close(True)
        if url is not None:
            executeShell(self._ctx, url)

    def viewPdfAttachment(self):
        attachment = self._view.getSelectedAttachment()
        document= self._model.getDocument(attachment)
        url = self._model.saveDocumentAs(document, 'pdf')
        if url is not None:
            executeShell(self._ctx, url)

    def addAttachments(self):
        title = self._model.getFilePickerTitle()
        path = self._model.Path
        attachments, path = self._view.getAttachmentUrls(title, path)
        self._model.Path = path
        if len(attachments) > 0:
            pdf = self._view.getAttachmentAsPdf()
            urls = self._model.parseAttachments(attachments, pdf)
            self._view.addAttachments(urls)

    def changeAttachments(self, enabled, attachment):
        self._view.enableRemoveAttachments(enabled)
        enabled &= attachment.endswith('#pdf')
        self._view.enableButtonViewPdf(enabled)

    def removeAttachments(self):
        self._view.removeAttachments()

    def changeSender(self, enabled):
        self._view.enableRemoveSender(enabled)

    def changeRecipient(self):
        self._view.enableRemoveRecipient(True)

    def changeSubject(self):
        self._canSend()

    def sendDocument(self):
        subject = self._view.getSubject()
        attachments = self._view.getAttachments()
        self._saveDocumentProperty(subject, attachments)
        sender = self._view.getSender()
        recipients = self._view.getRecipients()
        url = self._model.getUrl()
        service = 'com.sun.star.mail.MailServiceSpooler'
        spooler = createService(self._ctx, service)
        id = spooler.addJob(sender, subject, url, recipients, attachments)

# MailerManager private methods
    def _canSend(self):
        enabled = all((self._view.isSenderValid(),
                       self._view.isRecipientsValid(),
                       self._view.isSubjectValid()))
        self._manager.updateUI(enabled)

    def _saveDocumentProperty(self, subject, attachments):
        document = self._model.getDocument()
        state = self._view.getSaveSubject()
        self._model.setDocumentUserProperty(document, 'SaveSubject', state)
        if state:
            self._model.setDocumentSubject(document, subject)
        state = self._view.getSaveAttachments()
        self._model.setDocumentUserProperty(document, 'SaveAttachments', state)
        if state:
            self._model.setDocumentAttachments(document, 'Attachments', attachments)
        state = self._view.getAttachmentAsPdf()
        self._model.setDocumentUserProperty(document, 'AttachmentAsPdf', state)
        document.store()
        document.close(True)
