#!
# -*- coding: utf_8 -*-

from com.sun.star.logging.LogLevel import SEVERE
from com.sun.star.logging.LogLevel import WARNING
from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import CONFIG
from com.sun.star.logging.LogLevel import FINE
from com.sun.star.logging.LogLevel import FINER
from com.sun.star.logging.LogLevel import FINEST
from com.sun.star.logging.LogLevel import ALL
from com.sun.star.logging.LogLevel import OFF

from unolib import getConfiguration
from unolib import getStringResource

from .configuration import g_identifier

g_stringResource = {}
g_logger = None
g_debugMode = False
g_logSettings = None


def setDebugMode(ctx, mode):
    if mode:
        _setDebugModeOn(ctx)
    else:
        _setDebugModeOff(ctx)
    _setDebugMode(mode)

def isDebugMode():
    return g_debugMode

def getMessage(ctx, fileresource, resource, format=()):
    msg = _getResource(ctx, fileresource).resolveString(resource)
    if format:
        msg = msg % format
    return msg

def logMessage(ctx, level, msg, cls=None, method=None):
    logger = _getLogger(ctx)
    if logger.isLoggable(level):
        if cls is None or method is None:
            logger.log(level, msg)
        else:
            logger.logp(level, cls, method, msg)

def clearLogger():
    global g_logger
    g_logger = None

def isLoggerEnabled(ctx):
    level = _getLogConfig(ctx).LogLevel
    enabled = _isLogEnabled(level)
    return enabled

def getLoggerSetting(ctx):
    enabled, index, handler = _getLoggerSetting(ctx)
    return enabled, index, _getState(handler)

def setLoggerSetting(ctx, enabled, index, state):
    handler = _getHandler(state)
    _setLoggerSetting(ctx, enabled, index, handler)

def getLoggerUrl(ctx):
    url = '$(userurl)/$(loggername).log'
    settings = _getLogConfig(ctx).getByName('HandlerSettings')
    if settings.hasByName('FileURL'):
        url = settings.getByName('FileURL')
    service = ctx.ServiceManager.createInstance('com.sun.star.util.PathSubstitution')
    logger = _getLogName()
    return service.substituteVariables(url.replace('$(loggername)', logger), True)

# Private getter method
def _getLogger(ctx):
    if g_logger is None:
        _setLogger(ctx)
    return g_logger

def _getResource(ctx, fileresource):
    if fileresource not in g_stringResource:
        resource = getStringResource(ctx, g_identifier, _getPathResource(), fileresource)
        g_stringResource[fileresource] = resource
    return g_stringResource[fileresource]

def _getLogName():
    return '%s.Logger' % g_identifier

def _getPathResource():
    return 'resource'

def _getLoggerSetting(ctx):
    configuration = _getLogConfig(ctx)
    enabled, index = _getLogIndex(configuration)
    handler = configuration.DefaultHandler
    return enabled, index, handler

def _getLogConfig(ctx):
    logger = _getLogName()
    nodepath = '/org.openoffice.Office.Logging/Settings'
    configuration = getConfiguration(ctx, nodepath, True)
    if not configuration.hasByName(logger):
        configuration.insertByName(logger, configuration.createInstance())
        configuration.commitChanges()
    nodepath += '/%s' % logger
    return getConfiguration(ctx, nodepath, True)

def _getLogIndex(configuration):
    index = 7
    level = configuration.LogLevel
    enabled = _isLogEnabled(level)
    if enabled:
        index = _getLogLevels().index(level)
    return enabled, index

def _getLogLevels():
    levels = (SEVERE,
              WARNING,
              INFO,
              CONFIG,
              FINE,
              FINER,
              FINEST,
              ALL)
    return levels

def _isLogEnabled(level):
    return level != OFF

def _getLogSetting():
    global g_logSettings
    enabled = g_logSettings['enabled']
    index = g_logSettings['index']
    handler = g_logSettings['handler']
    g_logSettings = None
    return enabled, index, handler

def _getDebugSetting():
    return True, 7, 'com.sun.star.logging.FileHandler'

def _getHandler(state):
    handlers = {True: 'ConsoleHandler', False: 'FileHandler'}
    return 'com.sun.star.logging.%s' % handlers.get(state)

def _getState(handler):
    states = {'com.sun.star.logging.ConsoleHandler' : 1,
              'com.sun.star.logging.FileHandler': 2}
    return states.get(handler)

# Private setter method
def _setLogger(ctx):
    global g_logger
    logger = _getLogName()
    singleton = '/singletons/com.sun.star.logging.LoggerPool'
    g_logger = ctx.getValueByName(singleton).getNamedLogger(logger)

def _setLoggerSetting(ctx, enabled, index, handler):
    configuration = _getLogConfig(ctx)
    _setLogIndex(configuration, enabled, index)
    _setLogHandler(configuration, handler, index)
    if configuration.hasPendingChanges():
        configuration.commitChanges()
        clearLogger()

def _setLogIndex(configuration, enabled, index):
    level = _getLogLevels()[index] if enabled else OFF
    if configuration.LogLevel != level:
        configuration.LogLevel = level

def _setLogHandler(configuration, handler, index):
    if configuration.DefaultHandler != handler:
        configuration.DefaultHandler = handler
    settings = configuration.getByName('HandlerSettings')
    if settings.hasByName('Threshold'):
        if settings.getByName('Threshold') != index:
            settings.replaceByName('Threshold', index)
    else:
        settings.insertByName('Threshold', index)

def _setDebugMode(mode):
    global g_debugMode
    g_debugMode = mode

def _setDebugModeOn(ctx):
    _setLogSetting(*_getLoggerSetting(ctx))
    _setLoggerSetting(ctx, *_getDebugSetting())

def _setDebugModeOff(ctx):
    if g_logSettings is not None:
        _setLoggerSetting(ctx, *_getLogSetting())

def _setLogSetting(enabled, index, handler):
    global g_logSettings
    g_logSettings = {'enabled': enabled, 'index': index, 'handler': handler}
