from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional, Awaitable

from tornado.escape import json_encode, json_decode
from tornado.web import RequestHandler, HTTPError

from contrib.db import AsyncConnection


class BaseHandler(RequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = {}

    def prepare(self) -> Optional[Awaitable[None]]:
        required_fields = getattr(self, 'required_fields')
        if required_fields and self.request.headers['Content-Type'] == 'application/json':
            args = json_decode(self.request.body)
            for field in required_fields:
                value = args.get(field, '').strip()
                if value:
                    args['field'] = value
                else:
                    raise HTTPError(403, f'The field "{field}" is required')
            self.args = args

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def set_current_user(self, uid, username):
        info = {
            'uid': uid,
            'username': username,
        }
        self.set_secure_cookie('user', json_encode(info))

    def on_finish(self):
        # self.session.flush()
        pass

    @property
    def db(self) -> AsyncConnection:
        return self.application.db

    @property
    def executor(self) -> ThreadPoolExecutor:
        return self.application.executor

    @property
    def client_ip(self):
        headers = self.request.headers
        return headers.get('X-Forwarded-For', headers.get('X-Real-Ip', self.request.remote_ip))
