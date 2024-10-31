from flask import request, make_response, jsonify, Blueprint
from datetime import datetime
from globals import DoF, ObjectId_to_str, User 

business_bp = Blueprint("business_bp", __name__)
@business_bp.route("/",methods=["GET"])
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
    return make_response(jsonify(result),200)

@business_bp.route("/<string:business>",methods=["GET"])
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
    result = User.aggregate(pipeline=[\
            {"$unwind":"$Gifts"},\
            {"$match": {"Gifts.Offered_From":business, "Gifts.Date_of_Offer": {"$lt": end_isotime, "$gt": start_isotime}}},\
            {"$skip":(page-1)*paginate},\
            {"$limit": paginate},\
            ]).to_list()
    result = ObjectId_to_str(result)
    return make_response(jsonify(result),200)
