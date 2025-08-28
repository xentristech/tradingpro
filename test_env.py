import os
from dotenv import load_dotenv

p = r"configs\.env"
print("PWD:", os.getcwd())
print("ENV PATH:", p)
print("Exists?", os.path.exists(p))
load_dotenv(p)
print("TWELVEDATA_API_KEY:", os.getenv("TWELVEDATA_API_KEY"))
