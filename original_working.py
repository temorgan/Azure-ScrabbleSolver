import logging
import azure.functions as func
import itertools
import json
from collections import Counter

def load_words_with_counters(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip().upper() for line in file if line.strip()]
    return {word: Counter(word) for word in words}


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

    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
    
def load_dictionary(trie, file_path):
    try:
        with open(file_path, 'r') as file:
            for word in file:
                trie.insert(word.strip())
    except Exception as e:
        logging.error(f"Failed to load dictionary: {str(e)}")

def load_word_list():
    try:
        # Adjust the file path as per your Azure environment setup
        with open('H:\\My Drive\\Udemy\\ChatGPT\\Azure ScrabbleSolver\\dictionary\\english-words\\words_alpha.txt', 'r') as file:
            return set(word.strip() for word in file)
    except Exception as e:
        logging.error(f"Failed to load dictionary: {str(e)}")
        return set()

# Global dictionary loaded once for performance
word_list = load_word_list()

def can_spell(letters, word):
    letters = sorted(letters, reverse=True)  # Sort letters to prioritize non-blank tiles
    word_list = list(word)
    for letter in letters:
        if letter == '?':
            if word_list:  # Ensure there is still a letter to replace if using a blank
                word_list.pop(0)
        elif letter in word_list:
            word_list.remove(letter)
        if not word_list:  # If all letters are matched
            return True
    return not word_list  # Return True if word_list is empty, meaning all letters were matched

def find_possible_words(rack):
    words = load_words_with_counters('H:\\My Drive\\Udemy\\ChatGPT\\Azure ScrabbleSolver\\dictionary\\english-words\\words_alpha.txt')
    rack_counter = Counter(rack.upper())
    valid_words = []
    for word, count in words.items():
        if not (count - rack_counter):
            valid_words.append(word)

    # Sort words by length in descending order
    valid_words_sorted = sorted(valid_words, key=len, reverse=True)
    return valid_words_sorted

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="scrabbleSolver", methods=["POST"])
def scrabble_solver(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        tiles = req_body.get('tiles', '')
        possible_words = find_possible_words(tiles)
        response_json = json.dumps({"possible_words": possible_words}, indent=4)
        return func.HttpResponse(response_json, mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Error processing your request: {str(e)}")
        return func.HttpResponse("Error processing your request", status_code=500)