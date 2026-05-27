import requests
import msal

# ===== CONFIGURATION =====
TENANT_ID = "your-tenant-id"
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
FABRIC_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"

# ===== AUTHENTICATION =====
app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential=CLIENT_SECRET
)

token_result = app.acquire_token_for_client(scopes=FABRIC_SCOPE)
if "access_token" not in token_result:
    raise Exception("Authentication failed: " + str(token_result))

headers = {
    "Authorization": f"Bearer {token_result['access_token']}",
    "Content-Type": "application/json"
}

# ===== GET ALL WORKSPACES =====
workspaces = requests.get(f"{FABRIC_API_BASE}/workspaces", headers=headers).json().get("value", [])

for ws in workspaces:
    ws_id = ws["id"]
    print(f"🔍 Checking workspace: {ws['displayName']}")

    # ===== GET ALL NOTEBOOKS IN WORKSPACE =====
    notebooks = requests.get(f"{FABRIC_API_BASE}/workspaces/{ws_id}/items?type=notebook", headers=headers).json().get("value", [])

    for nb in notebooks:
        nb_id = nb["id"]

        # ===== CHECK NOTEBOOK SESSION STATUS =====
        session_url = f"{FABRIC_API_BASE}/workspaces/{ws_id}/notebooks/{nb_id}/sessions"
        sessions = requests.get(session_url, headers=headers).json().get("value", [])

        for session in sessions:
            if session.get("state") == "Running":
                print(f"⏹ Stopping notebook: {nb['displayName']}")
                stop_url = f"{session_url}/{session['id']}/stop"
                requests.post(stop_url, headers=headers)

print("✅ All running notebooks have been stopped.")