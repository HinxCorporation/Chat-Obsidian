import configparser

from elasticsearch import Elasticsearch


class es_terraria:
    def __init__(self, config_file='config.ini'):
        self.name = "es_terraria"
        self.description = 'Elasticsearch client for Terraria logs'
        self.__setup_es(config_file)
        if self.ping():
            pass
        else:
            print("Elasticsearch server is not available.")

    def __setup_es(self, config_file):
        # Read config file
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        # Get Elasticsearch configuration
        es_host = config.get('es', 'host', fallback='localhost')
        es_port = config.getint('es', 'port', fallback=9200)
        es_username = config.get('es', 'username', fallback=None)
        es_password = config.get('es', 'password', fallback=None)
        # Setup Elasticsearch client
        protocol = 'http'
        host = f'{protocol}://{es_host}:{es_port}'
        self.es_client = Elasticsearch(
            [host],
            http_auth=(es_username, es_password) if es_username and es_password else None
        )

    # ping server
    def ping(self):
        """
        Ping the Elasticsearch server to check if it's available.

        Returns:
            bool: True if the server is available, False otherwise.
        """
        return self.es_client.ping()
