"""Syslog UDP receiver for LogSweeper."""

import logging
import socketserver

logger = logging.getLogger(__name__)


class SyslogUDPHandler(socketserver.BaseRequestHandler):
    """Simple UDP syslog handler."""

    callback = None

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        if self.callback:
            self.callback(data)
        else:
            logger.debug("Syslog received (no callback): %s", data[:200])


def start_syslog_server(host: str = "0.0.0.0", port: int = 1514, callback=None) -> socketserver.UDPServer:
    """Start a UDP syslog listener. Returns the server instance."""
    SyslogUDPHandler.callback = callback
    server = socketserver.UDPServer((host, port), SyslogUDPHandler)
    logger.info("Syslog server listening on %s:%d", host, port)
    return server
