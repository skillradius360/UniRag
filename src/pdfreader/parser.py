from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import WebBaseLoader

webData = WebBaseLoader(
"https://www.google.com"
)

print(webData)


def pdf_upload_service(pdfname:str):
    try:
        loader = PyPDFLoader(f"./assets/{pdfname}")
        loaded = loader.load()
    except Exception as e:
        raise  Exception("The error is "+ e)
    
    return loaded