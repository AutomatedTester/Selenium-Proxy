# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import BaseHTTPServer
import json
import logging
import os
import platform
import re
import traceback

from marionette.errors import MarionetteException
from marionette import Marionette, HTMLElement
from mozprofile.profile import Profile
from mozrunner.runner import FirefoxRunner


logger = logging.getLogger('Selenium-Proxy')
ch = logging.FileHandler('selenium-proxy.log')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class SeleniumRequestServer(BaseHTTPServer.HTTPServer):

    def __init__(self, *args, **kwargs):
        self.marionette = None
        self.runner = None
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)

    def __del__(self):
        if self.server.marionette:
            self.marionette.delete_session()

class SeleniumRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    pathRe = re.compile(r'/session/(.*?)($|/((\w+/(.*?)/)?(.*)))')

    def server_error(self, error):
        self.send_response(500)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({'status': 500, 'value': {'message': error}}))

    def file_not_found(self):
        self.send_response(404)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({'status': 404, 'value': {'message': '%s not found' % self.path}}))

    def send_JSON(self, data=None, session=None, value=None):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        if data is None:
            data = {}
        if not 'status' in data:
            data['status'] = 0
        if session is not None:
            data['sessionId'] = session
        if value is None:
            data['value'] = {}
        else:
            data['value'] = value
        
        self.wfile.write(json.dumps(data))

    def process_request(self):
        session = body = None
        path = self.path
        element = None
        m = self.pathRe.search(self.path)
        if m:
            session = m.group(1)
            element = m.group(5)
            path = '/%s' % m.group(6) if m.group(6) else ''
        content_len = self.headers.getheader('content-length')
        if content_len:
            body = json.loads(self.rfile.read(int(content_len)))
        
        return path, body, session, element

    def do_DELETE(self):
        try:

            path, body, session, element = self.process_request()
            logger.debug("%s - %s - %s - %s" % (path, body, session, element))

            if path == '':
                logger.info("Deleting Session - %s" % session)
                assert(session)
                assert(self.server.marionette.delete_session())
                self.send_JSON(session=session)
                logger.debug("Shutting down the browser")
                self.server.runner.stop()
            elif path == '/window':
                logger.info("Closing the window - %s" % session)
                assert(session)
                assert(self.server.marionette.close_window())
                self.send_JSON(session=session)
            else:
                logger.error("Unknown path - %s" % session)
                self.file_not_found()

        except MarionetteException as e:
            logger.error("Status: %s - Message: %s" % (e.status, e.message))
            self.send_JSON(data={'status': e.status}, value={'message': e.message})
        except:
            trace_ = traceback.format_exc()
            logger.critical("Server Exception: %s" % trace_)
            self.server_error(trace_)

    def do_GET(self):
        try:

            path, body, session, element = self.process_request()
            logger.debug("%s - %s - %s - %s" % (path, body, session, element))

            if path.startswith('/attribute/'):
                logger.info("Getting Attribute %s - %s" % (element, session)) 
                assert(session)
                name = path[len('/attribute/'):]
                marionette_element = HTMLElement(self.server.marionette, element)
                self.send_JSON(session=session,
                               value=marionette_element.get_attribute(name))
            elif path == '/displayed':
                logger.info("Displayed %s - %s" % (element, session)) 
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                self.send_JSON(session=session,
                               value=marionette_element.is_displayed())
            elif path == '/enabled':
                logger.info("Enabled %s - %s" % (element, session)) 
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                self.send_JSON(session=session,
                               value=marionette_element.enabled())
            elif path.startswith('/equals/'):
                assert(session)
                other = path[len('/equals'):]
                marionette_element = HTMLElement(self.server.marionette, element)
                other_element = HTMLElement(self.server.marionette, other)
                self.send_JSON(session=session,
                               value=marionette_element.equals(other_element))
            elif path == '/selected':
                logger.info("Selected %s - %s" % (element, session)) 
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                self.send_JSON(session=session,
                               value=marionette_element.selected())
            elif path == '/status':
                self.send_JSON(data=self.server.marionette.status())
            elif path == '/text':
                logger.info("Getting text %s - %s" % (element, session)) 
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                self.send_JSON(session=session,
                               value=marionette_element.text)
            elif path == '/url':
                logger.info("Getting url - %s" % session)
                assert(session)
                self.send_JSON(value=self.server.marionette.get_url(),
                               session=session)
            elif path == '/window_handle':
                logger.info("Getting window handle - %s" % session)
                assert(session)
                self.send_JSON(session=session,
                               value=self.server.marionette.current_window_handle)
            elif path == '/window_handles':
                logger.info("Getting window handles - %s" % session)
                assert(session)
                self.send_JSON(session=session,
                               value=self.server.marionette.window_handles)
            elif path == '/title':
                logger.info("Getting Window Title")
                assert(session)
                self.send_JSON(session=session,
                            value=self.server.marionette.title)
            elif path == "/name":
                logger.info("Getting element tag name")
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                self.send_JSON(session=session,
                            value=marionette_element.tag_name)
            else:
                logger.error("Unknown path - %s" % session)
                self.file_not_found()

        except MarionetteException as e:
            logger.error("Status: %s - Message: %s" % (e.status, e.message))
            self.send_JSON(data={'status': e.status}, value={'message': e.message})
        except:
            trace_ = traceback.format_exc()
            logger.critical("Server Exception: %s" % trace_)
            self.server_error(trace_)

    def do_POST(self):
        try:

            path, body, session, element = self.process_request()
            logger.debug("%s - %s - %s - %s" % (path, body, session, element))

            if path == '/back':
                logger.info("Navigating back - %s" % session)
                assert(session)
                assert(self.server.marionette.go_back())
                self.send_JSON(session=session)
            elif path == '/clear':
                logger.info("Clearing %s - %s" % (element, session))
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                marionette_element.clear()
                self.send_JSON(session=session)
            elif path == '/click':
                logger.info("Clicking %s - %s" % (element, session))
                assert(session)
                marionette_element = HTMLElement(self.server.marionette, element)
                marionette_element.click()
                self.send_JSON(session=session)
            elif path == '/element':
                logger.info("Find Element using - %s, value - %s  - %s" \
                            % (body['using'], body['value'], session)) 
                # find element variants
                assert(session)
                self.send_JSON(session=session,
                               value={'ELEMENT': self.server.marionette.find_element(body['using'], body['value'], id=element).id})
            elif path == '/elements':
                logger.info("Find Elements using - %s, value - %s  - %s" \
                            % (body['using'], body['value'], session)) 
                # find elements variants
                assert(session)
                self.send_JSON(session=session,
                               value=[{'ELEMENT': x.id} for x in self.server.marionette.find_elements(body['using'], body['value'])])
            elif path == '/execute':
                logger.info("Executing Script - %s" % session)
                assert(session)
                if body['args']:
                    result = self.server.marionette.execute_script(body['script'], script_args=body['args'],
                                                            new_sandbox=False)
                else:
                    result = self.server.marionette.execute_script(body['script'],new_sandbox=False)
                self.send_JSON(session=session, value=result)
            elif path == '/execute_async':
                logger.info("Executing Async Script - %s" % session)
                assert(session)
                result = None
                if body['args']:
                    result = self.server.marionette.execute_async_script(body['script'], script_args=body['args'], new_sandbox=False)
                else:
                    result = self.server.marionette.execute_async_script(body['script'], new_sandbox=False)
                self.send_JSON(session=session, value=result)
            elif path == '/forward':
                logger.info("Forwarding - %s" % session)
                assert(session)
                assert(self.server.marionette.go_forward())
                self.send_JSON(session=session)
            elif path == '/frame':
                logger.info("Switch to Frame %s - %s" % (body['id'], session))
                assert(session)
                frame = body['id']
                if isinstance(frame, dict) and 'ELEMENT' in frame:
                    frame = HTMLElement(self.server.marionette, frame['ELEMENT'])
                assert(self.server.marionette.switch_to_frame(frame))
                self.send_JSON(session=session)
            elif path == '/refresh':
                logger.info("Refreshing the page - %s" % session)
                assert(session)
                assert(self.server.marionette.refresh())
                self.send_JSON(session=session)
            elif path == '/session':
                logger.info("Creating new session")
                logger.debug("loading webdriver prefs")
                with open('webdriver.json') as webpref:
                    read_prefs = webpref.read()

                prefs = json.loads(read_prefs)
                port = free_port()

                logger.debug("Creating Profile")
                profile = Profile()
                profile.set_preferences(prefs['frozen'])
                profile.set_preferences(prefs['mutable'])
                profile.set_preferences({"marionette.defaultPrefs.enabled": True,
                                        "marionette.defaultPrefs.port": port})

                logger.debug("Profile created at %s" % profile.profile)
                logger.debug("Creating runner")
                firefox_binary = body["desiredCapabilities"]['firefoxBinary'] if body["desiredCapabilities"]['firefoxBinary'] else firefox_binary_path()
                self.server.runner = FirefoxRunner(profile, firefox_binary)
                self.server.runner.start()
                logger.debug("Browser has been started")
                import time
                time.sleep(10)
                logger.info("Creating Marionette instance on %s:%s" % ("localhost", port)) 
                self.server.marionette = Marionette("localhost", port)
                session = self.server.marionette.start_session()
                self.send_JSON(session=session, value={})
                # 'value' is the browser capabilities, which we're ignoring for now
            elif path == '/timeouts/async_script':
                logger.info("Script timeout %s ms - %s" % (body['ms'], session))
                assert(session)
                assert(self.server.marionette.set_script_timeout(body['ms']))
                self.send_JSON(session=session)
            elif path == '/timeouts/implicit_wait':
                logger.info("Implicit timeout %s ms - %s" % (body['ms'], session))
                assert(session)
                assert(self.server.marionette.set_search_timeout(body['ms']))
                self.send_JSON(session=session)
            elif path == '/url':
                logger.info("Navigating to %s - %s" % (body['url'], session))
                assert(session)
                assert(self.server.marionette.navigate(body['url']))
                self.send_JSON(session=session)
            elif path == '/value':
                logger.info("Send Keys %s - %s" % (''.join(body['value']), session))
                assert(session)
                keys = ''.join(body['value'])
                marionette_element = HTMLElement(self.server.marionette, element)
                assert(marionette_element.send_keys(keys))
                self.send_JSON(session=session)
            elif path == '/window':
                logger.info("Switch to Window %s - %s" % (body['name'], session))
                assert(session)
                assert(self.server.marionette.switch_to_window(body['name']))
                self.send_JSON(session=session)
            else:
                logger.error("Unknown path - %s" % session)
                self.file_not_found()

        except MarionetteException as e:
            logger.error("Status: %s - Message: %s" % (e.status, e.message))
            self.send_JSON(data={'status': e.status}, value={'message': e.message})
        except:
            trace_ = traceback.format_exc()
            logger.critical("Server Exception: %s" % trace_)
            self.server_error(trace_)

