# Optional Event-Driven Components

This directory contains optional Azure Function App for automatic data ingestion.

## Overview

The Azure Function automatically inserts build and test data into the SQL Database when triggered by events from your CI/CD pipeline.

**Benefits**:
- Automatic data collection
- No manual SQL inserts needed
- Event-driven architecture
- Scales automatically

## Function App

**Trigger**: HTTP POST
**Input**: JSON payload with build and test data
**Output**: Success/failure response

### Example Usage

```bash
# Call function from CI/CD pipeline
curl -X POST https://<function-app>.azurewebsites.net/api/IngestBuildData?code=<function-key> \
  -H "Content-Type: application/json" \
  -d @example-payload.json
```

### Payload Format

See `example-payload.json` for the expected format.

## Deployment

### Option 1: Deploy via Azure CLI

```bash
# Create Function App
az functionapp create \
  --resource-group rg-mcp-server-dev \
  --name func-build-ingestion-dev \
  --storage-account <storage-account> \
  --consumption-plan-location eastus \
  --runtime node \
  --runtime-version 20 \
  --functions-version 4

# Deploy function code
cd function-app
func azure functionapp publish func-build-ingestion-dev
```

### Option 2: Deploy via Bicep

*(Bicep template available in iac/modules/function-app.bicep)*

## Configuration

Set these environment variables in Function App configuration:

```
SQL_SERVER=<sql-server>.database.windows.net
SQL_DATABASE=DevOpsMetrics
SQL_USER=build_writer
SQL_PASSWORD=<password>
```

**Note**: Create a separate SQL user with INSERT permissions for the function app.

## Integration with GitHub Actions

Add to your workflow:

```yaml
- name: Send build data to ingestion function
  run: |
    curl -X POST ${{ secrets.FUNCTION_APP_URL }} \
      -H "Content-Type: application/json" \
      -d @build-data.json
```

## Security Considerations

1. Use Function Key authentication
2. Create dedicated SQL user with INSERT-only permissions
3. Validate all inputs
4. Use Managed Identity for SQL authentication (recommended)
5. Enable Application Insights for monitoring
