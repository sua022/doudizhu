import json
from datetime import datetime, timedelta

import bcrypt
import jwt
import pymysql
import tornado
from tornado.web import HTTPError

from contrib.auth import SECRET_KEY
from contrib.handlers import BaseHandler


class HomeHandler(BaseHandler):

    def get(self):
        if not self.get_cookie("_csrf"):
            self.set_cookie("_csrf", self.xsrf_token)
        # user = xhtml_escape(self.current_user or '')
        user = self.current_user or ''
        self.render('poker.html', user=user)


class AuthHandler(tornado.web.RequestHandler):
    def prepare(self):
        self.encoded = jwt.encode(
            {'some': 'payload', 'exp': datetime.utcnow() + timedelta(seconds=600)},
            SECRET_KEY,
            algorithm='HS256'
        )

    def get(self, *args, **kwargs):
        response = {'token': self.encoded.decode('ascii')}
        self.write(response)


class SignupHandler(BaseHandler):

    required_fields = ('email', 'username', 'password', 'password_repeat')

    async def post(self):
        email = self.args['email']
        username = self.args.get('username')
        password = self.args.get('password')
        password_repeat = self.args.get('password_repeat')
        if password == password_repeat:
            try:
                user_id = await self.create_account(username, email, password)
                self.set_current_user(user_id, username)
                self.set_header('Content-Type', 'application/json')
                self.write({'uid': user_id, 'username': username})
            except pymysql.IntegrityError as e:
                if await self.account_exists(email):
                    raise HTTPError(403, 'An account with this email address already exists.')
                else:
                    raise e
        else:
            raise HTTPError(403, 'The password does not match')

    async def create_account(self, username, email, password) -> int:
        # password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        password = await self.executor.submit(bcrypt.hashpw, password.encode('utf8'), bcrypt.gensalt())
        return await self.db.insert('INSERT INTO account (email, username, password, ip_addr) VALUES (%s,%s,%s,%s)',
                                   email, username, password, self.client_ip)

    async def account_exists(self, email) -> bool:
        account = await self.db.fetchone('SELECT id FROM account WHERE email=%s', email)
        print(account)
        return True if account else False


class LoginHandler(BaseHandler):

    async def post(self):
        email = self.get_argument('email')
        password = self.get_argument("password")
        account = await self.db.fetchone('SELECT id, username, password FROM account WHERE email=%s', email)
        # password = bcrypt.hashpw(password.encode('utf8'), account.get('password'))
        can_login = await self.executor.submit(bcrypt.checkpw, password.encode('utf8'), account.get('password'))

        self.set_header('Content-Type', 'application/json')
        if can_login:
            self.set_current_user(account.get('id'), account.get('username'))
            self.redirect(self.get_argument("next", "/"))
        else:
            self.write({'errcode': 1, 'errmsg': 'username or password was wrong!'})


class LogoutHandler(BaseHandler):

    def post(self):
        self.clear_cookie('user')
        self.redirect(self.get_argument("next", "/"))
