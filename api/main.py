from flask import Flask, make_response, send_file, request, jsonify
from flask_cors import CORS
from pipeline_k1.azure_upload import azure_upload_blueprint
from pipeline_k1.ext_k1_1065 import extract_k1_1065_blueprint
from refresh import refresh_blueprint
from handle_duplicates import handle_duplicates_blueprint
from database import Database
from table_builder import TableBuilder
import os
from azure.storage.blob import BlobServiceClient
from io import BytesIO
from azure_credentials import BUCKET_NAME_1065, CONNECTION_STRING, BLOB_NAME
import openpyxl
from tempfile import NamedTemporaryFile
from copyfunc import copy_worksheet
from FOFexport import process_FOF


app = Flask(__name__)
CORS(app)


app.register_blueprint(azure_upload_blueprint)
app.register_blueprint(extract_k1_1065_blueprint)
app.register_blueprint(refresh_blueprint)
app.register_blueprint(handle_duplicates_blueprint)

@app.route('/download_csv/<document_id>', methods=['GET', 'POST'])
def download_csv(document_id):
    print("Entered download_csv function")
    client_id = request.json['clientID']
    db = Database(None, None)  
    csv_string = db.generate_csv(document_id, client_id)
    db.close()

    response = make_response(csv_string)
    print(csv_string)
    response.headers["Content-Disposition"] = f"attachment; filename={document_id}.csv"
    response.headers["Content-type"] = "text/csv"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" 
    
    return response

@app.route('/get_client_data', methods=['POST'])
def get_client_data():
    client_id = request.json.get('client_id')
    table_builder = TableBuilder()
    client_data = table_builder.fetch_client_data(client_id)
    return jsonify({"data": client_data})

@app.route('/download_all_documents', methods=['POST'])
def download_all_documents():
    data = request.json
    client_id = data['clientID']
    document_names = data['documentNames']
    
    # Initialize the BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(BUCKET_NAME_1065)

    # Download the existing FOFtest.xlsx
    blob_client = container_client.get_blob_client('FOFtest.xlsx')
    fof_test_stream = BytesIO(blob_client.download_blob().readall())
    fof_workbook = openpyxl.load_workbook(fof_test_stream)
    
    db = Database(None, None)

    # Create a new workbook
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)  # Remove the default sheet
    copy_worksheet(fof_workbook, workbook, 'Sheet1')
    def sanitize_sheet_title(title):
        invalid_chars = ':\\/?*[]'
        for char in invalid_chars:
            title = title.replace(char, '')
        return title[:31]

    for document_name in document_names:
        sanitized_name = sanitize_sheet_title(document_name)
        original_data, fof_data = db.generate_sheet_data(sanitized_name, client_id)
        
        # Add original sheet
        original_sheet = workbook.create_sheet(title=sanitized_name)
        for row in original_data:
            original_sheet.append(row)
        
        # Add FOF sheet
        fof_sheet = workbook.create_sheet(title=f"FOF_{sanitized_name}")
        for row in fof_data:
            fof_sheet.append(row)
    print(f"workbook: {vars(workbook)}")
    
    fof_sheet_objects = [workbook[sheet_name] for sheet_name in workbook.sheetnames if 'FOF_' in sheet_name]
    
    process_FOF(workbook, fof_sheet_objects)

    # Save the workbook to a BytesIO object
    output_stream = BytesIO()
    workbook.save(output_stream)
    output_stream.seek(0)

    db.close()

    # Save the workbook to a temporary file
    with NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        workbook.save(tmp.name)
        tmp.seek(0)
        response = send_file(tmp.name, as_attachment=True)
    
    # Set the correct content type for .xlsx
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # Set the correct Content-Disposition header
    response.headers['Content-Disposition'] = f'attachment; filename="{client_id}_FOF_Data.xlsx"'

    # Remove the temporary file after sending it
    os.remove(tmp.name)

    return response

if __name__ == "__main__":
    app.run(debug=True)