class SeleniumProxy(object):

    def __init__(self, remote_host='localhost', proxy_port=4444):
        self.remote_host = remote_host
        self.proxy_port = proxy_port

    def start(self):
        logger.info("Starting the Selenium Proxy. Server is running is running on %s:%s" \
                     % ("localhost", self.proxy_port) )
        httpd = SeleniumRequestServer(('127.0.0.1', self.proxy_port),
                                      SeleniumRequestHandler)
        httpd.serve_forever()

def free_port():
    import socket
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('127.0.0.1', 0))
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port

def firefox_binary_path():
    start_cmd = ""
    if platform.system() == "Darwin":
        start_cmd = ("/Applications/Firefox.app/Contents/MacOS/firefox-bin")
    elif platform.system() == "Windows":
        start_cmd = (_find_exe_in_registry() or 
                     _default_windows_location())
    elif platform.system() == 'Java' and os._name == 'nt':
        start_cmd = _default_windows_location()
    else:
        for ffname in ["firefox", "iceweasel"]:
            start_cmd = _which(ffname)
            if start_cmd is not None:
                break
            else:
                # couldn't find firefox on the system path
                raise RuntimeError("Could not find firefox in your system PATH." + 
                                   " Please specify the firefox binary location or install firefox")
    return start_cmd

