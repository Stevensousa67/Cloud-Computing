import os, json

CLIENT_SECRET_FILE = os.environ.get('CLIENT_SECRET_FILE', 'client_secret.json')

print(f"CLIENT_SECRET_FILE: {CLIENT_SECRET_FILE}")

if not os.path.exists(CLIENT_SECRET_FILE):
    print(f"File {CLIENT_SECRET_FILE} not found")
else:
    with open(CLIENT_SECRET_FILE) as f:
        data = json.load(f)
        print(f"Data from {CLIENT_SECRET_FILE}: {data}")

print("Current working directory:", os.getcwd())