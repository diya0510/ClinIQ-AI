from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Load PDF
loader = PyPDFLoader("Guidelines.pdf")
docs = loader.load()

# Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)
chunks = text_splitter.split_documents(docs)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Create FAISS vector store from chunks
vectorstore = FAISS.from_documents(chunks, embeddings)

# Save FAISS index locally
vectorstore.save_local("faiss_index")
