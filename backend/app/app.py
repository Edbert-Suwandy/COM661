from flask import Flask, make_response, jsonify, request, session
from os import getenv, path
from werkzeug.utils import secure_filename

from parse_csv import parse_csv

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = getenv("UPLOAD_FOLDER")
app.secret_key = 'hello'

# Make sure its admin locked
@app.route('/env', methods=["GET"])
def creds():
    return make_response(jsonify({
        "MONGO_USER":getenv("MONGO_USER"),
        "MONGO_PASSWORD":getenv("MONGO_PASSWORD"),
        "MONGO_URL":getenv("MONGO_URL")
    }))

# Make sure its admin locked
@app.route("/upload", methods=["POST"])
def upload_csv():
    f = request.files.get('file')
    data_filename = secure_filename(f.filename)
    f.save(path.join(app.config['UPLOAD_FOLDER'],data_filename))
    session['uploaded_data_file_path'] = path.join(app.config['UPLOAD_FOLDER'],data_filename)

    return (parse_csv("./datastore/"+data_filename))