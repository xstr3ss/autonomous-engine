import re

with open("repo_indexer.py", "r") as f:
    code = f.read()

# Upgrade to the v1.11+ Qdrant API
code = code.replace("results = self.client.search(", "results = self.client.query_points(")
code = code.replace("query_vector=query_vector", "query=query_vector")
code = code.replace("for hit in results", "for hit in results.points")

with open("repo_indexer.py", "w") as f:
    f.write(code)

print("✅ Qdrant API updated to latest v1.11+ specs!")
