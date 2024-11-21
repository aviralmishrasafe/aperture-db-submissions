import os
import boto3
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss  
from langchain_community.llms import OpenAI
from aperturedb import Utils
from docx import Document
import tempfile
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

S3_BUCKET_NAME = "aperturedb-bucket"
S3_REGION = "us-west-2"
s3_client = boto3.client('s3', region_name=S3_REGION)

def fetch_all_s3_keys():
    file_paths = []
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET_NAME)
    for page in pages:
        for obj in page.get('Contents', []):
            file_paths.append(f"s3://{S3_BUCKET_NAME}/{obj['Key']}")
    return file_paths

def fetch_s3_file(file_path):
    try:
        bucket = file_path.split("/")[2]
        key = "/".join(file_path.split("/")[3:])
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        if file_path.endswith(".docx"):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(response["Body"].read())
                tmp_path = tmp_file.name
            doc = Document(tmp_path)
            content = "\n".join([p.text for p in doc.paragraphs])
            os.remove(tmp_path)
            return content
        else:
            return response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching file {file_path}: {e}")
        return None

def split_text_into_chunks(text, chunk_size=500, overlap=50):
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    return text_splitter.split_text(text)

def get_user_id(db, username):
    query = [
        {
            "FindEntity": {
                "with_class": "User",
                "constraints": {
                    "name": ["==", username]
                },
                "results": {
                    "all_properties": True
                }
            }
        }
    ]
    db.query(query)
    if not db.last_query_ok():
        print(f"Error fetching user ID for username: {username}")
        print(db.response)
        return None

    response = db.response
    users = response[0].get("FindEntity", {}).get("entities", [])
    if not users:
        print(f"No user found with username: {username}")
        return None

    return users[0].get("user_id")

def get_user_files(db, user_id):
    query = [
        {
            "FindEntity": {
                "with_class": "User",
                "_ref": 1,
                "constraints": {
                    "user_id": ["==", user_id]
                }
            }
        },
        {
            "FindEntity": {
                "with_class": "File",
                "is_connected_to": {
                    "ref": 1  # Fetch all files directly connected to the user
                },
                "results": {
                    "all_properties": True
                }
            }
        }
    ]
    print(f"Querying ApertureDB for files accessible by user_id: {user_id}")
    db.query(query)

    if not db.last_query_ok():
        print("Error fetching files for user.")
        print(db.response)
        return []

    response = db.response
    files = response[1].get("FindEntity", {}).get("entities", [])
    file_paths = [file.get("path") for file in files if "path" in file]
    print(f"User has access to {len(file_paths)} files.")
    return file_paths

def create_embeddings_for_all_s3():
    s3_keys = fetch_all_s3_keys()

    if not s3_keys:
        print("No files found in S3 bucket.")
        return

    print(f"Found {len(s3_keys)} files in S3 bucket. Creating embeddings...")

    embeddings_model = OpenAIEmbeddings()
    dimension = len(embeddings_model.embed_query("test"))
    import faiss
    index = faiss.IndexFlatL2(dimension)
    vector_store = FAISS(
        index=index,
        docstore=InMemoryDocstore({}),
        index_to_docstore_id={},
        embedding_function=embeddings_model.embed_query,
    )

    for s3_key in s3_keys:
        content = fetch_s3_file(s3_key)
        if content is None:
            print(f"Skipping {s3_key} due to missing content.")
            continue

        chunks = split_text_into_chunks(content)
        valid_chunks = [chunk for chunk in chunks if len(chunk.strip()) > 0]
        metadatas = [{"file_path": s3_key}] * len(valid_chunks)

        embeddings = [embeddings_model.embed_query(chunk) for chunk in valid_chunks]
        embeddings = [embed for embed in embeddings if len(embed) == dimension]

        if not embeddings:
            print(f"No valid embeddings for file: {s3_key}")
            continue

        vector_store.add_texts(valid_chunks, metadatas)

    vector_store.save_local("faiss_index")
    print("Embeddings successfully created and stored in FAISS.")


def query_vector_store(query, user_name, db, vector_store_dir="faiss_index"):
    embeddings_model = OpenAIEmbeddings()

    vector_store = FAISS.load_local(
        vector_store_dir,
        embeddings=embeddings_model.embed_query,
        allow_dangerous_deserialization=True
    )

    user_id = get_user_id(db, user_name)
    if not user_id:
        print(f"User {user_name} not found in ApertureDB.")
        return []

    file_paths = get_user_files(db, user_id)
    if not file_paths:
        print(f"No accessible files for user {user_name}.")
        return []

    retrieved_chunks = vector_store.similarity_search(query, k=10)

    allowed_chunks = [
        chunk for chunk in retrieved_chunks
        if chunk.metadata["file_path"] in file_paths
    ]

    return allowed_chunks




def generate_response(query, allowed_chunks):
    if not allowed_chunks:
        return "You do not have access to any relevant information for this query."

    max_context_length = 7000  
    context = ""
    token_count = 0

    for chunk in allowed_chunks:
        chunk_tokens = len(chunk.page_content.split())
        if token_count + chunk_tokens > max_context_length:
            break
        context += chunk.page_content + "\n\n"
        token_count += chunk_tokens

    llm = ChatOpenAI(model="gpt-4", temperature=0)

    messages = [
        SystemMessage(content="You are an intelligent assistant."),
        HumanMessage(content=f"Context:\n{context}\n\nQuery:\n{query}")
    ]

    try:
        response = llm(messages)
        return response.content
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    db = Utils.create_connector()

    recompute_mode = False  # Set to True for recomputing embeddings, False for querying
    if recompute_mode:
        print("Recomputing embeddings for all S3 files...")
        create_embeddings_for_all_s3()
        print("Embeddings recomputed successfully.")
    else:
        username = "janeroberts@realm258.onmicrosoft.com"  # Replace with desired username
        # username = "RobBobby@Realm258.onmicrosoft.com"
        query = "What is the content of Nvidia News.docx?" 

        print(f"Querying ApertureDB for user {username}...")
        allowed_chunks = query_vector_store(query, username, db)

        print(f"Generating response for query: {query}")
        response = generate_response(query, allowed_chunks)
        print(f"Response:\n{response}")

if __name__ == "__main__":
    main()
