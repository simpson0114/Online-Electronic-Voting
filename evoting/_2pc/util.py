import base64, json
import pickle

def encodeDict(data):
        raw = pickle.dumps(data)
        return raw

def decodeDict(raw):
        data = pickle.loads(raw)
        return data