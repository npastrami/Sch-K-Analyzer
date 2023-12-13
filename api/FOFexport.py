from flask import Blueprint, jsonify, send_file, after_this_request
import shutil
from flask_cors import CORS
import openpyxl
import re
import numpy as np
import pandas as pd
from azure.storage.blob import BlobServiceClient, BlobClient
from io import BytesIO
from itemcodeoffsets import *
from  azure_credentials import CONNECTION_STRING, KEY, BUCKET_NAME_1065

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

fofexport_blueprint = Blueprint('process_fof', __name__)
CORS(fofexport_blueprint)

@fofexport_blueprint.route('/process_fof', methods=['POST'])
def process_FOF():
        print(f'Processing all files in the Azure Blob container...')
        
        container_client = blob_service_client.get_container_client(BUCKET_NAME_1065)
        blob_list = container_client.list_blobs()
        excel_files = [blob.name for blob in blob_list if blob.name.endswith('.xlsx')]

        if not excel_files:
            return {"message": "No Excel files found in the selected directory."}, 400

        fof_file = None
        other_files = []

        for file_key in excel_files:
            # Skip temporary files created by Excel
            if file_key.startswith("~$"):
                continue

            blob_client = container_client.get_blob_client(file_key)
            file_stream = BytesIO(blob_client.download_blob().readall())
            df = pd.read_excel(file_stream, sheet_name="Sheet1" if file_key == "FOFtest.xlsx" else "K-1 Output", header=None if file_key == "FOFtest.xlsx" else 0)

            if file_key == "FOFtest.xlsx":
                fof_file = df
            else:
                cleaned_filename = re.sub(r'\W+', '', file_key)
                other_files.append((cleaned_filename, df))

        if fof_file is None:
            print("Couldn't find FOFtest.xlsx!")
            return jsonify({"message": "Couldn't find FOFtest.xlsx!"}), 500
        print("Found FOF Test")
        # Enumerate filenames in row 8, starting in column E (index 4)
        for i, (filename, _) in enumerate(other_files, start=4):
            fof_file.iat[7, i] = filename

        # Based off 2022 IRS Intructions for K-1 (1065)
        mappings = {
            "ordinary business income": 20,
            "net rental real estate income": 21, 
            "other net rental income": 22,
            "guaranteed payments for services": 23,
            "guaranteed payments for capital": 24,
            "total guaranteed payments": 25, 
            "interest Income": 26,                       
            "ordinary dividends": 27, 
            "qualified dividends": 28, 
            "dividend equivalents": 29, 
            "royalties": 30,                       
            "net short-term capital gain": 31, 
            "net long-term capital gain": 32,                      
            "collectibles 28": 33, 
            "unrecaptured section 1250 gain": 34,                        
            "net section 1231 gain": 35, 
            "other income": 36, 
            "section 179 deduction": 46,                         
            "other deductions": 47, 
            "self-employment earnings": 71, 
            "credits": 75, 
            "alternative minimum tax (AMT) items": 92, 
            "tax-exempt income": 99, 
            "distributions": 103, 
            "other information": 107, 
            "foreign taxes paid": 142,  
        }
        
        # This dictionary will store the restructured data
        structured_data = {
            "Keyword": [],
            "Item Codes": [],
            "Amount": [],
            "Confidence": []
        }

        for filename, file in other_files:
            # Check if the filename exists in row 8 (Python index 7), if not, skip this file
            if filename not in fof_file.iloc[7].values:
                print(f"Skipping file {filename} because it does not exist in row 8 of FOFtest.xlsx")
                continue

            # Get the column index with the filename
            match = np.where(fof_file.iloc[7] == filename)
            if len(match[0]) > 0:
                col_index = match[0][0]
            else:
                continue  # Skip if filename not found

            # Iterate over each row and restructure the data
            for index, row in file.iterrows():
                # Split the 'Field Names' into keywords and item codes
                keyword = row['Field Names'].split(' [')[0]
                item_code_match = re.search(r'\[code (\d+)\]', row['Field Names'])
                item_code = item_code_match.group(1) if item_code_match else ''
                amount = row['Field Values'] if item_code_match else ''
                confidence = row['Confidence']

                # If it's a keyword with an item code, calculate the average confidence
                if item_code:
                    # Calculate the average if there's already an entry, else just assign
                    if keyword in structured_data['Keyword']:
                        existing_index = structured_data['Keyword'].index(keyword)
                        existing_confidence = structured_data['Confidence'][existing_index]
                        average_confidence = (existing_confidence + confidence) / 2
                        structured_data['Confidence'][existing_index] = average_confidence
                    else:
                        structured_data['Keyword'].append(keyword)
                        structured_data['Item Codes'].append(item_code)
                        structured_data['Amount'].append(amount)
                        structured_data['Confidence'].append(confidence)
                else:
                    # Just append the data if no item code is present
                    structured_data['Keyword'].append(keyword)
                    structured_data['Item Codes'].append('')
                    structured_data['Amount'].append(row['Field Values'])
                    structured_data['Confidence'].append(confidence)

        # Convert structured data to DataFrame
        structured_df = pd.DataFrame(structured_data)

        # Save the structured DataFrame to Excel file in-memory
        with BytesIO() as output:
            structured_df.to_excel(output, index=False)
            output.seek(0)
            data = output.read()  # Read the contents before the BytesIO object is closed

        # Create another BytesIO object from the saved data
        output_stream = BytesIO(data)
        output_stream.seek(0)

        # Define a cleanup function to close the BytesIO object after sending the file
        @after_this_request
        def cleanup(response):
            output_stream.close()
            return response

        # Send the file
        return send_file(
            output_stream,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            attachment_filename="FOFtest.xlsx"
        )
  