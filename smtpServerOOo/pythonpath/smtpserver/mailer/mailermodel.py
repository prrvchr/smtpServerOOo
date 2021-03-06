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

from com.sun.star.document.MacroExecMode import ALWAYS_EXECUTE_NO_WARN

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import getUrl
from unolib import getStringResource
from unolib import getPropertyValueSet
from unolib import getDesktop
from unolib import getPathSettings
from unolib import getUrlTransformer
from unolib import parseUrl

from smtpserver import g_identifier
from smtpserver import g_extension

from smtpserver import logMessage
from smtpserver import getMessage

import validators
import traceback


class MailerModel(unohelper.Base):
    def __init__(self, ctx, datasource, path):
        self._ctx = ctx
        self._datasource = datasource
        self._path = path
        self._url = None
        self._stringResource = getStringResource(ctx, g_identifier, g_extension)

    @property
    def DataSource(self):
        return self._datasource
    @property
    def Path(self):
        return self._path
    @Path.setter
    def Path(self, path):
        self._path = path

    def resolveString(self, resource):
        return self._stringResource.resolveString(resource)

    def getUrl(self):
        return self._url

    def setUrl(self, url):
        self._url = url

    def getSenders(self, *args):
        self.DataSource.getSenders(*args)

    def getDocument(self, url=None):
        if url is None:
            url = self._url
        properties = {'Hidden': True, 'MacroExecutionMode': ALWAYS_EXECUTE_NO_WARN}
        descriptor = getPropertyValueSet(properties)
        document = getDesktop(self._ctx).loadComponentFromURL(url, '_blank', 0, descriptor)
        return document

    def getDocumentSubject(self, document):
        return document.DocumentProperties.Subject

    def setDocumentSubject(self, document, subject):
        document.DocumentProperties.Subject = subject

    def removeSender(self, sender):
        return self.DataSource.removeSender(sender)

    def saveDocumentAs(self, document, format):
        url = None
        name, extension = self._getNameAndExtension(document.Title)
        filter = self._getDocumentFilter(extension, format)
        if filter is not None:
            temp = getPathSettings(self._ctx).Temp
            url = '%s/%s.%s' % (temp, name, format)
            descriptor = getPropertyValueSet({'FilterName': filter, 'Overwrite': True})
            document.storeToURL(url, descriptor)
            url = getUrl(self._ctx, url)
            if url is not None:
                url = url.Main
        return url

    def parseAttachments(self, attachments, pdf):
        urls = []
        transformer = getUrlTransformer(self._ctx)
        for attachment in attachments:
            url = self._parseAttachment(transformer, attachment, pdf)
            urls.append(url)
        return tuple(urls)

    def validateRecipient(self, email, exist):
        return all((self._isEmailValid(email), not exist))

# MailerModel StringRessoure methods
    def getFilePickerTitle(self):
        resource = self._getFilePickerTitleResource()
        title = self.resolveString(resource)
        return title

    def getDocumentUserProperty(self, document, name):
        resource = self._getPropertyResource(name)
        state = self._getDocumentUserProperty(document, resource)
        return state

    def getDocumentAttachemnts(self, document, name):
        resource = self._getPropertyResource(name)
        attachments = self._getDocumentAttachments(document, resource)
        return attachments

    def setDocumentUserProperty(self, document, name, value):
        resource = self._getPropertyResource(name)
        self._setDocumentUserProperty(document, resource, value)

    def setDocumentAttachments(self, document, name, value):
        resource = self._getPropertyResource(name)
        self._setDocumentAttachments(document, resource, value)

# MailerModel StringRessoure private methods
    def _getFilePickerTitleResource(self):
        return 'Mailer.FilePicker.Title'

    def _getPropertyResource(self, name):
        return 'Mailer.Document.Property.%s' % name

# MailerModel private methods
    def _getDocumentUserProperty(self, document, resource, default=True):
        name = self.resolveString(resource)
        properties = document.DocumentProperties.UserDefinedProperties
        if properties.PropertySetInfo.hasPropertyByName(name):
            value = properties.getPropertyValue(name)
        else:
            value = default
        return value

    def _getDocumentAttachments(self, document, resource, default=''):
        attachments = ()
        value = self._getDocumentUserProperty(document, resource, default)
        if len(value):
            attachments = tuple(value.split('|'))
        return attachments

    def _setDocumentAttachments(self, document, resource, values):
        value = '|'.join(values)
        self._setDocumentUserProperty(document, resource, value)

    def _setDocumentUserProperty(self, document, resource, value):
        name = self.resolveString(resource)
        properties = document.DocumentProperties.UserDefinedProperties
        if properties.PropertySetInfo.hasPropertyByName(name):
            properties.setPropertyValue(name, value)
        else:
            properties.addProperty(name,
            uno.getConstantByName("com.sun.star.beans.PropertyAttribute.MAYBEVOID") +
            uno.getConstantByName("com.sun.star.beans.PropertyAttribute.BOUND") +
            uno.getConstantByName("com.sun.star.beans.PropertyAttribute.REMOVABLE") +
            uno.getConstantByName("com.sun.star.beans.PropertyAttribute.MAYBEDEFAULT"),
            value)

    def _isEmailValid(self, email):
        if validators.email(email):
            return True
        return False

    def _parseAttachment(self, transformer, attachment, pdf):
        url = parseUrl(transformer, attachment)
        if pdf:
            self._addPdfMark(url)
        return transformer.getPresentation(url, False)

    def _addPdfMark(self, url):
        name, extension = self._getNameAndExtension(url.Name)
        if self._hasPdfFilter(extension):
            url.Complete += '#pdf'

    def _getNameAndExtension(self, filename):
        part1, sep, part2 = filename.rpartition('.')
        if sep:
            name, extension = part1, part2
        else:
            name, extension = part2, part1
        return name, extension

    def _hasPdfFilter(self, extension):
        filter = self._getDocumentFilter(extension, 'pdf')
        return filter is not None

    def _getDocumentFilter(self, extension, format):
        if extension == 'odt':
            filters = {'pdf': 'writer_pdf_Export', 'html': 'XHTML Writer File'}
        elif extension == 'ods':
            filters = {'pdf': 'calc_pdf_Export', 'html': 'XHTML Calc File'}
        elif extension == 'odp':
            filters = {'pdf': 'impress_pdf_Export', 'html': 'impress_html_Export'}
        elif extension == 'odg':
            filters = {'pdf': 'draw_pdf_Export', 'html': 'draw_html_Export'}
        else:
            filters = {}
        filter = filters.get(format, None)
        return filter
