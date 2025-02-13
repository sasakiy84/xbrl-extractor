"""
JSON としてロードできないファイルがあるかどうかをチェックするスクリプト
"""

from pathlib import Path
import json
json_files = Path("json-data").glob("**/*.json")

for json_file in json_files:
    try:
        with open(json_file, "r") as f:
            # ファイルが空かどうかをチェック
            if not f.read(1):
                print(f"Empty file: {json_file}")
                continue
            f.seek(0)
            json.load(f)
    except json.JSONDecodeError as e:
        print(f"Failed to load {json_file}")
        print(e)
    except Exception as e:
        print(f"Failed to load {json_file}")
        print(e)
