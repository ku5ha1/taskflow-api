from fastapi import FastAPI, File, UploadFile, HTTPException, status
from app.utils.database import Base, engine
from app.routes.user import router as user_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
from appwrite.id import ID
from appwrite.input_file import InputFile
import asyncio
import os
from app.utils.appwrite_service import storage
from dotenv import load_dotenv

load_dotenv()

app = FastAPI() 

def init_db():
    Base.metadata.create_all(bind=engine)

app.include_router(user_router)
app.include_router(project_router)
app.include_router(task_router)

@app.get("/health")
async def get_health():
    return {"message": "API running successfully"}

@app.on_event("startup")
async def startup_event():
    init_db()
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID", "<YOUR_PROJECT_ID>")
APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY", "<YOUR_API_KEY>") 
APPWRITE_BUCKET_ID = os.environ.get("APPWRITE_BUCKET_ID", "<YOUR_BUCKET_ID>")
    
@app.post("/upload_to_appwrite/")
async def upload_file_to_appwrite(file: UploadFile = File(...)):
    """
    Receives a file and uploads it to an Appwrite bucket using InputFile.
    """
    try:
        # 1. Read the file content asynchronously
        contents = await file.read()
        
        # 2. **FIXED STEP:** Create an InputFile object from the bytes
        # You must provide the file content (bytes) and the original filename.
        appwrite_file_input = InputFile.from_bytes(
            bytes=contents,
            filename=file.filename # Provides the filename to Appwrite
        )
        
        # 3. Upload the InputFile object to Appwrite Storage
        appwrite_file = storage.create_file(
            bucket_id=APPWRITE_BUCKET_ID,
            file_id=ID.unique(),
            file=appwrite_file_input, # <-- Pass the InputFile object
            permissions=['read("any")'],
            # filename is now included in appwrite_file_input, but 
            # Appwrite's SDK is smart enough to handle it.
        )
        
        return {
            "message": "File uploaded successfully!",
            "filename": file.filename,
            "appwrite_file_id": appwrite_file['$id'],
            "appwrite_file_url": f"{APPWRITE_ENDPOINT}/storage/buckets/{APPWRITE_BUCKET_ID}/files/{appwrite_file['$id']}/view"
        }
    except Exception as e:
        # Catch and print the exact Appwrite SDK error if there is one
        print(f"Appwrite SDK Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed. Check server logs for details."
        )
    finally:
        await file.close()