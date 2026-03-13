import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")

ACTIVE_MODEL = "cerebras/gpt-oss-120b"


EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, ~80MB download


CHUNK_SIZE = 300
CHUNK_OVERLAP = 50

TOP_K_CHUNKS = 3

# ChromaDB storage — local folder, no server needed
CHROMA_DB_PATH = "./data/chroma_db"
CHROMA_COLLECTION = "resume_chunks"


OUTPUT_DIR = "./output"
REPORT_FILENAME = "job_analysis_report.md"
