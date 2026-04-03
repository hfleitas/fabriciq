# Fabric Connections via REST API

## Prerequisites

### Install Az.Accounts PowerShell Module

```powershell
Install-Module Az.Accounts -Scope CurrentUser
```

### Authenticate to Azure

Disable the subscription selector (Azure CLI v2.61.0+):

```powershell
az config set core.login_experience_v2=off
```

Login using device code flow with your tenant:

```powershell
Connect-AzAccount -TenantId 5e8d79b8-bf16-4299-a787-94895bd3493a -UseDeviceAuthentication
```

> **Note:** Use `-UseDeviceAuthentication` if the interactive browser picks the wrong account. Navigate to https://microsoft.com/devicelogin and enter the code shown in the terminal.

## Get an Access Token

```powershell
$tokenResult = Get-AzAccessToken -ResourceUrl "https://api.fabric.microsoft.com" -AsSecureString
$token = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($tokenResult.Token)
)
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
```

> **Note:** Newer versions of `Az.Accounts` return the token as a `SecureString`. The marshal conversion above extracts the plain text token needed for the `Authorization` header.

## List Connections

```powershell
Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/connections" `
    -Headers @{ Authorization = "Bearer $token" } | ConvertTo-Json -Depth 10
```

Verify in the Fabric portal:
**Fabric UI → Settings → Manage connections and gateways**
`https://app.fabric.microsoft.com/groups/<workspace-id>/gateways?experience=fabric-developer`

## Create a Sample Connection

Create a Web connection with Anonymous auth:

```powershell
$body = @'
{
  "connectivityType": "ShareableCloud",
  "displayName": "api.data.gov",
  "connectionDetails": {
    "type": "Web",
    "creationMethod": "Web",
    "parameters": [
      { "dataType": "Text", "name": "url", "value": "https://api.data.gov" }
    ]
  },
  "privacyLevel": "Public",
  "credentialDetails": {
    "singleSignOnType": "None",
    "connectionEncryption": "NotEncrypted",
    "skipTestConnection": true,
    "credentials": { "credentialType": "Anonymous" }
  }
}
'@

Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/connections" `
    -Headers $headers -Method Post -Body $body | ConvertTo-Json -Depth 10
```

After creation, verify the new connection appears in the Fabric portal under **Manage connections and gateways**.

## Change Auth Type (Credential Rotation)

Update the connection from Anonymous to Basic auth:

```powershell
$connectionId = "89c91959-4500-4586-9f34-305a49470ae6"

$body = @'
{
  "connectivityType": "ShareableCloud",
  "credentialDetails": {
    "skipTestConnection": true,
    "credentials": {
      "credentialType": "Basic",
      "username": "testuser01",
      "password": "P@ssw0rd123!"
    }
  }
}
'@

Invoke-RestMethod -Uri "https://api.fabric.microsoft.com/v1/connections/$connectionId" `
    -Headers $headers -Method Patch -Body $body | ConvertTo-Json -Depth 10
```

> **Important:** The PATCH request requires `connectivityType` as a required field (e.g. `ShareableCloud`). Set `skipTestConnection` to `true` when the endpoint won't actually validate the credentials.

After updating, verify the credential type changed in the Fabric portal:
1. Go to **Manage connections and gateways**.
2. Find the connection (e.g. `api.data.gov`).
3. Confirm the **Authentication method** now shows **Basic**.

## API Reference

| Operation | Method | Endpoint |
|---|---|---|
| List connections | `GET` | `https://api.fabric.microsoft.com/v1/connections` |
| Create connection | `POST` | `https://api.fabric.microsoft.com/v1/connections` |
| Update connection | `PATCH` | `https://api.fabric.microsoft.com/v1/connections/{connectionId}` |
| Delete connection | `DELETE` | `https://api.fabric.microsoft.com/v1/connections/{connectionId}` |

Full docs: https://learn.microsoft.com/en-us/rest/api/fabric/core/connections
