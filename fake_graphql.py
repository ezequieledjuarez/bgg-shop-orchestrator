from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(500)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(b'{"error":"simulated upstream failure","detail":"fake body"}')

if __name__ == '__main__':
    HTTPServer(('0.0.0.0',9001), H).serve_forever()
