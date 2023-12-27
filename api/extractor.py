from collections.abc import MutableMapping
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
import datetime
import azure_credentials
from azure.ai.formrecognizer import DocumentAnalysisClient, DocumentField, AddressValue
from azure.storage.blob import BlobServiceClient
from database import Database
from azure.core.credentials import AzureKeyCredential
import json

class Extractor:
    def __init__(self, container_name):
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=azure_credentials.FORM_RECOGNIZER_ENDPOINT_k1_1065,
            credential=AzureKeyCredential(azure_credentials.FORM_RECOGNIZER_KEY_k1_1065)
        )

        self.blob_service_client = BlobServiceClient.from_connection_string(
            azure_credentials.CONNECTION_STRING
        )
        self.blob_container_client = self.blob_service_client.get_container_client(
            container_name
        )

    def unpack_fields(self, data, parent_key='', sep='_'):
        items = {}
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{parent_key}{sep}{key}" if parent_key else key
                if isinstance(value, DocumentField):
                    if value.value_type in ['dictionary', 'list']:
                        items.update(self.unpack_fields(value.value, new_key, sep=sep))
                    else:
                        # Associate the confidence directly with the field value
                        items[new_key] = {
                            'value': value.value,
                            'confidence': value.confidence
                        }
                elif isinstance(value, (dict, list)):
                    items.update(self.unpack_fields(value, new_key, sep=sep))
                else:
                    items[new_key] = {'value': value} 
        elif isinstance(data, list):
            for index, item in enumerate(data):
                items.update(self.unpack_fields(item, f"{parent_key}{sep}{index+1}", sep=sep))
        elif isinstance(data, DocumentField):
            if data.value_type == 'dictionary':
                for k, v in data.value.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    items.update(self.unpack_fields(v, new_key, sep=sep))
            else:
                items[parent_key] = {
                    'value': data.value,
                    'confidence': data.confidence
                }
        else:
            items[parent_key] = {'value': data}  

        return items

    def update_database(self, client_id, blob_sas_url, doc_name, extracted_values, gosystems_id):
        poster = Database(client_id, blob_sas_url)
        try:
            for extracted_value in extracted_values:
                for field_name, field_data in extracted_value.items():
                    if isinstance(field_data, dict):
                        field_value = field_data['value']
                        confidence = field_data['confidence']
                    else:
                        field_value = field_data
                        confidence = None

                    # Check if the value is of a custom type and convert it
                    if isinstance(field_value, AddressValue):
                        field_value = json.dumps(field_value.__dict__)

                    last_inserted_id = poster.post2postgres_extract(
                        client_id=client_id,
                        gosystems_id=gosystems_id,
                        doc_url=blob_sas_url,
                        doc_name=doc_name,
                        doc_status='extracted',
                        doc_type='K1-1065',
                        field_name=field_name,
                        field_value=field_value,
                        confidence=confidence
                    )
                    print(f"Last inserted ID for extraction: {last_inserted_id}")
        except Exception as e:
            print(f"An error occurred while updating the database: {e}")
        finally:
            poster.close()
        
    def extract(self, client_id, blob_name):
        blob_location = f"{client_id}/{blob_name}"
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.blob_container_client.container_name,
            blob_name=blob_location,
            account_key=azure_credentials.KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        )

        blob_sas_url = f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.blob_container_client.container_name}/{blob_location}?{sas_token}"
        doc_url = f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.blob_container_client.container_name}/{blob_location}"

        poller = self.document_analysis_client.begin_analyze_document_from_url(
            "k1-1065-v3", blob_sas_url)
        print("do we be alive")
        k1_1065 = poller.result()
        
        response_list = []
        for idx, k1_1065 in enumerate(k1_1065.documents):
            print(f"--------Recognizing K1-1065 #{idx}--------")
            k1_1065_dict = {}
            for name, field in k1_1065.fields.items():
                if isinstance(field.value, (dict, list)):
                    # Unpack nested fields with the parent name as a prefix
                    flat_fields = self.unpack_fields(field.value, parent_key=name)
                    k1_1065_dict.update(flat_fields)
                else:
                    # Extract the simple value
                    k1_1065_dict[name] = {
                        'value': field.value if hasattr(field, 'value') else field.content,
                        'confidence': field.confidence
                    }

                k1_1065_dict['confidence'] = field.confidence

            response_list.append(k1_1065_dict)
            print(k1_1065_dict)
            print("----------------------------------------")

        isEmpty = len(response_list) == 0

        return response_list, doc_url, isEmpty
