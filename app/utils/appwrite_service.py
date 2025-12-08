from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.query import Query 
from appwrite.exception import AppwriteException
import os 
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize the Appwrite Client
client = Client()

# Configure the client with your administrative keys
(client
  .set_endpoint(os.getenv('APPWRITE_ENDPOINT')) 
  .set_project(os.getenv('APPWRITE_PROJECT_ID')) 
  .set_key(os.getenv('APPWRITE_SECRET'))
  .set_self_signed() 
)

# Initialize the Storage service
storage = Storage(client)

try:
    # 2. CORRECTED CALL: Use the 'queries' argument with Query.limit()
    storage.list_buckets(queries=[
        Query.limit(1)
    ])
    
    # If the call succeeds without raising an exception
    print(f"Connection successful to the Appwrite Storage service in project: **{os.getenv('APPWRITE_PROJECT_ID')}**")

except AppwriteException as e:
    # If an Appwrite-specific exception occurs
    print(f"Connection unsuccessful. Appwrite Error: {e.message}")
except Exception as e:
    # Catch any other general exceptions
    print(f"Connection unsuccessful. General Error: {e}")