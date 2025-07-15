from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello from simple server on port 30010!')

print("Starting simple HTTP server on port 30010...")
httpd = HTTPServer(('0.0.0.0', 30010), SimpleHTTPRequestHandler)
print("Server started. Use Ctrl+C to stop.")
httpd.serve_forever()
