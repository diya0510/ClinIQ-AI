from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.chains import conversational_retrieval

load_dotenv()

def build_knowldeg_base(summary_str,health_str):
    doc1=Document(page_content=f"Report Summary:{summary_str}",metadata="Report Summary")
    doc2=Document(page_content=f"Health profile:{health_str}",metadata="Health Profile")

    docs=[doc1,doc2]

    splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)
    chunks=splitter.split_documents(docs)

    embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")