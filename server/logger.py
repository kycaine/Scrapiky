"""Colored console logger setup."""

import logging

ANSI = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[1;31m", # bold red
    "RESET":    "\033[0m",
}

class _AnsiFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = ANSI.get(record.levelname, ANSI["RESET"])
        record.levelname = f"{color}[{record.levelname}]{ANSI['RESET']}"
        return super().format(record)

def setup_logger(name: str = "gmaps") -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(_AnsiFormatter("%(levelname)s %(asctime)s  %(message)s", datefmt="%H:%M:%S"))
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

log = setup_logger()

# WebSocket log interception mechanism
_ws_callbacks = []

def add_ws_callback(callback):
    _ws_callbacks.append(callback)

def remove_ws_callback(callback):
    if callback in _ws_callbacks:
        _ws_callbacks.remove(callback)

class WsLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        for cb in _ws_callbacks:
            # We assume cb is a non-blocking or scheduled async call
            cb(msg)

ws_handler = WsLogHandler()
ws_handler.setFormatter(_AnsiFormatter("%(levelname)s %(asctime)s  %(message)s", datefmt="%H:%M:%S"))
log.addHandler(ws_handler)
