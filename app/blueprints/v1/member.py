from flask import Blueprint, request, make_response, jsonify
from datetime import datetime
from bson import ObjectId
from json import dumps
from globals import DoF, ObjectId_to_str
from hashlib import sha256
from decorator import admin_required 

member_bp = Blueprint("member_BP", __name__)

@member_bp.route("/", methods=["GET"])
def get_all_member():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page < 1:
        page = 1
    result = DoF.find({}).skip((page-1)*paginate).limit(paginate).to_list()

    result = ObjectId_to_str(result)
    return make_response(jsonify(result),200)

@member_bp.route("/<string:id>",methods=["GET"])
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

    try:
        id = ObjectId(id)
    except:
        return make_response(jsonify({"message": id + "is not a valid id"}),400)

    resp = DoF.aggregate([{"$match":{"_id":ObjectId(id)}},\
            {"$unwind": "$Gifts"},\
            {"$match":{"Gifts.Date_of_Offer":{"$gt":start_isotime,"$lt":end_isotime}}},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate},\
            ])\
            .to_list()
    if resp == None:
        return make_response(jsonify({"message":"id not found check url"}),400)

    resp = ObjectId_to_str(resp)
    return make_response(jsonify(resp),200)

@member_bp.route("/<string:id>/delete",methods=["DELETE"])
@admin_required
def delete_member(id):
    try:
        id = ObjectId(id)
    except:
        return make_response(jsonify({"message": id + "is not a valid id"}),400)

    resp = DoF.delete_one(filter={"_id":id})

    if not resp.acknowledged:
        return make_response(jsonify({"message": "query not acknowledged try again later"}),500)
    
    return make_response(jsonify({"message": "user succesfully deleted", "id": id}),200)

@member_bp.route("/<string:id>/update",methods=["PATCH"])
@admin_required
def update_member(id):
    try:
        id = ObjectId(id)
    except:
        return make_response(jsonify({"message": id + "is not a valid id"}),400)

    # ASK THIS I CAN VALIDATE INPUT BUT ALSO THE WHOLE POINT OF MONGO DB IS IT CAN MUTATE QUICKLY
    key = request.headers.get("key")
    if key != "Ultimate_Recipient" and key != "Business_Area":
        return make_response(jsonify({"message": "Key must be either Business_Area or Ultimate_Recipient"}),400)
    value = request.headers.get("value")
    if key == None or value == None:
        return make_response(jsonify({"message": "bad request both key and value must be filled"}, 400))

    resp = DoF.update_one(filter={"_id":ObjectId(id)},update={"$set":{key:value}},upsert=True).acknowledged

    if not resp:
        return make_response(jsonify({"message": "query not acknowledged try again later"}),500)
    return make_response(jsonify({"message": "user succesfully deleted", "id": id}),200)

@member_bp.route("/<string:id>/gifts",methods=["PUT"])
@admin_required
def add_gift(id):
    try:
        id = ObjectId(id)
    except:
        return make_response(jsonify({"message": id + "is not a valid id"}),400)
    gifts = {\
            "Date_of_Offer" :  request.args.get("Date_of_Offer"),\
    "Offered_From" : request.args.get("Offered_From"),\
    "Offered_to" : request.args.get("Offered_to"),\
    "Description_of_Offer" : request.args.get("Description_of_Offer"),\
    "Reason_for_offer" : request.args.get("Reason_for_offer"),\
    "Estimated_Gift_Value" : request.args.get("Estimated_Gift_Value"),\
    "Action_Taken" : request.args.get("Action_Taken"),\
    }
    
    if gifts.get("Date_of_Offer") == None or gifts.get("Offered_From") == None or gifts.get("Offered_to") == None or gifts.get("Description_of_Offer") == None or gifts.get("Reason_for_offer") == None or gifts.get("Estimated_Gift_Value") == None or gifts.get("Action_Taken") == None:
        return make_response(jsonify({"message": "bad request all field must be filled"}),400)

    try:
        datetime.strptime(gifts.get("Date_of_Offer"), "%d/%m/%Y")
    except:
        return make_response(jsonify({"message": "datetime invalid use format dd/mm/yyyy"}),400)

    gift_hash = sha256(dumps(gifts.encode())).hexdigest()
    gifts["gift_hash"] = gift_hash
    resp = DoF.update_one(filter={"_id": id}, update={"$push": gifts}).acknowledged
    if not resp:
        return make_response(jsonify({"message": "query not acknowledged try again later"}),500)
    return make_response(jsonify({"message": "user succesfully deleted", "id": id}),200)

@member_bp.route("<string:id>/gift/<string:hash>/update",methods=["PATCH"])
@admin_required
def update_gift(id,hash):
    try:
        id = ObjectId(id)
    except:
        return make_response(jsonify({"message": id + "is not a valid id"}),400)
    key = request.headers.get("key")
    value = request.headers.get("value")
    if key == None or value == None:
        return make_response(jsonify({"message": "bad request both key and value must be filled"}),400)

    resp = DoF.update_one(filter={"_id": id,"Gifts": {"hash": hash}}, update={"$set": {"Gifts.$."+ key: value}},upsert=True).acknowledged

    if not resp:
        return make_response(jsonify({"message": "query not acknowledged try again later"}),500)
    
    return make_response(jsonify({"message": "gift succesfully deleted", "id": id}),200)

@member_bp.route("gift/<string:hash>/delete",methods=["DELETE"])
@admin_required
def delete_gift(hash):
    resp = DoF.delete_one(filter={"Gifts": {"hash": hash}})

    if not resp.acknowledged:
        return make_response(jsonify({"message": "query not acknowledged try again later"}),500)
    
    return make_response(jsonify({"message": "gifts succesfully deleted"}),200)
