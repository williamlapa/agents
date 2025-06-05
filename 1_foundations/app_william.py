from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader # Ainda útil para carregar diretamente, mas o RAG vai mais longe
import gradio as gr

# Importações para RAG
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA # Para orquestrar recuperação e geração
from langchain.prompts import PromptTemplate # Para templates de prompt
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage # Para histórico de mensagens


load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


class Me:

    def __init__(self):
        self.openai_client = OpenAI() # Renomeado para evitar conflito com self.openai do LangChain
        self.name = "William Lapa" # !!! IMPORTANTE: Mudar para o seu nome
        
        # O LinkedIn e o resumo serão carregados pelo RAG, não mais diretamente aqui
        self.linkedin = "" 
        self.summary = ""

        # Configuração do RAG
        self.VECTOR_DB_PATH = "vector_db"
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        
        # Carregar o banco de dados vetorial persistente
        try:
            self.vector_store = Chroma(persist_directory=self.VECTOR_DB_PATH, embedding_function=self.embeddings)
            print("Base de conhecimento ChromaDB carregada com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar ChromaDB: {e}. Certifique-se de ter executado 'prepare_knowledge_base.py' primeiro.")
            self.vector_store = None # Ou adicione lógica para recriar se for o caso


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        # O system_prompt agora será mais genérico, o contexto específico virá do RAG
        system_prompt = f"Você está agindo como {self.name}. Você está respondendo a perguntas no site de {self.name}, " \
                        f"particularmente perguntas relacionadas à carreira, histórico, habilidades e experiência de {self.name}. " \
                        f"Sua responsabilidade é representar {self.name} para interações no site da forma mais fiel possível. " \
                        f"Use o contexto fornecido para responder às perguntas. " \
                        f"Seja profissional e engajador, como se estivesse conversando com um potencial cliente ou futuro empregador que encontrou o site. " \
                        f"Se você não souber a resposta para alguma pergunta, use sua ferramenta record_unknown_question para registrar a pergunta que você não conseguiu responder, mesmo que seja sobre algo trivial ou não relacionado à carreira. " \
                        f"Se o usuário estiver engajando em discussão, tente direcioná-lo a entrar em contato via e-mail; peça o e-mail dele e registre-o usando sua ferramenta record_user_details. " \
                        f"Com este contexto, por favor, converse com o usuário, sempre mantendo o personagem de {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        # Formatar o histórico para o LangChain
        # O LangChain espera uma lista de objetos Message
        langchain_history = []
        for msg in history:
            if msg['role'] == 'user':
                langchain_history.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                langchain_history.append(AIMessage(content=msg['content']))
        
        # Adicionar a mensagem atual do usuário
        langchain_history.append(HumanMessage(content=message))

        # Configurar o RAG
        if self.vector_store is None:
            # Fallback se a base de conhecimento não foi carregada
            print("Base de conhecimento não disponível, respondendo sem RAG.")
            messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        else:
            # Criar um Retriever a partir do Vector Store
            retriever = self.vector_store.as_retriever(search_kwargs={"k": 3}) # k é o número de chunks mais relevantes para buscar

            # Recuperar documentos relevantes para a pergunta do usuário
            retrieved_docs = retriever.invoke(message)
            
            # Construir o contexto a partir dos documentos recuperados
            context_from_rag = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # Incorporar o contexto recuperado no prompt do sistema
            # Isso é uma forma de "injetar" o contexto relevante no LLM
            rag_system_prompt = self.system_prompt() + "\n\n## Contexto Recuperado:\n" + context_from_rag

            messages = [{"role": "system", "content": rag_system_prompt}] + history + [{"role": "user", "content": message}]

        done = False
        while not done:
            response = self.openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()

    title = "Converse com William Lapa"
    description = """
    Olá! Eu sou o assistente virtual de William Lapa, pronto para responder às suas perguntas sobre a carreira, projetos e experiência dele. 
    Sinta-se à vontade para perguntar!
    """

    initial_message = "Olá! Sou o avatar digital de William Lapa. Como posso ajudar você hoje?"
    history_default = [{"role": "assistant", "content": initial_message}]

    avatar_images = ("../assets/william_usuario.png", "../assets/william_avatar.png")

    gr.ChatInterface(
        fn=me.chat,
        title=title,
        description=description,
        examples=[
            "Quais são os principais projetos do William?",
            "Fale sobre a experiência de William em mineração de dados.",
            "Como posso entrar em contato com o William?"
        ],
        chatbot=gr.Chatbot(
            label="Conversa com William Lapa",
            show_copy_button=True,
            show_share_button=False,
            height=500,
            avatar_images=avatar_images,
            value=history_default,  # Mensagem inicial
            type="messages"         # Usa o novo formato openai-style
        ),
        #clear_button="Limpar Conversa",
        # submit_button="Enviar"
    ).launch()