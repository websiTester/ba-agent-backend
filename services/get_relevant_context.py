import os
from dotenv import load_dotenv
from langchain_google_genai  import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()
def get_relevant_context(query: str, phaseId: str, source: list[str] = None):
    
    embeddings = GoogleGenerativeAIEmbeddings(
            model="text-embedding-004"
        )
    

    # Define the persistent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(current_dir,"..", "db")
    persistent_directory = os.path.join(db_dir, f"chroma_db_with_metadata_{phaseId}")

    if(not os.path.exists(persistent_directory)):
        raise FileNotFoundError(f"The vector store database file does not exist at {persistent_directory}")

    # Load the existing vector store with the embedding function
    db = Chroma(persist_directory=persistent_directory,
                embedding_function=embeddings)
    
    # Retrieve relevant documents based on the query
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10},
    )

    if source is not None:
        source_list = []
        for s in source:
            s = s.replace(" ", "_")
            source_list.append(s)

        retriever.search_kwargs["filter"] = {
            "source": {
                "$in": source_list
            }
        }
    
    relevant_docs = retriever.invoke(query)

    context = ""
    for i,doc in enumerate(relevant_docs,1):
        context += f"Document {i}:\n{doc.page_content}\n"
        context += f"Source: {doc.metadata['source']}\n\n"
    return context

