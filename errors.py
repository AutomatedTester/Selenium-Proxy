# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1 
# 
# The contents of this file are subject to the Mozilla Public License Version 
# 1.1 (the "License"); you may not use this file except in compliance with 
# the License. You may obtain a copy of the License at 
# http://www.mozilla.org/MPL/ # 
# Software distributed under the License is distributed on an "AS IS" basis, 
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License 
# for the specific language governing rights and limitations under the 
# License. 
# 
# The Original Code is Marionette Client. 
# 
# The Initial Developer of the Original Code is 
#   Mozilla Foundation. 
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved. 
# 
# Contributor(s): 
#  Jonathan Griffin <jgriffin@mozilla.com>
# 
# Alternatively, the contents of this file may be used under the terms of 
# either the GNU General Public License Version 2 or later (the "GPL"), or 
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"), 
# in which case the provisions of the GPL or the LGPL are applicable instead 
# of those above. If you wish to allow use of your version of this file only 
# under the terms of either the GPL or the LGPL, and not to allow others to 
# use your version of this file under the terms of the MPL, indicate your 
# decision by deleting the provisions above and replace them with the notice 
# and other provisions required by the GPL or the LGPL. If you do not delete 
# the provisions above, a recipient may use your version of this file under 
# the terms of any one of the MPL, the GPL or the LGPL. 
# 
# ***** END LICENSE BLOCK ***** 


class MarionetteException(Exception):

    def __init__(self, message=None, status=500, stacktrace=None):
        self.message = message
        self.status = status
        self.stacktrace = stacktrace

    def __str__(self):
        if self.stacktrace:
            return '%s\nstacktrace:\n%s' % (str(self.message),
                ''.join(['\t%s\n' % x for x in self.stacktrace.split('\n')]))
        else:
            return str(self.message)

class TimeoutException(MarionetteException):
    pass

class NoSuchAttributeException(MarionetteException):
    pass

class JavascriptException(MarionetteException):
    pass

class NoSuchElementException(MarionetteException):
    pass

class XPathLookupException(MarionetteException):
    pass

class NoSuchWindowException(MarionetteException):
    pass

class StaleElementException(MarionetteException):
    pass

class ScriptTimeoutException(MarionetteException):
    pass

class ElementNotVisibleException(MarionetteException):
    pass

class NoSuchFrameException(MarionetteException):
    pass

class InvalidElementStateException(MarionetteException):
    pass

class NoAlertPresentException(MarionetteException):
    pass

class InvalidCookieDomainException(MarionetteException):
    pass

class UnableToSetCookieException(MarionetteException):
    pass

class InvalidSelectorException(MarionetteException):
    pass

class MoveTargetOutOfBoundsException(MarionetteException):
    pass

class ErrorCodes(object):
    
    SUCCESS = 0
    NO_SUCH_ELEMENT = 7
    NO_SUCH_FRAME = 8
    UNKNOWN_COMMAND = 9
    STALE_ELEMENT_REFERENCE = 10
    ELEMENT_NOT_VISIBLE = 11
    INVALID_ELEMENT_STATE = 12
    UNKNOWN_ERROR = 13
    ELEMENT_IS_NOT_SELECTABLE = 15
    JAVASCRIPT_ERROR = 17
    XPATH_LOOKUP_ERROR = 19
    TIMEOUT = 21
    NO_SUCH_WINDOW = 23
    INVALID_COOKIE_DOMAIN = 24
    UNABLE_TO_SET_COOKIE = 25
    UNEXPECTED_ALERT_OPEN = 26
    NO_ALERT_OPEN = 27
    SCRIPT_TIMEOUT = 28
    INVALID_ELEMENT_COORDINATES = 29
    INVALID_SELECTOR = 32
    MOVE_TARGET_OUT_OF_BOUNDS = 34
    INVALID_XPATH_SELECTOR = 51
    INVALID_XPATH_SELECTOR_RETURN_TYPER = 52
