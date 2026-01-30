import os
from langchain.agents import create_agent
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver  
from dotenv import load_dotenv
from langchain_google_genai  import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from key_manager.gemini_key_manager import key_manager

load_dotenv()
def create_rag_chain(phase_id: str, qa_system_prompt: str, input: str):

    new_key = key_manager.get_key()
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=new_key)

    embeddings = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004"
        )
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir,"..", "db")
    persistent_directory = os.path.join(db_dir, f"chroma_db_with_metadata_{phase_id}")

    # Check if the Chroma vector store already exists
    if os.path.exists(persistent_directory):
        print("Loading existing vector store...")
        
    else:
        db = Chroma.from_documents(
            documents=[],
            embedding=embeddings,
            persist_directory=persistent_directory
        )

    # Load the existing vector store with the embedding function
    db = Chroma(persist_directory=persistent_directory,
                embedding_function=embeddings)


    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10},
    )


    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, just "
        "reformulate it if needed and otherwise return it as is."
    )


    # Create a prompt template for contextualizing questions
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            ("human", "{input}"),
        ]
    )


    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    result1 = history_aware_retriever.invoke({"input": input})
    print(f"History-aware-retriever: {result1}")

    # qa_system_prompt = (
    #     "Sử dụng các thông tin có sẵn để phát hiện các functional requirements và non-functional requirements từ yêu cầu của người dùng"
    #     "\n\n"
    #     "{context}"
    # )


    # Create a prompt template for answering questions
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            ("human", "{input}"),
        ]
    )


    # Create a chain to combine documents for question answering
    # `create_stuff_documents_chain` feeds all retrieved context into the LLM
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Create a retrieval chain that combines the history-aware retriever and the question answering chain
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain)
    
    return rag_chain