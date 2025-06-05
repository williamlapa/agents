from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
import git # Para clonar repositórios (opcional)
from pathlib import Path # Para manipular caminhos de arquivo

load_dotenv(override=True)

DATA_PATH = "me"
PROJECTS_PATH = "projects_temp" # Novo diretório para clonar projetos
VECTOR_DB_PATH = "vector_db"

def load_directory_documents(directory_path):
    """Carrega documentos de texto de um diretório."""
    loader_documents = []
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            # Defina os tipos de arquivo que você deseja incluir
            if file_name.endswith(('.py', '.md', '.txt', '.json', '.yaml', '.yml', '.rst')):
                file_path = os.path.join(root, file_name)
                try:
                    # Usar TextLoader para carregar o conteúdo do arquivo como um documento
                    loader = TextLoader(file_path, encoding="utf-8")
                    loader_documents.extend(loader.load())
                    print(f"  Carregado: {file_path}")
                except Exception as e:
                    print(f"  Erro ao carregar {file_path}: {e}")
    return loader_documents

def prepare_knowledge_base():
    documents = []

    # --- Carregar documentos existentes ---
    print("Carregando LinkedIn PDF...")
    pdf_loader = PyPDFLoader(os.path.join(DATA_PATH, "linkedin_william.pdf"))
    documents.extend(pdf_loader.load())
    print(f"Documentos PDF carregados: {len(documents)}")

    print("Carregando Summary TXT...")
    text_loader = TextLoader(os.path.join(DATA_PATH, "summary_william.txt"), encoding="utf-8")
    documents.extend(text_loader.load())
    print(f"Total de documentos carregados (PDF e TXT): {len(documents)}")

    # --- Adicionar projetos do GitHub ---
    github_repos = [
        "https://github.com/williamlapa/extrator-finan-as.git", # Substitua pelo URL do seu repo
        "https://github.com/williamlapa/BeachVolleyChallenge.git",
        "https://github.com/williamlapa/dividendos.git",
        "https://github.com/williamlapa/ssa2025-painel.git",
        "https://github.com/williamlapa/funpresp.git",
        "https://github.com/williamlapa/mestrado_mineracao.git"        
        # Adicione mais URLs de repositórios conforme necessário
    ]

    # Crie o diretório temporário se não existir
    os.makedirs(PROJECTS_PATH, exist_ok=True)

    print("\nClonando e carregando projetos do GitHub...")
    for repo_url in github_repos:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(PROJECTS_PATH, repo_name)

        if os.path.exists(repo_path):
            print(f"  Repositório '{repo_name}' já existe. Ignorando clonagem.")
            # Opcional: git pull para atualizar se quiser
            # try:
            #     repo = git.Repo(repo_path)
            #     origin = repo.remotes.origin
            #     origin.pull()
            #     print(f"  Atualizado '{repo_name}'.")
            # except Exception as e:
            #     print(f"  Erro ao atualizar '{repo_name}': {e}")
        else:
            print(f"  Clonando {repo_url} para {repo_path}...")
            try:
                git.Repo.clone_from(repo_url, repo_path)
                print(f"  Clonagem de '{repo_name}' concluída.")
            except Exception as e:
                print(f"  Erro ao clonar {repo_url}: {e}")
                continue # Pula para o próximo repositório se houver erro na clonagem

        # Carregar documentos do repositório clonado
        print(f"  Carregando documentos de '{repo_name}'...")
        documents.extend(load_directory_documents(repo_path))
        print(f"  Documentos de '{repo_name}' carregados. Total atual: {len(documents)}")

    # --- Processar e indexar todos os documentos ---
    print("\nDividindo documentos em chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Total de chunks: {len(chunks)}")

    print("Gerando embeddings e armazenando no ChromaDB...")
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # Criar ou carregar o banco de dados vetorial
    vector_store = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=VECTOR_DB_PATH
    )
    # vector_store.persist()  # Remova ou comente esta linha
    print("Base de conhecimento preparada e salva!")

if __name__ == "__main__":
    prepare_knowledge_base()