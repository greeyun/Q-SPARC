import json
from langchain_community.document_loaders import JSONLoader
from langchain_community.embeddings import HuggingFaceEmbeddings # You can replace with OpenAIEmbeddings or another model
from langchain.schema import Document
from langchain_chroma import Chroma

# --- 1. Load and parse the original JSON data ---

# Define file path and JQ schema
file_path = '/hpc/fxu244/Documents/Code/LLMs/a-b-via-c.json'
jq_schema = '.results.bindings[]'

# text_content=False is critical; it preserves each element's JSON structure
loader = JSONLoader(
    file_path=file_path,
    jq_schema=jq_schema,
    text_content=False 
)

# Load documents; each document's page_content is a JSON string
raw_docs = loader.load()

# --- 2. Transform data to the target format and create LangChain Document objects ---
def get_val(record, key):
    """Safely extract the 'value' for the given key from the record"""
    if key in record and isinstance(record.get(key), dict):
        return record[key].get('value')
    return None # Return None if key doesn't exist or format is invalid

final_documents = []
for doc in raw_docs:
    # Parse page_content (JSON string) into a Python dictionary
    record = json.loads(doc.page_content)

    # Extract and transform data in the desired format
    clean_data = {
        "Neuron_ID": get_val(record, "Neuron_ID"),
        "A": get_val(record, "A"),
        "B": get_val(record, "B"),
        "C": get_val(record, "C"),
        "Target_Organ": get_val(record, "Target_Organ"),
        # Special handling for C_Type; set to "N/A" if missing
        "C_Type": get_val(record, "C_Type") if "C_Type" in record else "N/A",
    }
    
    # For better semantic search, convert structured data to meaningful text
    # This text will be used to generate vector embeddings
    page_content = (
        f"Neuron connection info: Neuron ID is {clean_data['Neuron_ID']}."
        f" It connects from {clean_data['A']} to {clean_data['B']} via {clean_data['C']}."
        f" The target organ is {clean_data['Target_Organ']}."
        f" Connection type (C_Type) is {clean_data['C_Type']}."
    )

    # Create a new LangChain Document object
    # page_content is used for vector search
    # metadata stores clean structured data for filtering or use
    final_documents.append(
        Document(page_content=page_content, metadata=clean_data)
    )

# Print the first processed document as a check
if final_documents:
    print("--- Sample of first processed Document ---")
    print(f"Page Content: {final_documents[0].page_content}")
    print(f"Metadata: {final_documents[0].metadata}")
    print("-" * 30)


# --- 3. Initialize embedding model and vector database, then add documents ---

# Initialize an embedding model. This uses HuggingFace's open-source model, which runs locally.
# The model will be downloaded automatically the first time.
# You can also replace it with OpenAIEmbeddings(openai_api_key="sk-...") or other models.
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# from_documents handles embedding and indexing of all documents
print("Creating vector database, this might take a while...")

vector_store = Chroma.from_documents(
    final_documents,
    # embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
    embedding = embeddings
)

print("Vector database created successfully!")

# --- 4. (Optional) Demo: How to use the vector database ---
print("\n--- Similarity Search Demo ---")

query = 'Is there a connection from inferior mesenteric ganglion to the urinary bladder in rats? Summarize the pathways based on the nerves involved.'
results = vector_store.similarity_search(query, k=10)

if results:
    print(f"Query: '{query}'")
    print("\nTop relevant result:",results)
