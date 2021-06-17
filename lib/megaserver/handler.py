import time, os, re, sys

if sys.version_info[0] >= 3:
    PY3 = True
    # from http.server import BaseHTTPRequestHandler
    import urllib.request as urllib
    import urllib.parse as urlparse
else:
    PY3 = False
    # from BaseHTTPServer import BaseHTTPRequestHandler
    import urlparse
    import urllib


class Handler():


    def __init__(self, client):
        self._client = client

    # def log_message(self, format, *args):
    #     pass

    # def parse_range(self, range):
    #     if range:
    #         m=re.compile(r'bytes=(\d+)-(\d+)?').match(range)
    #         if m:
    #           return m.group(1), m.group(2)
    #     return None, None

    def handle_request(self,
        method = None,
        url = None,
        response = None,
        range = None,
        response_status = None,
        add_header = None,
        end_headers = None):


        proceed = False

        while not self._client.files:
            time.sleep(1)

        if url == "/playlist.pls":
            pls = self.get_pls(response, self._client.files)
            response_status(200, 'OK')
            add_header( "Content-Length", str(len(playlist)) )
            end_headers()
            response.write(playlist)
            proceed = False

        if PY3: filename = urllib.unquote(url)[1:]
        else: filename = urllib.unquote(url)[1:].decode("utf-8")

        if not self._client.file or urllib.unquote(url)[1:] != self._client.file.name:
            for f in self._client.files:
                if f.name == filename:
                    self._client.file = f
                    break


        if self._client.file and filename == self._client.file.name:
            self.offset = 0
            size, mime = self._file_info()
            start = range[0]
            end = range[1]
            self.size = size

            if start != None:
                if end == None: end = size - 1
                self.offset=int(start)
                self.size=int(end) - int(start) + 1
                range=(int(start), int(end), int(size))
            else:
                range = None

            self.send_resp_header(response_status, add_header, end_headers, mime, size, range)
            proceed = True

        else:
            response_status(404, 'Not Found')
            proceed = False

        if proceed:
            with self._client.file.create_cursor(self.offset) as f:
                sent = 0
                while sent < self.size:
                    buf = f.read(1024*16)
                    if buf:
                        if sent + len(buf) > self.size: buf=buf[:self.size-sent]
                        response.write(buf)
                        sent +=len(buf)
                    else:
                        break


    # def do_GET(self):
    #     self._client.connected = True


    def get_pls(self, files):
        playlist = "[playlist]\n\n"
        for x,f in enumerate(files):
            playlist += "File"+str(x+1)+"=http://" + self.server._client.ip + ":" + str(self.server._client.port) + "/" + urllib.quote(f.name)+"\n"
            playlist += "Title"+str(x+1)+"=" +f.name+"\n"

        playlist +="NumberOfEntries=" + str(len(files))
        playlist +="Version=2"


    # def do_HEAD(self):
    #     url=urlparse.urlparse(self.path).path

    #     while not self.server._client.files:
    #         time.sleep(1)

    #     if url=="/playlist.pls":
    #         self.send_pls(self.server._client.files)
    #         return False

    #     if PY3: filename = urllib.unquote(url)[1:]
    #     else: filename = urllib.unquote(url)[1:].decode("utf-8")

    #     if not self.server._client.file or urllib.unquote(url)[1:] != self.server._client.file.name:
    #         for f in self.server._client.files:
    #             if f.name == filename:
    #                 self.server._client.file = f
    #                 break


    #     if self.server._client.file and filename == self.server._client.file.name:
    #         range = False
    #         self.offset = 0
    #         size, mime = self._file_info()
    #         start, end = self.parse_range(self.headers.get('Range', ""))
    #         self.size = size

    #         if start != None:
    #             if end == None: end = size - 1
    #             self.offset=int(start)
    #             self.size=int(end) - int(start) + 1
    #             range=(int(start), int(end), int(size))
    #         else:
    #             range = None

    #         self.send_resp_header(mime, size, range)
    #         return True

    #     else:
    #         self.send_error(404, 'Not Found')


    def _file_info(self):
        size=self._client.file.size
        ext=os.path.splitext(self._client.file.name)[1]
        mime=self._client.VIDEO_EXTS.get(ext)
        if not mime:
            mime='application/octet-stream'
        return size,mime


    def send_resp_header(self, send_status, send_header, end_headers, cont_type, size, range=False):

        if range:
            send_status(206, 'Partial Content')
        else:
            send_status(200, 'OK')

        send_header('Content-Type', cont_type)
        send_header('Accept-Ranges', 'bytes')

        if range:
            if isinstance(range, (tuple, list)) and len(range)==3:
                send_header('Content-Range', 'bytes %d-%d/%d' % range)
                send_header('Content-Length', range[1]-range[0]+1)
            else:
                raise ValueError('Invalid range value')
        else:
            send_header('Content-Length', size)

        send_header('Connection', 'close')
        end_headers()

