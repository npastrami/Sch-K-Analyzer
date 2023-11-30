from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from uploader import Uploader
from database import Database

azure_upload_blueprint = Blueprint("azure_upload", __name__)

def upload_blob(bucket_name, doc_type):
    client_id = request.form.get('clientID', None)
    gosystems_id = request.form.get('versionID', None)
    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '':
        return jsonify({"error": "No file was uploaded."}), 400
    
    uploader = Uploader(bucket_name)
    blob_url = uploader.upload(client_id, uploaded_file)
    
    if not blob_url:
        return jsonify({"error": "An error occurred during upload."}), 400
    
    poster = Database(client_id, blob_url)
    last_inserted_id = poster.post2postgres_upload(client_id, blob_url, 'uploaded', doc_type, bucket_name, gosystems_id)
    return jsonify({"message": "Blob upload and database insertion successful", "uploaded_file": blob_url, 'doc_status': "Uploaded" })

@azure_upload_blueprint.route("/upload", methods=["POST"])
def upload_to_blob():
    doc_type = request.form.get('docType', None)
    if doc_type == "K1-1065":
        return upload_blob('extract-k1-1065', 'k1-1065')
    else:
        return upload_blob('unsorted', 'unsorted')