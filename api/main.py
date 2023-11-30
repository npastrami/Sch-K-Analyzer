from flask import Flask, make_response, request, jsonify
from flask_cors import CORS
from pipeline_k1.azure_upload import azure_upload_blueprint
from pipeline_k1.ext_k1_1065 import extract_k1_1065_blueprint
from refresh import refresh_blueprint
from handle_duplicates import handle_duplicates_blueprint
from database import Database
from table_builder import TableBuilder


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


if __name__ == "__main__":
    app.run(debug=True)
