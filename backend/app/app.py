from flask import Flask, make_response, jsonify, request, session
from os import getenv, path
from werkzeug.utils import secure_filename
import pymongo
from pymongo.collection import Collection
from datetime import datetime

import json
from bson import ObjectId

from parse_csv import parse_csv

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = getenv("UPLOAD_FOLDER")
app.secret_key = 'hello'

def get_collection() -> Collection:
    client = pymongo.MongoClient(getenv("MONGO_URL"))
    db = client["DoF-gratuity"]
    collection = db["DoF"]
    return collection

# TO-DO: Make sure its admin locked
@app.route("/upload", methods=["POST"])
def upload_csv():
    f = request.files.get('file')
    if f == None:
        return jsonify({"message":"no file in the body of request found"})
    data_filename = secure_filename(f.filename)
    f.save(path.join(app.config['UPLOAD_FOLDER'],data_filename))
    session['uploaded_data_file_path'] = path.join(app.config['UPLOAD_FOLDER'],data_filename)

    inputs = parse_csv("./datastore/"+data_filename)

    collection = get_collection()

    for input in inputs:
        details = get_collection().find_one({"Ultimate_Recipient":input.get("Ultimate_Recipient")})
        if details != None:
            # find the Ultimate_Recipient, append gift, sum the number of accepted offer, update total gift and total accepted gift
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
    if page <= 1:
        page = 1

    # Dont want to show all just stats
    result = get_collection().find({}).skip((page-1)*paginate).limit(paginate)
    resp = result.to_list()
    return jsonify(json.dumps(obj=resp,cls=JSONEncoder))

@app.route("/member/<string:id>")
def get_specific_member(id):
    collection = get_collection()

    #TO-DO Deduping entries (TECH DIFF)
    start = request.args.get(key="start",default="01/01/1000")
    end = request.args.get(key="end",default=datetime.today().strftime('%d/%m/%Y'))

    start_isotime = datetime.strptime(start, "%d/%m/%Y").isoformat()
    end_isotime = datetime.strptime(end, "%d/%m/%Y").isoformat()

    resp = collection.aggregate([{"$match":{"_id":ObjectId(id)}},\
            {"$unwind": "$Gifts"},\
            {"$match":{"Gifts.Date_of_Offer":{"$gt":start_isotime,"$lt":end_isotime}}},\
            ])\
            .to_list()
    if resp == None:
        return jsonify({"message":"id not found"})

    return jsonify(json.dumps(obj=resp,cls=JSONEncoder))

@app.route("/Business_Area", methods=["GET"])
def get_all_business_area():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1

    # Group by Business_Area, sum the Total_Gifts, sum Total_Accepted_Gifts
    result = get_collection().aggregate(pipeline=[{"$group": {"_id": "$Business_Area","Total_Gifts":{"$sum": "$Total_Gifts"},"Total_Accepted_Gifts":{"$sum":"$Total_Accepted_Gifts"}}}]).to_list()
    return jsonify(json.dumps(obj=result,cls=JSONEncoder))

@app.route("/Business_Area/<string:name>")
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
    return jsonify(json.dumps(obj=resp,cls=JSONEncoder))

# SOLUTION FROM https://vuyisile.com/dealing-with-the-type-error-objectid-is-not-json-serializable-error-when-working-with-mongodb/
class JSONEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, ObjectId):
            return str(item)
        return json.JSONEncoder.default(self, item)
