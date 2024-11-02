from flask import Flask
from globals import User, upload_folder, secret_key
from hashlib import sha256

from blueprints.v1.admin import admin_bp
from blueprints.v1.business import business_bp 
from blueprints.v1.businessArea import businessArea_bp 
from blueprints.v1.member import member_bp 

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = upload_folder
app.secret_key = secret_key

app.register_blueprint(blueprint=admin_bp, url_prefix="/api/v1/admin")
app.register_blueprint(blueprint=business_bp,url_prefix = "/api/v1/business/")
app.register_blueprint(blueprint=businessArea_bp, url_prefix= "/api/v1/businessArea")
app.register_blueprint(blueprint=member_bp,url_prefix= "/api/v1/member")

def ensure_root():
    if(User.find_one(filter={"username": "root"}) == None):
        User.insert_one({"username": "root", "password": sha256("password".encode("UTF-8")).hexdigest(), "is_admin": True, "is_sudo": True})
ensure_root()


