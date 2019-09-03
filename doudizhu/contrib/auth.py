import jwt

AUTHORIZATION_HEADER = 'Authorization'
SECRET_KEY = "my_secret_key"
INVALID_HEADER_MESSAGE = "invalid header authorization"
MISSING_AUTHORIZATION_KEY = "Missing authorization"

jwt_options = {
    'verify_signature': True,
    'verify_exp': True,
    'verify_nbf': False,
    'verify_iat': True,
    'verify_aud': False
}


def is_valid_header(parts):
    """
        Validate the header
    """
    # authorization method
    if parts[0].lower() != 'bearer':
        return False
    elif len(parts) == 1:
        return False
    elif len(parts) > 2:
        return False

    return True


def handle_auth_error(handler, message):
    # authorization error code 401
    handler._transforms = []
    handler.set_status(401)
    handler.write(message)
    handler.finish()


def jwt_auth(handler_class):

    def wrap_execute(handler_execute):

        def require_auth(handler, kwargs):
            auth = handler.request.headers.get(AUTHORIZATION_HEADER)
            if auth:
                parts = auth.split()
                if is_valid_header(parts):
                    token = parts[1]
                    try:
                        jwt.decode(token, SECRET_KEY, options=jwt_options)
                    except jwt.PyJWTError as err:
                        handle_auth_error(handler, str(err))
                else:
                    handle_auth_error(handler, INVALID_HEADER_MESSAGE)
            else:
                handler._transforms = []
                handler.write(MISSING_AUTHORIZATION_KEY)
                handler.finish()

            return True

        def _execute(self, transforms, *args, **kwargs):
            try:
                require_auth(self, kwargs)
            except jwt.PyJWTError:
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class
