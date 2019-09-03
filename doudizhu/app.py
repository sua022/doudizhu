import asyncio
import logging.config
from concurrent.futures import ThreadPoolExecutor

import tornado.web
import tornado.websocket

from apps.urls import url_patterns
from contrib.db import AsyncConnection
from settings import config

logging.config.dictConfig(config.LOGGING)

try:
    import uvloop
    uvloop.install()
except ModuleNotFoundError:
    pass


class Application(tornado.web.Application):
    settings = {
        'debug': config.DEBUG,
        'cookie_secret': config.SECRET_KEY,
        'xsrf_cookies': getattr(config, 'XSRF_COOKIES', True),
        'gzip': getattr(config, 'GZIP', True),
        'autoescape': getattr(config, 'AUTO_ESCAPE', 'xhtml_escape'),
        'template_path': config.TEMPLATE_ROOT,
        'static_path': config.STATIC_ROOT,
        'static_url_prefix': config.STATIC_URL,
    }

    def __init__(self):
        super().__init__(url_patterns, **self.settings)
        self.db = AsyncConnection(**config.DATABASE)
        self.executor = ThreadPoolExecutor(max_workers=10)


def make_app(port):
    app = Application()
    app.listen(port)
    return app


def main():
    make_app(config.PORT)
    logging.info(f'server on http://127.0.0.1:{config.PORT}')
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
