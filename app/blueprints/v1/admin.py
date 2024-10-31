from flask import make_response, jsonify, request, session, Blueprint
from jwt import encode
from bson import ObjectId
from hashlib import sha256
from datetime import datetime,UTC, timedelta
from os import path
from werkzeug.utils import secure_filename 

from parse_csv import parse_csv
from globals import DoF, User, secret_key, upload_folder 
from decorator import admin_required, sudo_required

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/login", methods=["GET"])
def login():
    auth = request.authorization
    username = auth.username
    password = auth.password

    if auth == None or username == None or password == None:
        make_response(jsonify({"message":"bad request"}),400)
    resp = User.find_one({"username":username})
    if resp == None:
        return make_response(jsonify({"message":"user not found"}))
    if sha256(password.encode("UTF-8")).hexdigest() != resp.get("password"):
        return make_response(jsonify({"message": "can't verify"}),401)

    return make_response(jsonify({"token":encode(payload=\
            {"username":username,\
            "exp": datetime.now(UTC) + timedelta(minutes=30),\
            "is_admin":str(resp.get("is_admin")),\
            "is_sudo":str(resp.get("is_sudo"))},key=secret_key)})\
            ,200)

@admin_bp.route("/register", methods=["POST"])
def register():
    username = request.headers.get("Username")
    password = request.headers.get("Password")
    description = request.form.get("description")
    if username == "root":
        return make_response(jsonify({"message":"username can't be root"}),400)
    if username == None or password == None:
        make_response(jsonify({"message":"bad request username and password can't be null"}),400)

    # TO-DO: Fix this shit idk why man
    if User.find_one(filter={"username": username}) != None:
        make_response(jsonify({"message": "username taken"}),400)
    userid = User.insert_one({"username": username, "password": sha256(password.encode("UTF-8")).hexdigest(),"description":description, "is_admin": False}).inserted_id
    return make_response(jsonify({"message": "user added","id": str(userid)}), 201)

@admin_bp.route("/<string:id>/update",methods=["PUT"])
@admin_required
@sudo_required
def update(id):
    key = request.headers.get("key")
    value = request.headers.get("value")
    if key == None or value == None:
        return make_response(jsonify({"message": "bad request both key and value must be filled"}, 400))
    resp = User.update_one(filter={"_id":ObjectId(id)},update={"$set":{key:value}},upsert=True).acknowledged

    # REDIRECT BACK TO BEFORE OR /users/admin_bp
    if resp:
        return make_response(jsonify({"message": "user " + str(id) + "has been updated"}, {"raw": resp}),201)
    else:
        return make_response(jsonify({"message", "query not acknowledged by db"}),500)

@admin_bp.route("/<string:id>/delete",methods=["DELETE"])
@admin_required
@sudo_required
def delete(id):
    resp = User.delete_one(filter={"_id": ObjectId(id)}).acknowledged
    # REDIRECT BACK TO BEFORE OR /users/admin

    if resp:
        return make_response(jsonify({"message": "user " + str(id) + "has been deleted"}),200)
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
    if f == None:
        return jsonify({"message":"no params name file in the body of request found"})
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
