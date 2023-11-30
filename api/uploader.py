import datetime
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import azure_credentials
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import traceback


class Uploader:
    def __init__(self, container_name):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            azure_credentials.CONNECTION_STRING)
        self.blob_container_client = self.blob_service_client.get_container_client(
            container_name)

    def upload(self, client_id, file):
        print("Debug: Received request for upload")
        filename = secure_filename(file.filename)
        blob_name = f"{client_id}/{filename}"
        blob_client = self.blob_container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file.read(), overwrite=True)
        blob_url = blob_client.url
        return blob_url  
