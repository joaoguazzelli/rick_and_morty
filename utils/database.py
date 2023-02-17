from pymongo import MongoClient

uri = 'mongodb://127.0.0.1:27017/?serverSelectionTimeoutMS=2000&connectTimeoutMS=10000'
client = MongoClient(uri)
db = client['rickandmortydb']