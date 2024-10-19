from flask import Flask, make_response, jsonify, request, session
from os import getenv, path
from werkzeug.utils import secure_filename
import pymongo
from pymongo.collection import Collection

import json
from bson import ObjectId

from parse_csv import parse_csv

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = getenv("UPLOAD_FOLDER")
app.secret_key = 'hello'

def get_collection() -> Collection:
    try:
        client = pymongo.MongoClient(getenv("MONGO_URL"))
        db = client["DoF-gratuity"]
        collection = db["DoF"]
        return collection
    except:
        return None

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
    data_filename = secure_filename(f.filename)
    f.save(path.join(app.config['UPLOAD_FOLDER'],data_filename))
    session['uploaded_data_file_path'] = path.join(app.config['UPLOAD_FOLDER'],data_filename)

    inputs = parse_csv("./datastore/"+data_filename)

    collection = get_collection()

    # TO-DO Maybe upsert could be cool
    for input in inputs:
        details = get_collection().find_one({"Ultimate_Recipient":input.get("Ultimate_Recipient")})
        if details != None:
            collection.update_one(filter={"Ultimate_Recipient": input.get("Ultimate_Recipient")},update={"$push": {"Gifts":input.get("Gifts")[0]}})
        else:
            collection.insert_one(input)

    if(collection != None):
       return jsonify({"success": True})
    return jsonify({"success":False})

#TO-DO: ADD PAGINATIONS
@app.route("/member", methods=["GET"])
def get_all():
    result = get_collection().find({})

    resp = result.to_list()

    return jsonify(json.dumps(obj=resp,cls=JSONEncoder))

# SOLUTION FROM https://vuyisile.com/dealing-with-the-type-error-objectid-is-not-json-serializable-error-when-working-with-mongodb/
class JSONEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, ObjectId):
            return str(item)
        return json.JSONEncoder.default(self, item)
