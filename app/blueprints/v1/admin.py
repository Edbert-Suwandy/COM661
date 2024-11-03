from flask import make_response, jsonify, request, session, Blueprint
from jwt import encode
from bson import ObjectId
from hashlib import sha256
from datetime import datetime,UTC, timedelta
from os import path
from werkzeug.utils import secure_filename 

from parse_csv import parse_csv
from globals import Blacklist, DoF, User, secret_key, upload_folder 
from decorator import admin_required, sudo_required

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/login", methods=["GET"])
def login():
    try:
        auth = request.authorization
        username = auth.username
        password = auth.password
    except:
        return make_response(jsonify({"message": "username and password field can't be null"}),400)
    if not auth or not password or not username:
        make_response(jsonify({"message":"bad request"}),400)

    resp = User.find_one({"username":username})
    if resp == None:
        return make_response(jsonify({"message":"user not found"}))
    if sha256(password.encode("UTF-8")).hexdigest() != resp.get("password"):
        return make_response(jsonify({"message": "can't verify"}),401)

    return make_response(jsonify({"token":encode(payload=\
            {"username":username,\
            "exp": datetime.now(UTC) + timedelta(minutes=30),\
            "is_admin":bool(resp.get("is_admin")),\
            "is_sudo":bool(resp.get("is_sudo"))},key=secret_key)})\
            ,200)

@admin_bp.route("/logout", methods=["PUT"])
def logout():
    token = request.headers.get("token")
    if username == None or password == None:
        return make_response(jsonify({"message":"bad request username and password can't be null"}),400)
    
    Blacklist.insert_one({"token": token})
    return make_response(jsonify({"message":"successfully logged out"}))

@admin_bp.route("/register", methods=["POST"])
def register():
    username = request.headers.get("username")
    password = request.headers.get("password")
    description = request.form.get("description")

    if not username or not password:
        return make_response(jsonify({"message":"bad request username and password can't be null"}),400)
    if User.find_one(filter={"username": username}):
        return make_response(jsonify({"message": "username taken"}),400)
    userid = User.insert_one({"username": username, "password": sha256(password.encode("UTF-8")).hexdigest(),"description":description, "is_admin": False}).inserted_id
    return make_response(jsonify({"message": "user added","id": str(userid)}), 201)

@admin_bp.route("/<string:id>/update",methods=["PUT"])
@admin_required
@sudo_required
def update(id):
    key = request.headers.get("key")
    value = request.headers.get("value")
    if not key or not value:
        return make_response(jsonify({"message": "bad request both key and value must be filled"}, 400))
    resp = User.update_one(filter={"_id":ObjectId(id)},update={"$set":{key:value}}).acknowledged

    # REDIRECT BACK TO BEFORE OR /users/admin_bp
    if not resp:
        return make_response(jsonify({"message", "query not acknowledged by db"}),500)
    return make_response(jsonify({"message": "user " + str(id) + "has been updated"}),201)

@admin_bp.route("/<string:id>/delete",methods=["DELETE"])
@admin_required
@sudo_required
def delete(id):
    resp = User.delete_one(filter={"_id": ObjectId(id)}).acknowledged
    if resp:
        return make_response(jsonify({"message": "user " + str(id) + "has been deleted"}),204)
    else:
        return make_response(jsonify({"message", "query not acknowledged by db"}),500)

@admin_bp.route("/", methods=["GET"])
def get_admin():
    users = User.find({},{"description":0,"password":0}).to_list()
    for i,_ in enumerate(users):
        users[i]["_id"] = str(users[i]["_id"])
    return make_response(jsonify(users),200)



@admin_bp.route("/upload", methods=["POST"])
@admin_required
def upload_csv():     
    f = request.files.get('file')
    if not f:
        return make_response(jsonify({"message":"no params name file in the body of request found"}),400)
    data_filename = secure_filename(f.filename)
    f.save(path.join(upload_folder,data_filename))
    session['uploaded_data_file_path'] = path.join(secret_key,data_filename)

    inputs = parse_csv("./datastore/"+data_filename)

    for input in inputs:
        doc = DoF.find_one({"Ultimate_Recipient": input.get("Ultimate_Recipient"), "Gifts": {"$elemMatch": {"hash": input.get("Gifts")[0].get("hash")}}})
        if doc == None:
            DoF.update_one(\
                    filter={"Ultimate_Recipient": input.get("Ultimate_Recipient")},\
                    update={\
                    "$setOnInsert": {\
                    "Ultimate_Recipient": input.get("Ultimate_Recipient"),\
                    "Business_Area": input.get("Business_Area")\
                    },
                    "$push": {"Gifts": input.get("Gifts")[0]},\
                    "$inc": {"Total_Gifts": input.get("Total_Gifts"), "Total_Accepted_Gifts": input.get("Total_Accepted_Gifts")}\
                    },\
                    upsert=True\
                    )

    return make_response(jsonify({"message": "successfully entered"}),201)
