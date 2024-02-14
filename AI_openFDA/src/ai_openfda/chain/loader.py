#Question을 Embedding하기위한 용도
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
import config

print("load vector_db start")

model_kwargs = {'device': 'cpu'} # set 'cuda' if you have a GPU
encode_kwargs = {'normalize_embeddings': True} # set True to compute cosine similarity

#Loading embedding model
llm_embedder_model = HuggingFaceBgeEmbeddings(
    model_name=config.LLM_EMBEDDER_MODEL_NAME,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    query_instruction="Represent this query for retrieving relevant documents: "
) 
# The directory where your vector database is saved
persist_directory = config.DB_FAISS_PATH

# Load the existing vector database
vector_db = FAISS.load_local(persist_directory, embeddings = llm_embedder_model)

print("load vector_db end")
