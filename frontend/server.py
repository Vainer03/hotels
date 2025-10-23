import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Frontend server running at http://localhost:{PORT}")
        print(f"Serving files from: {os.path.abspath(DIRECTORY)}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()