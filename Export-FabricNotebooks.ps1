<#
.SYNOPSIS
    Exports all Fabric Notebook item definitions from a workspace and saves them as .txt files.

.PARAMETER WorkspaceId
    The Fabric workspace ID to export notebooks from.

.EXAMPLE
    .\Export-FabricNotebooks.ps1 -WorkspaceId "564dff7b-1a14-4fcc-ba85-b3d901f12934"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceId
)

$ErrorActionPreference = "Stop"

# Timestamp for the output folder
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFolder = Join-Path $PSScriptRoot "output_$timestamp"
New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null

Write-Host "Output folder: $outputFolder" -ForegroundColor Cyan

# Get access token via Azure CLI
Write-Host "Acquiring access token..." -ForegroundColor Yellow
$tokenResponse = az account get-access-token --resource "https://api.fabric.microsoft.com" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get access token. Make sure you are logged in with 'az login'. Error: $tokenResponse"
    exit 1
}
$token = ($tokenResponse | ConvertFrom-Json).accessToken
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

$baseUrl = "https://api.fabric.microsoft.com/v1"

# List all notebooks in the workspace
Write-Host "Listing notebooks in workspace $WorkspaceId..." -ForegroundColor Yellow
$notebooks = @()
$listUrl = "$baseUrl/workspaces/$WorkspaceId/notebooks"

do {
    $response = Invoke-RestMethod -Uri $listUrl -Headers $headers -Method Get
    $notebooks += $response.value
    $listUrl = $response.continuationUri
} while ($listUrl)

Write-Host "Found $($notebooks.Count) notebook(s)." -ForegroundColor Green

# Function to poll a long-running operation until complete
function Wait-FabricOperation {
    param(
        [string]$OperationUrl,
        [hashtable]$Headers
    )
    $maxRetries = 30
    $retryCount = 0
    while ($retryCount -lt $maxRetries) {
        Start-Sleep -Seconds 5
        $opResponse = Invoke-WebRequest -Uri $OperationUrl -Headers $Headers -Method Get
        $opBody = $opResponse.Content | ConvertFrom-Json
        if ($opBody.status -eq "Succeeded") {
            # Get the result from the operation
            $resultUrl = "$OperationUrl/result"
            $result = Invoke-RestMethod -Uri $resultUrl -Headers $Headers -Method Get
            return $result
        }
        elseif ($opBody.status -eq "Failed") {
            Write-Error "Operation failed: $($opBody | ConvertTo-Json -Depth 5)"
            return $null
        }
        $retryCount++
    }
    Write-Warning "Operation timed out after $maxRetries retries."
    return $null
}

# Get definition for each notebook and save to file
foreach ($notebook in $notebooks) {
    $notebookName = $notebook.displayName
    $notebookId = $notebook.id
    Write-Host "  Exporting: $notebookName ($notebookId)..." -ForegroundColor White

    $defUrl = "$baseUrl/workspaces/$WorkspaceId/notebooks/$notebookId/getDefinition"

    try {
        $defResponse = Invoke-WebRequest -Uri $defUrl -Headers $headers -Method Post -UseBasicParsing

        if ($defResponse.StatusCode -eq 200) {
            $definition = $defResponse.Content | ConvertFrom-Json
        }
        elseif ($defResponse.StatusCode -eq 202) {
            # Long-running operation - poll for result
            $operationUrl = $defResponse.Headers["Location"]
            if (-not $operationUrl) {
                $operationUrl = "$baseUrl/operations/$($defResponse.Headers['x-ms-operation-id'])"
            }
            $definition = Wait-FabricOperation -OperationUrl $operationUrl -Headers $headers
        }

        if ($definition -and $definition.definition -and $definition.definition.parts) {
            foreach ($part in $definition.definition.parts) {
                # Decode base64 payload
                $decodedContent = [System.Text.Encoding]::UTF8.GetString(
                    [System.Convert]::FromBase64String($part.payload)
                )

                # Sanitize notebook name for filename
                $safeName = $notebookName -replace '[\\/:*?"<>|]', '_'
                $partName = [System.IO.Path]::GetFileNameWithoutExtension($part.path)
                $fileName = "${safeName}_${partName}.txt"
                $filePath = Join-Path $outputFolder $fileName

                Set-Content -Path $filePath -Value $decodedContent -Encoding UTF8
                Write-Host "    Saved: $fileName" -ForegroundColor DarkGray
            }
        }
        else {
            Write-Warning "    No definition returned for $notebookName"
        }
    }
    catch {
        Write-Warning "    Failed to export $notebookName : $($_.Exception.Message)"
    }
}

Write-Host "`nDone! Exported notebooks to: $outputFolder" -ForegroundColor Green
