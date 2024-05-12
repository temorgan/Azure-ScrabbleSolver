import logging
import azure.functions as func
import itertools
import json
from collections import Counter
from azure.storage.blob import BlobServiceClient
import os  # Needed for environment variables

# Configure logging to print to stdout which is visible in the Azure Function logs
logging.basicConfig(level=logging.INFO)

# Retrieve the connection string from environment variables
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Log the retrieved connection string
logging.info(f"Retrieved connection string: {connect_str}")

if connect_str is None:
    logging.error("Connection string is not set in the environment variables.")
else:
    # If the connection string is retrieved successfully, proceed with BlobServiceClient initialization
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_word

def load_dictionary(trie, container_name, blob_name):
    try:
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        stream = blob_client.download_blob()
        file_text = stream.readall()
        
        # Debug: Check what is being returned
        logging.info(f"Type of file_text: {type(file_text)}")
        logging.info(f"Content of file_text: {file_text[:200]}")  # Print first 200 characters

        if file_text:
            words = file_text.decode('utf-8').splitlines()
            for word in words:
                trie.insert(word.strip().upper())
        else:
            logging.error("No data found in the blob.")
    except Exception as e:
        logging.error(f"Failed to load dictionary: {str(e)}")

def generate_permutations(tiles, max_length):
    all_permutations = set()
    for length in range(1, max_length + 1):
        for permutation in itertools.permutations(tiles, length):
            all_permutations.add(''.join(permutation))
    return all_permutations

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="tokenize", methods=["POST"])
def tokenize_scrabble_tiles(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        tiles = req_body.get('tiles', '')
        if not tiles:
            return func.HttpResponse("No tiles provided", status_code=400)
        
        tokenized_tiles = generate_permutations(tiles, len(tiles))
        return func.HttpResponse(json.dumps({"tokenized": list(tokenized_tiles)}, indent=4), mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error processing your request: {str(e)}")
        return func.HttpResponse("Error processing your request", status_code=500)

@app.route(route="scrabbleSolver", methods=["POST"])
def scrabble_solver(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        tiles = req_body.get('tiles', '')
        if not tiles:
            return func.HttpResponse("No tiles provided", status_code=400)

        # Instantiate Trie here
        trie = Trie()
        # Load dictionary data into the trie
        load_dictionary(trie, 'dictionary', 'twl06.txt')

        possible_words = find_possible_words(tiles, trie)
        response_json = json.dumps({"possible_words": possible_words}, indent=4)
        return func.HttpResponse(response_json, mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error processing your request: {str(e)}")
        return func.HttpResponse("Error processing your request", status_code=500)

def find_possible_words(rack, trie):
    rack = rack.upper()
    permutations = generate_permutations(rack, len(rack))
    valid_words = [word for word in permutations if trie.search(word)]
    return sorted(valid_words, key=len, reverse=True)