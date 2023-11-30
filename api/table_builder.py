import psycopg2
import json

class TableBuilder:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="k1-analyzer",
            user="postgres",
            password="kr3310",
            host="localhost",
            port="5432"
        )
        self.cur = self.conn.cursor()

    def fetch_client_data(self, client_id):
        """
        Fetch client_docs and extracted_fields for a specific client_id.
        Returns the data as a JSON object.
        """
        # Fetch data from client_docs
        self.cur.execute("SELECT * FROM client_docs WHERE client_id = %s;", (client_id,))
        client_docs = self.cur.fetchall()
        client_docs_column_names = [desc[0] for desc in self.cur.description]
        client_docs_data = [dict(zip(client_docs_column_names, record)) for record in client_docs]

        # Close database connection
        self.close()

        # Prepare final JSON data
        final_data = {
            'client_docs': client_docs_data,
        }

        return json.dumps(final_data)

    def close(self):
        """
        Close the database connection.
        """
        self.cur.close()
        self.conn.close()