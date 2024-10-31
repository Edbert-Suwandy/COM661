from flask import Blueprint, request, make_response, jsonify
from datetime import datetime
from bson import ObjectId
from globals import DoF, ObjectId_to_str

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
