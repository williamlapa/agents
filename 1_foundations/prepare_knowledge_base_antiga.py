from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os

load_dotenv(override=True)

# Defina o diretório onde estão seus arquivos de contexto
DATA_PATH = "me"
VECTOR_DB_PATH = "vector_db" # Onde o ChromaDB vai armazenar os embeddings

def prepare_knowledge_base():
    documents = []

    # Carregar LinkedIn PDF
    print("Carregando LinkedIn PDF...")
    pdf_loader = PyPDFLoader(os.path.join(DATA_PATH, "linkedin_william.pdf"))
    documents.extend(pdf_loader.load())
    print(f"Documentos PDF carregados: {len(documents)}")

    # Carregar Summary TXT
    print("Carregando Summary TXT...")
    text_loader = TextLoader(os.path.join(DATA_PATH, "summary_william.txt"), encoding="utf-8")
    documents.extend(text_loader.load())
    print(f"Total de documentos carregados: {len(documents)}")

    # Dividir documentos em pedaços (chunks)
    print("Dividindo documentos em chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Total de chunks: {len(chunks)}")

    # Gerar embeddings e armazenar no Vector Database
    print("Gerando embeddings e armazenando no ChromaDB...")
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002") # Modelo de embeddings da OpenAI
    
    # Criar ou carregar o banco de dados vetorial
    # Se já existir, ele o carrega; caso contrário, ele o cria.
    vector_store = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory=VECTOR_DB_PATH
    )
    vector_store.persist() # Salva os embeddings no disco
    print("Base de conhecimento preparada e salva!")

if __name__ == "__main__":
    prepare_knowledge_base()