import os

# Set local paths BEFORE importing edgar to prevent sandbox permission errors on ~/.edgar
output_data = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output/data"))
output_cache = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output/cache"))
os.makedirs(output_data, exist_ok=True)
os.makedirs(output_cache, exist_ok=True)

os.environ["EDGAR_LOCAL_DATA_DIR"] = output_data
os.environ["EDGAR_CACHE_DIR"] = output_cache
os.environ["EDGAR_IDENTITY"] = "Value Investing Screener screener@example.com"
