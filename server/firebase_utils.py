import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import datetime
from dotenv import load_dotenv
load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
app = firebase_admin.initialize_app(cred)

def get_user_addresses(user_id):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "addresses"

    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).document(str(user_id))
    doc_snapshot = doc_ref.get()
    doc_ref = db.collection(collection_name).where("userId", "==", str(user_id))
    doc_snapshots = doc_ref.get()

    public_keys = []

    # Iterate over the document snapshots
    for doc_snapshot in doc_snapshots:
        # Get the data from the document
        data = doc_snapshot.to_dict()
        if "publicKey" in data:
            public_key = data["publicKey"]
            public_keys.append(public_key)

    return public_keys

def get_user_address(user_id, wallet_nonce):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "addresses"

    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).document(str(user_id)+'_'+str(wallet_nonce))
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot.exists:
        # Get the data from the document
        data = doc_snapshot.to_dict()["publicKey"]

        return data

def get_private_key(public_key):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "addresses"
    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).where("publicKey", "==", public_key)
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot != []:
        # Get the data from the document
        data = doc_snapshot[0].to_dict()
        return data['privateKey']

    else:
        # Document not found
        return None

def insert_user_address(user_id, user_handle, public_key, private_key):
    # Initialize Firestore database
    db = firestore.client()

    user = get_user(user_id)
    wallet_count = user['walletCount']
    wallet_count += 1

    # Define the document reference using the user ID
    doc_ref = db.collection('addresses').document(str(user_id)+'_'+str(wallet_count))

    # Create the data to be inserted
    data = {
        'userId': str(user_id),
        'userHandle': user_handle,
        'publicKey': public_key,
        'privateKey': private_key
    }

    # Insert the data into the document
    doc_ref.set(data)

    user['walletCount'] = wallet_count
    update_user(user_id,user)

def get_tokens():
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "tokens"

    # Get all documents in the collection
    doc_ref = db.collection(collection_name)
    doc_snapshot = doc_ref.get()

    # Check if there are any documents in the collection
    if len(doc_snapshot) > 0:        # Retrieve data from all documents
        tokens = [doc.to_dict() for doc in doc_snapshot]
        return tokens
    else:
        # Collection is empty
        return []

def get_token(symbol):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "tokens"
    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).where("symbol", "==", symbol)
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot != []:
        # Get the data from the document
        data = doc_snapshot[0].to_dict()
        return data

    else:
        # Document not found
        return None

def insert_token(symbol, address, decimal, chain):
    # Initialize Firestore database
    db = firestore.client()

    # Define the document reference using the user ID
    doc_ref = db.collection('tokens').document(str(symbol)+"_"+chain)

    # Create the data to be inserted
    data = {
        'symbol': symbol,
        'address': address,
        'decimal': decimal,
        'chain': chain,
    }

    # Insert the data into the document
    doc_ref.set(data)

def get_order(user_id):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "orders"
    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).where("user_id", "==", user_id)
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot != []:
        # Get the data from the document
        data = doc_snapshot[0].to_dict()
        return data

    else:
        # Document not found
        return None

def insert_order(order):
    # Initialize Firestore database
    db = firestore.client()

    doc_ref = db.collection('orders').document()

    order['inserted_at'] = datetime.datetime.now()

    doc_ref.set(order)

def get_user(user_id):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "users"

    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).document(str(user_id))
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot.exists:
        # Get the data from the document
        data = doc_snapshot.to_dict()

        return data

def insert_new_user(user_id, user_handle):
    # Initialize Firestore database
    db = firestore.client()

    # Define the document reference using the user ID
    doc_ref = db.collection('users').document(str(user_id))

    # Create the data to be inserted
    data = {
        'userId': str(user_id),
        'userHandle': user_handle,
        'walletCount': 0,
    }

    # Insert the data into the document
    doc_ref.set(data)

def update_user(user_id, user):
    # Initialize Firestore database
    db = firestore.client()

    # Define the document reference using the user ID
    doc_ref = db.collection('users').document(str(user_id))

    doc_ref.set(user)