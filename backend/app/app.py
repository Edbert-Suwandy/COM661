from flask import Flask, make_response, jsonify
from os import getenv

app = Flask(__name__)

# Make sure its admin locked
@app.route('/creds', method=["GET"])
def creds():
    return make_response(jsonify({
        "MONGO_USER":getenv("MONGO_USER"),
        "MONGO_PASSWORD":getenv("MONGO_PASSWORD"),
        "MONGO_URL":getenv("MONGO_URL")
    }))
