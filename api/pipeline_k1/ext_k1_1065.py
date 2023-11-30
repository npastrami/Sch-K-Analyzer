from flask import Blueprint, request, jsonify
import xml.etree.ElementTree as ET
from extractor import Extractor
from azure_credentials import BUCKET_NAME_1065
import re

extract_k1_1065_blueprint = Blueprint("extract_k1-1065", __name__)

def sanitize_blob_name(blob_name):
    sanitized = re.sub(r'[()\[\]{}]', '', blob_name)
    sanitized = sanitized.replace(' ', '_')
    return sanitized   

@extract_k1_1065_blueprint.route("/extract_k1_1065", methods=["POST"])
def extract_k1_1065():
    client_id = request.json['clientID']
    gosystems_id = request.json['versionID']
    req_blob_name = request.json['blobName']
    sanitized_blob_name = sanitize_blob_name(req_blob_name)

    # Extract information using the Extractor class
    extractor = Extractor(BUCKET_NAME_1065)
    extracted_values, blob_sas_url, isEmpty = extractor.extract(client_id, sanitized_blob_name)
    
    if not isEmpty:
        extractor.update_database(client_id, blob_sas_url, req_blob_name, extracted_values, gosystems_id)

    # Format dict as XML
    root = ET.Element("K1-1065")
    for extracted_value in extracted_values:
        K1_1065_element = ET.SubElement(root, "K1-1065")
        for key, value in extracted_value.items():
            if key == 'confidence':
                K1_1065_element.set('confidence', str(value))
            else:
                ET.SubElement(K1_1065_element, key).text = str(value) if value is not None else None

    xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')

    return jsonify({"message": "K1-1065 extraction successful", "xml": xml_str, "isEmpty": isEmpty})