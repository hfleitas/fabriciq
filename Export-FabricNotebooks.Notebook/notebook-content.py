# Fabric notebook source, do not edit manually.

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # Export Fabric Notebook Definitions
# 
# This notebook exports all Fabric Notebook item definitions from a workspace and saves them as files in the attached Lakehouse.

# PARAMETERS CELL ********************

workspace_id = "564dff7b-1a14-4fcc-ba85-b3d901f12934"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import requests
import base64
import json
import re
from datetime import datetime
from notebookutils import mssparkutils

# Get access token for Fabric API
token = mssparkutils.credentials.getToken("https://api.fabric.microsoft.com")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

base_url = "https://api.fabric.microsoft.com/v1"

# Create timestamped output folder in lakehouse Files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"Files/notebook_exports/output_{timestamp}"

print(f"Output path: {output_path}")
print(f"Workspace ID: {workspace_id}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# List all notebooks in the workspace
notebooks = []
list_url = f"{base_url}/workspaces/{workspace_id}/notebooks"

while list_url:
    response = requests.get(list_url, headers=headers)
    response.raise_for_status()
    data = response.json()
    notebooks.extend(data.get("value", []))
    list_url = data.get("continuationUri")

print(f"Found {len(notebooks)} notebook(s).")
for nb in notebooks:
    print(f"  - {nb['displayName']} ({nb['id']})")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import time

def wait_for_operation(operation_url, headers, max_retries=30):
    """Poll a long-running operation until complete."""
    for _ in range(max_retries):
        time.sleep(5)
        op_response = requests.get(operation_url, headers=headers)
        op_response.raise_for_status()
        op_body = op_response.json()
        if op_body.get("status") == "Succeeded":
            result_url = f"{operation_url}/result"
            result = requests.get(result_url, headers=headers)
            result.raise_for_status()
            return result.json()
        elif op_body.get("status") == "Failed":
            print(f"Operation failed: {json.dumps(op_body, indent=2)}")
            return None
    print("Operation timed out.")
    return None

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Export each notebook definition and save to lakehouse
exported_count = 0

for notebook in notebooks:
    notebook_name = notebook["displayName"]
    notebook_id = notebook["id"]
    print(f"Exporting: {notebook_name} ({notebook_id})...")

    def_url = f"{base_url}/workspaces/{workspace_id}/notebooks/{notebook_id}/getDefinition"

    try:
        def_response = requests.post(def_url, headers=headers)

        if def_response.status_code == 200:
            definition = def_response.json()
        elif def_response.status_code == 202:
            # Long-running operation
            operation_url = def_response.headers.get("Location")
            if not operation_url:
                op_id = def_response.headers.get("x-ms-operation-id")
                operation_url = f"{base_url}/operations/{op_id}"
            definition = wait_for_operation(operation_url, headers)
        else:
            print(f"  Unexpected status {def_response.status_code}: {def_response.text}")
            continue

        if definition and definition.get("definition", {}).get("parts"):
            for part in definition["definition"]["parts"]:
                # Decode base64 payload
                decoded_content = base64.b64decode(part["payload"]).decode("utf-8")

                # Sanitize notebook name for filename
                safe_name = re.sub(r'[\\/:*?"<>|]', '_', notebook_name)
                part_name = part["path"].rsplit(".", 1)[0]  # remove extension
                file_name = f"{safe_name}_{part_name}.txt"
                file_path = f"{output_path}/{file_name}"

                # Write to lakehouse
                mssparkutils.fs.put(file_path, decoded_content, overwrite=True)
                print(f"  Saved: {file_name}")
                exported_count += 1
        else:
            print(f"  No definition returned for {notebook_name}")

    except Exception as e:
        print(f"  Failed to export {notebook_name}: {str(e)}")

print(f"\nDone! Exported {exported_count} file(s) to: {output_path}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
