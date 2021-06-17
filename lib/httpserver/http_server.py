import sys, traceback, random
import re
if sys.version_info[0] >= 3:
    PY3 = True
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
    import urllib.request as urllib
    import urllib.parse as urlparse
else:
    PY3 = False
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from SocketServer import ThreadingMixIn
    import urlparse
    import urllib


from threading import Thread
from platformcode import logger

IP = "127.0.0.1"

def find_port():
    return random.randint(8000,8099)


KOD_SERVER_INSTANCE = None

def GET_KOD_SERVER():
    if KOD_SERVER_INSTANCE == None:
        logger.info('KODServer: create a new  server')
        KOD_SERVER_INSTANCE = KODServer()

    return KOD_SERVER_INSTANCE

def ADD_NAMESPACE(namespace, handler):
    KOD_SERVER_INSTANCE.add_namespace( namespace, handler )


def GET_ADDRESS():
    return str(IP) + ':' + str(KOD_SERVER_INSTANCE.port)



class KODServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    timeout = 1
    running = False
    port = 0
    _handler = None

    def __init__(self):

        self._handler = Handler()
        self.start()


    def start(self):
        OK = False
        choices = 3

        if self.running == True:
            # server is already running
            return True

        while choices > 0:
            _port = find_port()

            try:
                HTTPServer.__init__(self, (IP, _port), self._handler )
                self.port = _port
                OK = True
            except Exception as e:
                logger.warn(_port, 'is not a valid port, try again')

            if OK:
                logger.info('HTTPServer has found port:', _port)
                break # exit loop
                pass

            choices = choices - 1

        if OK:
            self._thread = Thread(target = self.run, name = 'KOD HTTP Server')
            self._thread.daemon = self.daemon_threads
            self._thread.start()

        return OK



    def stop(self):
        self.server_close()
        self.running = False

        KOD_SERVER_INSTANCE = None

    # def serve(self):
    #     while self.running:
    #         try:
    #             self.handle_request()
    #         except:
    #             logger.error(traceback.format_exc())

    def run(self):
        self.serve_forever()
        self.running == True


    def handle_error(self, request, client_address):
        if not "socket.py" in traceback.format_exc():
            # logger.error(traceback.format_exc())
            pass

    def add_namespace(self, namespace, handler):
        self._handler.add_namespace(namespace, handler)



class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    namespaces = []


    def __init__(self):
        pass


    def add_namespace(self, namespace, handler):

        if namespace in self.namespaces:
            logger.warn('KODServer: ', namespace, 'already in collection, replace the older one!')

        self.namespaces[ namespace ] = handler
        logger.warn('KODServer: ', namespace, 'has been added to collection and ready to handle request :)')



    def parse_range(self, range):
        if range:
            m=re.compile(r'bytes=(\d+)-(\d+)?').match(range)
            if m:
              return m.group(1), m.group(2)
        return None, None



    def handle_all_request(self, method):
        """
        " Catch and manage all requests for each method
        """

        url = urlparse.urlparse(self.path).path

        start, end = self.parse_range( self.headers.get('Range', "") )

        logger.info('KODServer: get a request ->', method, url)

        re_namespace = re.search(r'^\/?(.*?)\/', url)
        ns = re_namespace.group(1)

        if ns in self.namespace:
            handler = self.namespace[ ns ]
            logger.warn('KODServer: namespace found:', ns, handler)

            url_for_handler = url.replace( re_namespace.group(0),  '' )
            handler.handle_request(
                method=method,
                url=url_for_handler,
                response=self.wfile,
                range=(start, end),
                response_status=self.send_response,
                add_header=self.send_header,
                end_headers=self.end_headers
                 )


        else:
            logger.warn('NO namespace found for', ns)

            # finish response
            self.finish_response()




    def finish_response(self):
        """
        " This method catch each 'not-handled-request'
        """
        logger.warn('KODServer: responding 501')
        self.send_response(501, 'Method not implemented')
        self.end_headers()
        self.wfile.flush()



    def do_HEAD(self):
        self.handle_all_request('HEAD')

    def do_POST(self):
        self.handle_all_request('POST')

    def do_GET(self):
        self.handle_all_request('GET')


# KODServer()
