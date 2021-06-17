import sys, traceback, random
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
# from platformcode import logger

IP = "127.0.0.1"


def find_port():
    return random.randint(8000,8099)



class KODServer(ThreadingMixIn, HTTPServer):
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
            port = find_port()

            try:
                HTTPServer.__init__(self, (IP, port), None)
                self._port = port
                OK = True
            except Exception as e:
                logger.warn(port, 'is not a valid port, try again')

            if OK:
                logger.info('HTTPServer has found port:', port)
                break # exit loop
                pass

            choices = choices - 1

        if OK:
            self._thread = Thread(target=self.run, name='KOD HTTP Server')
            self._thread.daemon = self.daemon_threads
            self._thread.start()

        return OK



    def stop(self):
        self.server_close()
        self.running = False

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



KODServer()
