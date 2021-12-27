
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import logging
import json
import time
import mimetypes
import os
from functools import partial


PRODUCT_NAME = 'Mini HTTP Server'
PRODUCT_VER = '1.0.0'
PRODUCT_DESCRIPTION = 'A Mini HTTP Server.'


SERVICE_LIST = [
    {'path': '/api/echo', 'description': 'the echo service'},
]


class MiniHTTPServer(BaseHTTPRequestHandler):
    def __init__(self, *args, static_directory=None, **kwargs):
        self.static_directory = static_directory
        super().__init__(*args, **kwargs)
    
    def log_error(self, format, *args):
        logging.error("%s %s\n" %
                      (self.address_string(),
                          format % args))

    def log_message(self, format, *args):
        logging.info("%s %s\n" %
                     (self.address_string(),
                      format % args))
        
    def send_file(self, code, file):
        if os.path.isfile(file):
            content_type = mimetypes.guess_type(file)[0]
            if content_type is None:
                content_type = 'application/octet-stream'
            
            with open(file, 'rb') as f:
                self.send_response(code)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.log_message('sendfile: {}'.format(file))
                self.wfile.write(f.read())
                return
        
        if os.path.isdir(file):
            self.send_error(403, 'List {} forbidden'.format(file))
            return
        
        self.send_error(404, 'File {} not found'.format(file))
    
    def echo(self):
        self.send_response(200)
        self.send_header('Content-Type', self.headers['Content-Type'])
        self.end_headers()
        clen = int(self.headers['Content-Length'])
        self.wfile.write(self.rfile.read(clen))
    
    def redirect(self, url):
        self.send_response(301)
        self.send_header('Location', url)
        self.end_headers()
    
    def send_text(self, code, text, content_type='text/plain; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(text.encode('utf-8'))
        
    def send_html(self, code, text):
        self.send_text(code, text, 'text/html; charset=utf-8')

    def send_json(self, code, obj):
        text = json.dumps(obj)
        self.send_text(code, text, 'application/json; charset=utf-8')

    def read_json(self):
        clen = int(self.headers['Content-Length'])
        body = self.rfile.read(clen)
        return json.loads(body)

    def do_GET(self):
        if self.path == '/':
            self.send_text(200, '{}\n{}: v{}'.format(
                    PRODUCT_DESCRIPTION, PRODUCT_NAME, PRODUCT_VER)
                )
            return

        if self.path == '/favicon.ico':
            self.send_file(200, 'favicon.ico')
            return
        
        if self.path == '/api':
            self.send_json(200, SERVICE_LIST)
            return

        if self.path == '/status' or self.path == '/healthcheck':
            self.send_json(200, {'status': 'okay'})
            return
        
        if self.path == '/version':
            self.send_json(200, {'product': PRODUCT_NAME,
                             'version': PRODUCT_VER,
                             'description': PRODUCT_DESCRIPTION})
            return
        
        if self.path.startswith('/static/') and self.static_directory is not None:
            self.send_file(200, os.path.join(self.static_directory,
                                        self.path.removeprefix('/static/')))
            return
        
        self.send_error(404, 'Path "{}" not found.'.format(self.path))

    def do_POST(self):
        if self.path.startswith('/api'):
            if self.path == '/api/echo':
                self.echo()
                return
            
            self.send_error(404, 'Service "{}" not found'.format(self.path))
            return
        
        self.send_error(404, 'Path "{}" not found.'.format(self.path))


#from socketserver import ThreadingMixIn
#class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
#    """Multithreading HTTP server."""


def main():
    parser = argparse.ArgumentParser(description=PRODUCT_DESCRIPTION)
    parser.add_argument("--http", help="http address", default=":9000")
    parser.add_argument("-d", "--directory", help="static file directory", default="static")
    parser.add_argument("--logfile", help="file to log", default=None)
    args = parser.parse_args()

    logging.basicConfig(filename=args.logfile, format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S',
                        level=logging.INFO)

    (hostIP, port) = args.http.split(":", 2)
    s = ThreadingHTTPServer((hostIP, int(port)), partial(MiniHTTPServer,
                                                    static_directory=args.directory))

    logging.info("{}: v{}\n".format(PRODUCT_NAME, PRODUCT_VER))

    try:
        logging.info("Listen: {}:{}".format(hostIP, port))
        s.serve_forever()
    except KeyboardInterrupt:
        logging.info("Interrupt by user")

    logging.info("Exit")
    s.server_close()

if __name__ == '__main__':
    main()
