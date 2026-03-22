
import http.server
import socketserver
import socket
from functools import partial

class RobustHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, socket.error):
            # Silently ignore connection errors
            pass
    
    def log_message(self, format, *args):
        # Reduce logging noise
        if not any(x in format % args for x in ['ConnectionResetError', 'BrokenPipeError']):
            super().log_message(format, *args)

with socketserver.TCPServer(("127.0.0.1", 8080), RobustHTTPRequestHandler) as httpd:
    print("Frontend server running on http://127.0.0.1:8080")
    httpd.serve_forever()
