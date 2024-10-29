from flask import Flask, make_response, jsonify, request, session
from os import getenv, path
from pymongo.common import WAIT_QUEUE_TIMEOUT
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime, UTC, timedelta
from functools import wraps
from jwt import encode
import json
from bson import ObjectId
from parse_csv import parse_csv
from hashlib import sha256 

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = getenv("UPLOAD_FOLDER")
# change to get from env var
app.secret_key = 'hello'

client = MongoClient(getenv("MONGO_URL"))
db = client["DoF-gratuity"]
DoF = db["DoF"]
User = db["User"]

def ensure_root():
    if(User.find_one(filter={"username": "root"}) == None):
        User.insert_one({"username": "root", "password": sha256("password".encode("UTF-8")).hexdigest(), "is_admin": True})
ensure_root()

def get_collection() -> Collection:
    client = MongoClient(getenv("MONGO_URL"))
    db = client["DoF-gratuity"]
    collection = db["DoF"]
    return collection

# TO-DO: Make sure its admin locked
@app.route("/upload", methods=["POST"])
def upload_csv():
    f = request.files.get('file')
    if f == None:
        return jsonify({"message":"no params name file in the body of request found"})
    data_filename = secure_filename(f.filename)
    f.save(path.join(app.config['UPLOAD_FOLDER'],data_filename))
    session['uploaded_data_file_path'] = path.join(app.config['UPLOAD_FOLDER'],data_filename)

    inputs = parse_csv("./datastore/"+data_filename)

    collection = get_collection()

    for input in inputs:
        details = get_collection().find_one({"Ultimate_Recipient":input.get("Ultimate_Recipient")})
        if details != None:
            # find the Ultimate_Recipient, append gift, sum the number of accepted offer, update total gift and total accepted gift
            # TO-DO: DEDUPE ENTRIES BASED ON CHECKSUM
            collection.update_one(filter={"Ultimate_Recipient":input.get("Ultimate_Recipient")},\
                    update={"$push":{"Gifts": input.get("Gifts")[0]},\
                    "$inc": {"Total_Gifts": input.get("Total_Gifts"),"Total_Accepted_Gifts": input.get("Total_Accepted_Gifts")},\
                    })
        else:
            collection.insert_one(input)
    # TO-DO: On success delete the csv (Debatable on this)
    if(collection != None):
       return jsonify({"success": True})
    return jsonify({"success":False})

@app.route("/member", methods=["GET"])
def get_all_member():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page < 1:
        page = 1
    result = get_collection().find({}).skip((page-1)*paginate).limit(paginate).to_list()
    return jsonify(json.dumps(obj=result,cls=JSONEncoder))

@app.route("/member/<string:id>",methods=["GET"])
def get_specific_member(id):
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1

    start = request.args.get(key="start",default="01/01/1000")
    end = request.args.get(key="end",default=datetime.today().strftime('%d/%m/%Y'))
    start_isotime = datetime.strptime(start, "%d/%m/%Y").isoformat()
    end_isotime = datetime.strptime(end, "%d/%m/%Y").isoformat()

    resp = DoF.aggregate([{"$match":{"_id":ObjectId(id)}},\
            {"$unwind": "$Gifts"},\
            {"$match":{"Gifts.Date_of_Offer":{"$gt":start_isotime,"$lt":end_isotime}}},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate},\
            ])\
            .to_list()
    if resp == None:
        return jsonify({"message":"id not found"})

    for e,_ in enumerate(resp):
        resp[e]["_id"]=str(resp[e]["_id"])

    return make_response(jsonify(resp),200)

@app.route("/businessArea", methods=["GET"])
def get_all_business_area():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1

    # Group by Business_Area, sum the Total_Gifts, sum Total_Accepted_Gifts
    result = get_collection().aggregate(pipeline=[{"$group": \
            {"_id": "$Business_Area",\
            "Total_Gifts":{"$sum": "$Total_Gifts"},\
            "Total_Accepted_Gifts":{"$sum":"$Total_Accepted_Gifts"}}},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate},\
            ]).to_list()
    return jsonify(json.dumps(obj=result,cls=JSONEncoder))

