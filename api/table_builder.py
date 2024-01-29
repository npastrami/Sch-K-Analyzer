import json
from database import Database

class TableBuilder:
    def __init__(self, client_id, doc_url):
        self.database = Database(client_id, doc_url)

    async def fetch_client_data(self, client_id):
        await self.database.ensure_connected()

        records = await self.database.conn.fetch("SELECT * FROM client_docs WHERE client_id = $1;", client_id)
        client_docs_data = [dict(record) for record in records]

        final_data = {
            'client_docs': client_docs_data,
        }

        return json.dumps(final_data)

    async def close(self):
        await self.database.close()
