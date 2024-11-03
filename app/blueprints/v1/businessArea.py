from flask import make_response, jsonify, request, Blueprint
from datetime import datetime
from globals import DoF, ObjectId_to_str
from decorator import admin_required 

businessArea_bp = Blueprint("businessArea_bp", __name__)

@businessArea_bp.route("/<string:name>",methods=["GET"])
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
    resp = DoF.aggregate([{"$match":{"Business_Area":name}},\
            {"$unwind": "$Gifts"},\
            {"$match":{"Gifts.Date_of_Offer":{"$gt":start_isotime,"$lt":end_isotime}}},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate}
            ])\
            .to_list()
    if resp == None:
        return jsonify({"message":"Business Area not found"})

    resp = ObjectId_to_str(resp)
    return make_response(jsonify(resp),200)

@businessArea_bp.route("/",methods=["GET"])
def get_business():
    paginate:int = request.args.get(key="paginate",default=10, type=int)
    if paginate < 1:
        paginate = 10
    page:int = request.args.get(key="page",default=1,type=int)
    if page <= 1:
        page = 1
    # group business, count all offer, count accepted offer
    result = DoF.aggregate(pipeline=[\
            {"$unwind":"$Gifts"},\
            {"$group":\
            {"_id":"$Business_Area",\
            "Total_Offer":{"$sum":"Total_Gifts"},\
            "Total_Accepted_Offer":{"$sum":"Total_Accepted_Gifts"}\
            }},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate}\
            ]).to_list()
    result = ObjectId_to_str(result)
    return make_response(jsonify(result), 200)

@businessArea_bp.route("/<string:name>/rename", methods=["PATCH"])
@admin_required
def rename_business_area(name):
    new_name = request.args.get("new_name")
    if not new_name:
        return make_response(jsonify({"message":"new_name filed can't be empty"}),400)

    resp = DoF.update_many(filter={"Business_Area": name}, update={"$set": {"Business_Area": new_name}})
    if not resp.acknowledged:
        make_response(jsonify({"message": "query not ackowledge"}),500)

    if (not resp.raw_result.get("updateExisting")):
        make_response(jsonify({"message": "no update"}),200)

    return make_response(jsonify({"message" : "rename operations successful"}),201)
