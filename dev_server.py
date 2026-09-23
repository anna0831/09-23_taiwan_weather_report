"""Local Development Server for Taiwan Weather Forecast Vercel App.

Serves static files from `public/` and routes `/api/weather` to `api/weather.py`.
Runs on http://localhost:3000
"""

import sys
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"

# Import Vercel handler
sys.path.insert(0, str(BASE_DIR))
from api.weather import handler as ApiHandler


class VercelDevServerHandler(SimpleHTTPRequestHandler):
    """Local simulation of Vercel routing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            ApiHandler.do_OPTIONS(self)
        else:
            super().do_OPTIONS()

    def do_GET(self):
        parsed = urlparse(self.path)
        # 路由到 API
        if parsed.path.startswith("/api/weather") or parsed.path == "/api":
            ApiHandler.do_GET(self)
        else:
            # 路由到 public 靜態資源
            if parsed.path == "/" or parsed.path == "":
                self.path = "/index.html"
            super().do_GET()


def run_server(port=3000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, VercelDevServerHandler)
    print(f"\n=======================================================")
    print(f" [Vercel Local Dev Server] Running at: http://localhost:{port}")
    print(f" Web Dashboard: http://localhost:{port}/")
    print(f" Weather API:   http://localhost:{port}/api/weather")
    print(f" Press Ctrl+C to stop.")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
