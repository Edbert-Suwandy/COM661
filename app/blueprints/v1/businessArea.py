from flask import make_response, jsonify, request, Blueprint
from datetime import datetime
from globals import DoF, ObjectId_to_str

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
    # Unwind gift, group business, count all offer, count accepted offer
    result = DoF.aggregate(pipeline=[\
            {"$unwind":"$Gifts"},\
            {"$group":\
            {"_id":"$Gifts.Offered_From",\
            "Total_Offer":{"$sum":1},\
            "Total_Accepted_Offer":{"$sum":{"$cond": [{"$eq":["$Gifts.Action_Taken","Accepted"]},1,0]}}\
            }},\
            {"$skip": (page-1) * paginate},\
            {"$limit": paginate}\
            ]).to_list()
    result = ObjectId_to_str(result)
    return make_response(jsonify(result), 200)
