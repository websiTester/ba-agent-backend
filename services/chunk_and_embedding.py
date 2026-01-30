import os
from dotenv import load_dotenv
from langchain_google_genai  import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def chunk_and_embedding(document: str, source: str, phaseId: str):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="text-embedding-004"
    )

    source = source.replace(" ", "_")
    
    # Define the directory containing the text files and the persistent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir,"..", "db")
    persistent_directory = os.path.join(db_dir, f"chroma_db_with_metadata_{phaseId}")

    
    print("source: ", source)
    print("\n--- Using Recursive Character-based Splitting ---")
    rec_char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100)



    rec_char_docs = rec_char_splitter.create_documents(
        texts= [document],
        metadatas= [{
            "source": source,
            "phaseId": phaseId
        }]
    )

    if(os.path.exists(persistent_directory)):
        db = Chroma(persist_directory=persistent_directory,
                    embedding_function=embeddings)
        db.add_documents(rec_char_docs)
    else:
        db = Chroma.from_documents(
            rec_char_docs, embeddings, persist_directory=persistent_directory
        )

    return "Document chunked and embedded successfully"


def delete_chunk(phaseId: str, source: str):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="text-embedding-004"
    )

    source = source.replace(" ", "_")
    
    # Define the directory containing the text files and the persistent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir,"..", "db")
    persistent_directory = os.path.join(db_dir, f"chroma_db_with_metadata_{phaseId}")

    if(not os.path.exists(persistent_directory)):
        return "The vector store database file does not exist"

    db = Chroma(persist_directory=persistent_directory,
                embedding_function=embeddings)
    db.delete(where={"source": source})
    return "Chunk deleted successfully"

        