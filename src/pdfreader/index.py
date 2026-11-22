from fastapi import FastAPI,File, UploadFile
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import WebBaseLoader


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain.messages import HumanMessage,SystemMessage

from qdrant_client.models import (Filter, FieldCondition, MatchValue, MatchAny)

import os
import getpass
from pydantic import BaseModel, ConfigDict
import uuid
from typing import List


from .parser import pdf_upload_service


load_dotenv()
app = FastAPI()

db_url = os.environ["QDRANT_URL"]
db_api = os.environ["QDRANT_API_KEY"]

if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass("Get Gemini Api Key")

if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass("Get Groq Api Key")


embedding_model = GoogleGenerativeAIEmbeddings(model='gemini-embedding-2')
client = QdrantClient(
    url=db_url,
    api_key=db_api,
    cloud_inference=True,
    timeout=120
)

def db_instance(col_name:str):
    return QdrantVectorStore(
        client=client,
        collection_name=col_name,
        embedding=embedding_model
    )

@app.post("/upload")
async def upload_ingest(uploaded_file:list[UploadFile]= File(...)):

    # file_data = await uploaded_file.read()
    uploaded_files = [x for x in uploaded_file]
    print(uploaded_files)

    files_names = []
    for files in uploaded_file:
        file_data = await files.read()
        
        if file_data == None:
            return "file upload error"
        # if file_data.content_type != "application/pdf":
        #     return "file not pdf"
        
        cust_dir_name = "assets"

        cust_dir = os.makedirs(cust_dir_name,exist_ok=True)
        filename = f"{uuid.uuid4()}.pdf"
        final_path = os.path.join(cust_dir_name,  filename)

        with open(final_path,"wb") as f:
            f.write(file_data)

        files_names.append(filename)

    final_collections = []
    for files in files_names:
        curr_data = pdf_upload_service(pdfname=files )

        
        splitted_text = RecursiveCharacterTextSplitter(
            chunk_size = 500,
            chunk_overlap =110
        )
        chunks =splitted_text.split_documents(curr_data)

        # print(files.filename)

        if not client.collection_exists(files):
            client.create_collection(files,vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
                                timeout = 120)
        instance = db_instance(files)
        ingested_collections = instance.add_documents(chunks)
        final_collections.append(ingested_collections)
    return {
        "collection":ingested_collections
    }





@app.get("/load")
def load():
    loader = WebBaseLoader("https://docs.langchain.com/oss/python/learn")

    docs = loader.load()

    return [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]