@app.route("/businessArea/<string:name>",methods=["GET"])
def get_specific_Business_Area(name):
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1

    start = request.args.get(key="start",default="01/01/1000")
    end = request.args.get(key="end",default=datetime.today().strftime('%d/%m/%Y'))
    start_isotime = datetime.strptime(start, "%d/%m/%Y").isoformat()
    end_isotime = datetime.strptime(end, "%d/%m/%Y").isoformat()

    # return all member of that business area and then calculate their accepted offer and total offer
    resp = get_collection().aggregate([{"$match":{"Business_Area":name}},\
            {"$unwind": "$Gifts"},\
            {"$match":{"Gifts.Date_of_Offer":{"$gt":start_isotime,"$lt":end_isotime}}},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate}
            ])\
            .to_list()
    if resp == None:
        return jsonify({"message":"Business Area not found"})
    return make_response(json.dumps(obj=resp,cls=JSONEncoder),200)

@app.route("/business",methods=["GET"])
def get_business():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1
    # Unwind gift, group business, count all offer, count accepted offer
    result = get_collection().aggregate(pipeline=[\
            {"$unwind":"$Gifts"},\
            {"$group":\
            {"_id":"$Gifts.Offered_From",\
            "Total_Offer":{"$sum":1},\
            "Total_Accepted_Offer":{"$sum":{"$cond": [{"$eq":["$Gifts.Action_Taken","Accepted"]},1,0]}}\
            }},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate}\
            ]).to_list()
    return jsonify(json.dumps(cls=JSONEncoder, obj=result))

@app.route("/business/<string:business>",methods=["GET"])
def get_specific_business(business):
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1

    start = request.args.get(key="start",default="01/01/1000")
    end = request.args.get(key="end",default=datetime.today().strftime('%d/%m/%Y'))
    start_isotime = datetime.strptime(start, "%d/%m/%Y").isoformat()
    end_isotime = datetime.strptime(end, "%d/%m/%Y").isoformat()

    # unwind gifts, match Gifts.Offered_From, Order by date
    result = get_collection().aggregate(pipeline=[\
            {"$unwind":"$Gifts"},\
            {"$match": {"Gifts.Offered_From":business, "Gifts.Date_of_Offer": {"$lt": end_isotime, "$gt": start_isotime}}},\
            {"$skip":(page-1)*paginate},\
            {"$limit": paginate},\
            ]).to_list()
    return jsonify(json.dumps(obj=result, cls=JSONEncoder))

@app.route("/user/login", methods=["GET"])
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

    return make_response(jsonify({"token":encode(payload={"username":username, "exp": datetime.now(UTC) + timedelta(minutes=30)},key=app.secret_key)}),200)

@app.route("/user/register", methods=["POST"])
def register():
    username = request.headers.get("username")
    password = request.headers.get("password")
    description = request.form.get("description")
    if username == "root":
        return make_response(jsonify({"message":"username can't be root"}))
    if username == None or password == None:
        make_response(jsonify({"message":"bad request username and password can't be null"}),400)
    # DO a check on their name to make no duplicate
    userid = User.insert_one({"username": username, "password": sha256(password.encode("UTF-8")).hexdigest(),"description":description, "is_admin": False}).inserted_id
    return make_response(jsonify({"message": "user "+str(userid)+" added"}), 200)

# ROOT ONLY ENDPOINT
@app.route("/user/update/<string:id>",methods=["POST"])
def update(id):
    key = request.headers.get("key")
    value = request.headers.get("value")
    if key == None or value == None:
        return make_response(jsonify({"message": "bad request both key and value must be filled"}, 400))
    User.update_one(filter={"_id":ObjectId(id)},update={"$set":{key:value}})

    # REDIRECT BACK TO BEFORE OR /users/admin
    return make_response(jsonify({"message": "user " + id + "has been updated"}),200)

@app.route("/user/admins")
def get_admin():
    users = User.find({}).to_list()
    for i,_ in enumerate(users):
        users[i]["_id"] = str(users[i]["_id"])
    return make_response(jsonify(users))

# SOLUTION FROM https://vuyisile.com/dealing-with-the-type-error-objectid-is-not-json-serializable-error-when-working-with-mongodb/
class JSONEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, ObjectId):
            return str(item)
        return json.JSONEncoder.default(self, item)
