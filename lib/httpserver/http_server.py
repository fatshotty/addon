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
from core import support

IP = "127.0.0.1"

def find_port():
    return 8000 #random.randint(8000,8099)


KOD_SERVER_INSTANCE = None

def GET_KOD_SERVER():
    global KOD_SERVER_INSTANCE
    if KOD_SERVER_INSTANCE == None:
        logger.info('KODServer: create a new  server')
        KOD_SERVER_INSTANCE = KODServer()

    return KOD_SERVER_INSTANCE

def GET_ADDRESS():
    return str(IP) + ':' + str(KOD_SERVER_INSTANCE.port)



class KODServer(HTTPServer):
    daemon_threads = True
    timeout = 1
    running = False
    port = 0

    def __init__(self):
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
                HTTPServer.__init__(self, (IP, _port), Handler )
                self.port = _port
                OK = True
            except Exception as e:
                logger.error(_port, 'is not a valid port, try again')

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
        self.shutdown()
        self.running = False

        KOD_SERVER_INSTANCE = None
        logger.info('KODServer: HTTPServer is closed!')

    # def serve(self):
    #     while self.running:
    #         try:
    #             self.handle_request()
    #         except:
    #             logger.error(traceback.format_exc())

    def run(self):
        logger.info('KODServer: http server is starting...')
        self.running == True
        self.serve_forever()
        logger.info('KODServer: http server is started!')


    def handle_error(self, request, client_address):
        logger.error( traceback.format_exc() )
        if not "socket.py" in traceback.format_exc():
            # logger.error(traceback.format_exc())
            pass



class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    namespaces = {}


    # def __init__(self):
    #     pass


    def parse_range(self, range):
        if range:
            m=re.compile(r'bytes=(\d+)-(\d+)?').match(range)
            if m:
              return m.group(1), m.group(2)
        return None, None

    def _get_client(self, namespace):
        c = __import__('lib.' + namespace + '.client', None, None, ['lib.' + namespace + '.client'])
        return c.get_klass()


    def handle_all_request(self, method):
        """
        " Catch and manage all requests for each method
        """
        logger.info('req path', self.path)

        indx = self.path.find('?')
        params = ''
        if indx > -1:
            params = self.path[ (indx + 1): ]

        url = urlparse.urlparse(self.path).path

        start, end = self.parse_range( self.headers.get('Range', "") )

        logger.info('KODServer: get a request ->', method, url)

        re_namespace = re.search(r'^\/?(.*?)\/', url)
        ns = re_namespace.group(1)
        url_for_handler = url.replace( re_namespace.group(0),  '' )

        logger.info('KODServer: suburl ->', url_for_handler)

        if url_for_handler == 'init':
            logger.info('KODServer: request for first ping', ns, url_for_handler)
            # support.dbg()
            client_klass = self._get_client(ns)
            client = client_klass(params)
            new_location = client.initialization()
            logger.info('KODServer: new location url', new_location)

            self.namespaces[ ns ] = None

            if new_location:

                self.namespaces[ ns ] = client.handler

                self.send_response(302, 'Moved Temporarily')
                self.send_header('Location', new_location)
                self.end_headers()

            else:
                logger.error('KODServer: no new_location')
                self.send_error(502)

        elif ns in self.namespaces:
            handler = self.namespaces[ ns ]
            logger.info('KODServer: namespace found:', ns, handler)

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
            logger.error('NO namespace found for', ns)

            # finish response
            self.send_error(501)




    def finish_response(self, code = 501):
        """
        " This method catch each 'not-handled-request'
        """
        logger.error('KODServer: responding ', code)
        self.send_response(code)
        self.end_headers()
        self.wfile.write(b'')
        self.wfile.flush()



    def do_HEAD(self):
        logger.info('HEAD REQUEST')
        self.handle_all_request('HEAD')

    def do_GET(self):
        logger.info('GET REQUEST')
        self.handle_all_request('GET')


# KODServer()
