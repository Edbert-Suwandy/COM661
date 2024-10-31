from flask import make_response,request 
from functools import wraps
from jwt import decode

from globals import secret_key 

def sudo_required(func):
    @wraps(func)
    def sudo_required_wrapper(*args, **kwargs):
        token = request.headers.get("x-access-header")
        if token == None:
            return make_response({"message": "auth token required"},401)
        data = decode(jwt=token, key=secret_key,algorithms=["HS256"])
        
        if not bool(data.get("is_sudo")):
            return make_response({"message": "sudo permission is required"},401)

        return func(*args, **kwargs)
    return sudo_required_wrapper

def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers.get("x-access-header")
        if token == None:
            return make_response({"message": "auth token required"},401)
        try:
            data = decode(token, secret_key, ["HS256"])
            # make sure token is not invalidated
        except:
            return make_response({"message": "token is invalid"}, 401)
        
        if not data.get("is_admin"):
            return make_response({"message": "no admin privilage"},401)

        return func(*args, **kwargs)
    return admin_required_wrapper
