import pandas as pd
import os
import json

class CacheManager:
    @staticmethod
    def save(df: pd.DataFrame, filename: str, directory: str = "tests/output"):
        if not os.path.exists(directory):
            os.makedirs(directory)
        path = os.path.join(directory, filename)
        df.to_csv(path, index=False)
        print(f"Data saved to {path}")

    @staticmethod
    def load(filename: str, directory: str = "tests/output"):
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            print(f"Loading data from {path}")
            return pd.read_csv(path)
        return None

    @staticmethod
    def save_json(data: dict, filename: str, directory: str = "tests/output/cache"):
        if not os.path.exists(directory):
            os.makedirs(directory)
        path = os.path.join(directory, filename)
        with open(path, 'w') as f:
            json.dump(data, f)
            
    @staticmethod
    def load_json(filename: str, directory: str = "tests/output/cache"):
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None
