#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import signal
import sys
from urllib.parse import urlparse, parse_qs
import time
import json


PORT = 8080
COMPONENT_LIST = [
    "sysbench-qm",
    "ffi_client-qm",
    "sysbench",
    "ffi_server",
    "cyclictest",
    "stress-ng",
]


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/status"):
            self.handle_api_stautus()
        elif self.path.startswith("/api/qmcpuweight"):
            self.handle_api_cpuweight_get()
        elif self.path == "/":
            self.serve_html("index.html")
        else:
            self.serve_html(self.path[1:])  # Remove leading slash

    def do_POST(self):
        if self.path.startswith("/api/component/"):
            self.handle_api_component()
        elif self.path.startswith("/api/qmcpuweight"):
            self.handle_api_cpuweight_set()
        else:
            self.send_error(404, "Endpoint not found")

    def serve_html(self, file_name):
        try:
            with open(file_name, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def handle_api_component(self):
        # Parse the path to get component
        parsed = urlparse(self.path)
        parts = parsed.path.split("/")
        component = parts[-1]
        action = parse_qs(parsed.query).get("action", [None])[0]

        if len(parts) != 4:
            self.send_error(400, "Invalid API path")
            return

        if action is None:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing action parameter")
            return

        # Handle different components and actions
        try:
            if component not in COMPONENT_LIST:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(f"Unknown component: {component}".encode())
                return

            if component.endswith("-qm"):
                cmd = [
                    "podman",
                    "exec",
                    "qm",
                    "systemctl",
                    f"{action}",
                    component.removesuffix("-qm"),
                ]
            else:
                cmd = ["systemctl", f"{action}", f"{component}"]

            log_cmd(cmd)

            if get_os_release_id() == "autosd":
                subprocess.run(cmd, check=True)
            else:
                time.sleep(2)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"{action} {component} successful".encode())

        except subprocess.CalledProcessError as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Command failed: {e}".encode())

    def handle_api_stautus(self):
        response = {}

        for component in COMPONENT_LIST:
            response[component] = is_service_active(component)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def handle_api_cpuweight_get(self):
        cmd = ["systemctl", "show", "qm", "-p", "CPUWeight"]
        log_cmd(cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            # result looks like: CPUWeight=100
            cpu_weight = result.stdout.strip().split("=")[1]
            if cpu_weight == "[not set]":
                cpu_weight = ""
        except subprocess.CalledProcessError:
            return self.send_error(400, "CPUWeight get error")

        response = {}
        response["weight"] = cpu_weight
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def handle_api_cpuweight_set(self):
        parsed = urlparse(self.path)
        weight = parse_qs(parsed.query, True).get("weight", [None])[0]
        if weight == "unset":
            weight = ""

        cmd = [
            "systemctl",
            "set-property",
            "qm.service",
            f"CPUWeight={weight}",
        ]
        log_cmd(cmd)

        if get_os_release_id() == "autosd":
            subprocess.run(cmd, check=True)
        else:
            time.sleep(2)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"QM CPU Weight Set to {weight}".encode())


def log_cmd(cmd):
    cmd_str = " ".join(cmd)
    print(f"Executing: [{cmd_str}]")


def signal_handler(sig, frame):
    print("\nShutting down server gracefully...")
    if "httpd" in globals():
        httpd.server_close()
        print("Server stopped.")
    sys.exit(0)


def get_os_release_id():
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.strip().split("=")[1].strip('"')
    except FileNotFoundError:
        return None


def is_service_active(component):
    if get_os_release_id() != "autosd":
        time.sleep(0.2)
        return False

    if component.endswith("-qm"):
        cmd = [
            "podman",
            "exec",
            "qm",
            "systemctl",
            "is-active",
            component.removesuffix("-qm"),
        ]
    else:
        cmd = ["systemctl", "is-active", component]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() == "active"
    except subprocess.CalledProcessError:
        return False


def run():
    # Register signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    port = PORT

    # make port different for easy debugging
    # if get_os_release_id() != "autosd":
    #    port += 1

    server_address = ("", port)
    global httpd
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"Serving on http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
