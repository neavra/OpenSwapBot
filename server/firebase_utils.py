import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from dotenv import load_dotenv
load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
app = firebase_admin.initialize_app(cred)

# Function to fetch addresses for a user
def get_user_address(user_id):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "addresses"

    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).document(str(user_id))
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot.exists:
        # Get the data from the document
        data = doc_snapshot.to_dict()

        # Get the addresses associated with the user
        publicKey = data.get("publicKey", [])
        privateKey = data.get("privateKey")


        # Return the addresses
        return [publicKey, privateKey]

    else:
        # Document not found
        return []

def insert_user_address(user_id, public_key, private_key):
    # Initialize Firestore database
    db = firestore.client()

    # Define the document reference using the user ID
    doc_ref = db.collection('addresses').document(str(user_id))

    # Create the data to be inserted
    data = {
        'publicKey': public_key,
        'privateKey': private_key
    }

    # Insert the data into the document
    doc_ref.set(data)