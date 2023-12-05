import psycopg2
import os
import csv
from io import StringIO

class Database:
    def __init__(self, client_id, doc_url):
        self.client_id = client_id
        self.doc_url = doc_url
        self.conn = psycopg2.connect(
            dbname="k1-analyzer",
            user="postgres",
            password="kr3310",
            host="localhost",
            port="5432"
        )
        self.cur = self.conn.cursor()
        self.create_table()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS client_docs (
            id SERIAL PRIMARY KEY,
            client_id TEXT,
            doc_url TEXT,
            doc_name TEXT,
            doc_status TEXT,
            doc_type TEXT,
            container_name TEXT,
            gosystems_id TEXT
        );
        """
        self.cur.execute(create_table_query)
        self.conn.commit()
        
        create_extracted_fields_table_query = """
        CREATE TABLE IF NOT EXISTS extracted_fields (
            id SERIAL PRIMARY KEY,
            client_id TEXT,
            doc_url TEXT,
            doc_name TEXT,
            doc_status TEXT,
            doc_type TEXT,
            field_name TEXT,
            field_value TEXT,
            confidence REAL,
            gosystems_id TEXT
        );
        """
        self.cur.execute(create_extracted_fields_table_query)
        self.conn.commit()

    def post2postgres_upload(self, client_id, doc_url, doc_status, doc_type, container_name, gosystems_id):
        doc_name = os.path.basename(doc_url)  
        insert_query = """
        INSERT INTO client_docs (client_id, doc_url, doc_name, doc_status, doc_type, container_name, gosystems_id)  
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        self.cur.execute(insert_query, (client_id, doc_url, doc_name, doc_status, doc_type, container_name, gosystems_id))  
        self.conn.commit()

        last_inserted_id = self.cur.fetchone()[0]
        return last_inserted_id
    
    def post2postgres_extract(self, client_id, doc_url, doc_status, doc_type, doc_name, field_name, field_value, confidence, gosystems_id):
        insert_query = """
        INSERT INTO extracted_fields (client_id, doc_url, doc_status, doc_type, doc_name, field_name, field_value, confidence, gosystems_id) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """
        self.cur.execute(insert_query, (client_id, doc_url, doc_status, doc_type, doc_name, field_name, field_value, confidence, gosystems_id))
        
        last_inserted_id = self.cur.fetchone()[0]
        self.conn.commit()

        update_status_query = """
        UPDATE client_docs SET doc_status = 'extracted' WHERE client_id = %s AND doc_url = %s;
        """
        self.cur.execute(update_status_query, (client_id, doc_url))
        self.conn.commit()
        
        return last_inserted_id
    
    def generate_csv(self, document_id, client_id):
        # Query to fetch all fields and values for a specific document and client
        query = """ SELECT field_name, field_value, confidence FROM extracted_fields WHERE doc_name = %s AND client_id = %s"""
        self.cur.execute(query, (document_id, client_id))

        # Fetch all rows
        rows = self.cur.fetchall()
        # Initialize CSV output in memory
        output = StringIO()
        csv_writer = csv.writer(output)

        # Write the document name in cell A1
        csv_writer.writerow([f"Document Name: {document_id}"])

        # Write "Field Names" in cell A2 and "Field Values" in cell B2
        csv_writer.writerow(["Field Names", "Field Values", "Confidence"])

        # Populate the rest of the columns with field names and their values
        for row in rows:
            csv_writer.writerow([row[0], row[1], row[2]])

        # Get the CSV content and reset the pointer
        csv_content = output.getvalue()
        output.seek(0)

        return csv_content
    
    def generate_sheet_data(self, document_id, client_id):
        query = """ SELECT field_name, field_value, confidence FROM extracted_fields WHERE doc_name = %s AND client_id = %s"""
        self.cur.execute(query, (document_id, client_id))
        rows = self.cur.fetchall()

        # Format the data for Excel sheet
        sheet_data = []
        sheet_data.append([f"Document Name: {document_id}"])
        sheet_data.append(["Field Names", "Field Values", "Confidence"])
        for row in rows:
            sheet_data.append([row[0], row[1], row[2]])

        return sheet_data

    def close(self):
        self.cur.close()    
        self.conn.close()