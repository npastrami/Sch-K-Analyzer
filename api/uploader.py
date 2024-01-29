from azure.storage.blob.aio import BlobServiceClient
from werkzeug.utils import secure_filename
import azure_credentials

class Uploader:
    def __init__(self, container_name):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            azure_credentials.CONNECTION_STRING)
        self.blob_container_client = self.blob_service_client.get_container_client(
            container_name)

    async def upload(self, client_id, file):
        print("Debug: Received request for upload")
        filename = secure_filename(file.filename)
        blob_name = f"{client_id}/{filename}"
        blob_client = self.blob_container_client.get_blob_client(blob_name)
        await blob_client.upload_blob(file.read(), overwrite=True)
        blob_url = blob_client.url
        return blob_url 
    
    async def close(self):
        await self.blob_service_client.close()