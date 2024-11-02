from flask import make_response,request, jsonify 
from functools import wraps
from jwt import decode

from globals import secret_key, Blacklist 

def sudo_required(func):
    @wraps(func)
    def sudo_required_wrapper(*args, **kwargs):
        token = request.headers.get("x-access-header")
        if token == None:
            return make_response(jsonify({"message": "auth token required"}),401)
        data = decode(jwt=token, key=secret_key,algorithms=["HS256"])
        
        if not data.get("is_sudo") :
            return make_response(jsonify({"message": "sudo permission is required is_sudo: "+str(data.get("is_sudo"))}),401)

        return func(*args, **kwargs)
    return sudo_required_wrapper

def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers.get("x-access-header")
        if token == None:
            return make_response(jsonify({"message": "auth token required"}),401)
        try:
            data = decode(token, secret_key, ["HS256"])
        except:
            return make_response(jsonify({"message": "token is invalid"}), 401)

        if Blacklist.find_one({"token": token}):
            return make_response(jsonify({"message":"please login again"}),401)

        # I know this looks dumb but for some reason it does not do boolean operations properly
        if not data.get("is_admin"):
            return make_response(jsonify({"message": "no admin privilage: is_admin: "+str(data.get("is_admin"))}),401)

        return func(*args, **kwargs)
    return admin_required_wrapper
