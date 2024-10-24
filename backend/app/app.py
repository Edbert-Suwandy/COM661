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
@app.route('/env', methods=["GET"])
def creds():
    return make_response(jsonify({
        "MONGO_USER":getenv("MONGO_USER"),
        "MONGO_PASSWORD":getenv("MONGO_PASSWORD"),
        "MONGO_URL":getenv("MONGO_URL")
    }))

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
            collection.update_one(filter={"Ultimate_Recipient": input.get("Ultimate_Recipient")},update={"$push": {"Gifts":input.get("Gifts")[0]}})
        else:
            collection.insert_one(input)

    # TO-DO: On success delete the csv (Debatable on this)
    if(collection != None):
       return jsonify({"success": True})
    return jsonify({"success":False})

@app.route("/member", methods=["GET"])
def get_all():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate <= 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1

    result = get_collection().find({}).skip((page-1)*paginate).limit(paginate)
    resp = result.to_list()
    return jsonify(json.dumps(obj=resp,cls=JSONEncoder))

@app.route("/member/<string:id>")
def get_specific(id):
    collection = get_collection()

    #TO-DO Deduping entries (TECH DIFF)
    #TO-DO implement start and end
    start = request.args.get(key="start",default="01/01/1000")
    end = request.args.get(key="end",default=datetime.today().strftime('%d/%m/%Y'))

    start_isotime = datetime.strptime(start, "%d/%m/%Y").isoformat()
    end_isotime = datetime.strptime(end, "%d/%m/%Y").isoformat()

    # This look hidious but lets do it for performance maybe but deffo for score :D
    resp = collection.aggregate([{"$match":{"_id":ObjectId(id)}},{"$unwind": "$Gifts"},{"$match":{"Gifts.Date_of_Offer":{"$gt":start_isotime,"$lt":end_isotime}}},{"$project": {"Gifts":1}}]).to_list()

    if resp == None:
        return jsonify({"message":"id not found"})

    # resp = collection.find_one(filter={"_id":ObjectId(id)})

    # gifts = resp.get("Gifts")
   # accepted = 0

    #This is done instead of mongo query to reduce query to db
   #  for gift in gifts:
    #    if str(gift.get("Action_Taken")).lower() == "accepted":
   #         accepted+=1

    # resp["total_gift"] = len(gifts)
    # resp["accepted"] = accepted

    return jsonify(json.dumps(obj=resp,cls=JSONEncoder))

# SOLUTION FROM https://vuyisile.com/dealing-with-the-type-error-objectid-is-not-json-serializable-error-when-working-with-mongodb/
class JSONEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, ObjectId):
            return str(item)
        return json.JSONEncoder.default(self, item)
