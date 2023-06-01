import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/serviceAccountKey.json")  # Replace with the path to your service account key JSON file
firebase_admin.initialize_app(cred)

# Function to fetch addresses for a user
def fetch_user_addresses(user_id):
    # Access the Firestore database
    db = firestore.client()

    # Collection name
    collection_name = "addresses"

    # Get the document for the specified chat_id
    doc_ref = db.collection(collection_name).document(str(chat_id))
    doc_snapshot = doc_ref.get()

    # Check if the document exists
    if doc_snapshot.exists:
        # Get the data from the document
        data = doc_snapshot.to_dict()

        # Get the addresses associated with the user
        addresses = data.get("addresses", [])

        # Return the addresses
        return addresses

    else:
        # Document not found
        return []

# Example usage
chat_id = 123456789  # Replace with the chat ID of the user
user_addresses = fetch_user_addresses(chat_id)
print(user_addresses)
