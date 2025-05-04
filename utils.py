# utils.py

import json
import os
from config import DATABASE_FILE

def store_in_database(key, data):
    db = {}
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            try:
                db = json.load(f)
            except:
                db = {}
    db[key] = data
    with open(DATABASE_FILE, 'w') as f:
        json.dump(db, f, indent=2)

def get_from_database(key):
    if not os.path.exists(DATABASE_FILE):
        return None
    with open(DATABASE_FILE, 'r') as f:
        try:
            db = json.load(f)
            return db.get(key)
        except:
            return None