def _find_exe_in_registry():
    try:
        from _winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
    except ImportError:
        from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
    import shlex
    keys = (
            r"SOFTWARE\Classes\FirefoxHTML\shell\open\command",
            r"SOFTWARE\Classes\Applications\firefox.exe\shell\open\command"
           )
    command = ""
    for path in keys:
        try:
            key = OpenKey(HKEY_LOCAL_MACHINE, path)
            command = QueryValue(key, "")
            break
        except OSError:
            pass
        else:
            return ""
    return shlex.split(command)[0]


def _default_windows_location():
    program_files = [os.getenv("PROGRAMFILES", r"C:\Program Files"),
                     os.getenv("PROGRAMFILES(X86)", r"C:\Program Files (x86)")]
    for path in program_files:
        binary_path = os.path.join(path, r"Mozilla Firefox\firefox.exe")
        if os.access(binary_path, os.X_OK):
            return binary_path
    return ""

def _which(fname):
    """Returns the fully qualified path by searching Path of the given name"""
    for pe in os.environ['PATH'].split(os.pathsep):
        checkname = os.path.join(pe, fname)
        if os.access(checkname, os.X_OK) and not os.path.isdir(checkname):
            return checkname
    return None


if __name__ == "__main__":
    proxy = SeleniumProxy()
    proxy.start()
