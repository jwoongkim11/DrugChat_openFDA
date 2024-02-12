from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY")
DB_FAISS_PATH = os.getenv("DB_FAISS_PATH")
LLM_EMBEDDER_MODEL_NAME =  os.getenv("LLM_EMBEDDER_MODEL_NAME")
common_source = '/Users/jay/Desktop/Prj_qarag/AI_openFDA/instruction_file/json/'
