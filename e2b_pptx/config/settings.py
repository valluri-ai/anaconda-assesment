from environs import Env

env = Env()
env.read_env()

# Environment variables
E2B_API_KEY = env("E2B_API_KEY")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
LANGCHAIN_PROJECT = "e2b-pptx"
E2B_TEMPLATE_ID = "dpqrnnze53ej8u1pu2p1"
 
# Set environment variables
import os
os.environ["E2B_API_KEY"] = E2B_API_KEY
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
os.environ["E2B_TEMPLATE_ID"] = E2B_TEMPLATE_ID

# Constants
OUTPUT_DIR = "generated_presentations"