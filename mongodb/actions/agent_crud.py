from mongodb.actions.connection import get_db_connection


def get_collection(collection_name: str):
    db = get_db_connection("mastraDB2")
    collection = db[collection_name]
    return collection


def get_agent_by_name(name: str):
    collection = get_collection("agents")
    result = collection.find_one({"agentName": name})
    return result




