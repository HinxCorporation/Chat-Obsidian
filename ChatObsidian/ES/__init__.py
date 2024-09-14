import configparser

from elasticsearch import Elasticsearch, helpers


class ES:
    def __init__(self, config_file='config.ini', custom_index=None):
        # Read config file
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        # Get Elasticsearch configuration
        es_host = config.get('es', 'host', fallback='localhost')
        es_port = config.getint('es', 'port', fallback=9200)
        es_username = config.get('es', 'username', fallback=None)
        es_password = config.get('es', 'password', fallback=None)
        if not custom_index:
            self.es_index = config.get("es", "index", fallback="ai")
        else:
            self.es_index = custom_index
        # Setup Elasticsearch client
        protocol = 'http'
        host = f'{protocol}://{es_host}:{es_port}'
        print(f"Elasticsearch host: {host}/{self.es_index}")
        self.es_client = Elasticsearch(
            [host],
            http_auth=(es_username, es_password) if es_username and es_password else None
        )
        if self.ping():
            self.ensure_index()
        else:
            print("Elasticsearch server is not available.")

    # ping server
    def ping(self):
        """
        Ping the Elasticsearch server to check if it's available.

        Returns:
            bool: True if the server is available, False otherwise.
        """
        return self.es_client.ping()

    def ensure_index(self):
        """
        Create the index if it doesn't already exist.
        """
        self.es_client.indices.create(index=self.es_index, ignore=400)

    def index_document(self, document, doc_id=None):
        """
        Index a single document in Elasticsearch.

        Args:
            document (dict): The document to be indexed.
            doc_id (str, optional): The ID for the document. If not provided, Elasticsearch will generate one.

        Returns:
            dict: The response from Elasticsearch.
        """
        return self.es_client.index(index=self.es_index, body=document, id=doc_id)

    def search_documents(self, query):
        """
        Search for documents in the index.

        Args:
            query (dict): The search query.

        Returns:
            dict: The search results from Elasticsearch.
        """
        return self.es_client.search(index=self.es_index, body=query)

    def update_document(self, doc_id, update_body):
        """
        Update an existing document in the index.

        Args:
            doc_id (str): The ID of the document to update.
            update_body (dict): The fields to update and their new values.

        Returns:
            dict: The response from Elasticsearch.
        """
        return self.es_client.update(index=self.es_index, id=doc_id, body={"doc": update_body})

    def delete_document(self, doc_id):
        """
        Delete a document from the index.

        Args:
            doc_id (str): The ID of the document to delete.

        Returns:
            dict: The response from Elasticsearch.
        """
        return self.es_client.delete(index=self.es_index, id=doc_id)

    def bulk_index(self, documents):
        """
        Bulk index multiple documents.

        Args:
            documents (list): A list of dictionaries, each representing a document to be indexed.

        Returns:
            tuple: A tuple containing the number of successful operations and a list of any error messages.
        """
        actions = [
            {
                "_index": self.es_index,
                "_source": doc
            }
            for doc in documents
        ]
        return helpers.bulk(self.es_client, actions)

    def get_document(self, doc_id):
        """
        Retrieve a document by its ID.

        Args:
            doc_id (str): The ID of the document to retrieve.

        Returns:
            dict: The document if found, or None if not found.
        """
        return self.es_client.get(index=self.es_index, id=doc_id)

    def count_documents(self, query=None):
        """
        Count the number of documents in the index, optionally filtered by a query.

        Args:
            query (dict, optional): A query to filter the documents to be counted.

        Returns:
            int: The number of documents matching the query (or total documents if no query provided).
        """
        body = {"query": query} if query else None
        return self.es_client.count(index=self.es_index, body=body)['count']

    def get_cluster_health(self):
        """
        Get the health status of the Elasticsearch cluster.

        Returns:
            dict: A dictionary containing cluster health information, including:
                - status: 'green', 'yellow', or 'red'
                - number_of_nodes
                - number_of_data_nodes
                - active_primary_shards
                - active_shards
                - relocating_shards
                - initializing_shards
                - unassigned_shards
        """
        try:
            health = self.es_client.cluster.health()
            return health
        except Exception as e:
            print(f"Error getting cluster health: {str(e)}")
            return None

    def is_cluster_healthy(self):
        """
        Check if the Elasticsearch cluster is in a healthy state.

        Returns:
            bool: True if the cluster status is 'green', False otherwise.
        """
        health = self.get_cluster_health()
        if health and health['status'] == 'green':
            return True
        return False
