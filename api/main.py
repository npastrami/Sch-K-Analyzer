from flask import Flask, make_response, send_file, request, jsonify
from flask_cors import CORS
from pipeline_k1.azure_upload import azure_upload_blueprint
from pipeline_k1.ext_k1_1065 import extract_k1_1065_blueprint
from refresh import refresh_blueprint
from handle_duplicates import handle_duplicates_blueprint
from database import Database
from table_builder import TableBuilder
import openpyxl
import os
from tempfile import NamedTemporaryFile


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
    
    db = Database(None, None)

    # Create a new workbook
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)  # Remove the default sheet
    
    def sanitize_sheet_title(title):
        invalid_chars = ':\\/?*[]'
        for char in invalid_chars:
            title = title.replace(char, '')
        return title

    for document_name in document_names:
        document_name = sanitize_sheet_title(document_name)
        sheet_data = db.generate_sheet_data(document_name, client_id)
        sheet = workbook.create_sheet(title=document_name)
        for row in sheet_data:
            sheet.append(row)

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
#JO-2