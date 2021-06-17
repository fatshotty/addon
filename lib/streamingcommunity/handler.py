import time, os, re, sys

if sys.version_info[0] >= 3:
    PY3 = True
    import urllib.request as urllib
    import urllib.parse as urlparse
else:
    PY3 = False
    import urlparse
    import urllib

from platformcode import logger


class Handler():

    def __init__(self, client):
        self._client = client

    def log_message(self, format, *args):
        pass


    def handle_request(self,
        method = None,
        url = None,
        response = None,
        range = None,
        response_status = None,
        add_header = None,
        end_headers = None):
        """
        " Got request
        " We are going to handle the request path in order to proxy each manifest
        """
        logger.debug('HANDLER:', url)

        if method == 'HEAD':
            response_status(200, 'OK')
            end_headers()
            logger.info('responde 200 ok as per HEAD request')
            return True

        response_str = None

        # Default content-type for each manifest
        cType = "application/vnd.apple.mpegurl"

        if url == "manifest.m3u8":
            response_str = self._client.get_main_manifest_content()

        elif url.startswith('video/'):
            response_str = self._client.get_video_manifest_content(url)

        elif url.startswith('audio/'):
            response_str = self._client.get_audio_manifest_content(url)

        elif url.endswith('enc.key'):
            # This path should NOT be used, see get_video_manifest_content function
            response_str = self._client.get_enc_key( url )
            cType = "application/octet-stream"


        if response_str == None:
            # Default 404 response
            response_status(404, 'Not Found')
            end_headers()
            response.flush()
            logger.info('Responding 404 for url', url)

        else:
            # catch OK response and send it to client
            response_status(200, 'OK')
            add_header("Content-Type", cType )
            add_header("Content-Length", str( len(response_str.encode('utf-8')) ) )
            end_headers()

            response.write( response_str.encode() )

            # force flush just to be sure
            response.flush()

            logger.info('HANDLER flushed:', cType , str( len(response_str.encode('utf-8')) ) )
            logger.debug( response_str.encode('utf-8') )


