import logging


WEBSOCKET_TIMEOUTS = {'timeout': 2.0, 'heartbeat': 2.0}
HTTP_SESSION_TIMEOUTS = {'read_timeout': 2.0}


class RequestLogger(logging.LoggerAdapter):
    def __init__(self, logger, request):
        super().__init__(logger, None)
        self.prefix = f"[{request.url.path} {request.transport.get_extra_info('peername')}] "

    def process(self, msg, kwargs):
        return self.prefix + msg, kwargs


def setup_logging(verbosity):
    levels = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(verbosity, len(levels))],
                        format="[%(levelname)-7s] %(name)s %(message)s")
