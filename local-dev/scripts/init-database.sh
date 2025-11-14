#!/bin/bash
# =============================================================================
# Database Initialization Script
# =============================================================================
# This script:
#   1. Creates the DevOpsMetrics database
#   2. Runs security setup
#   3. Creates schema (tables)
#   4. Creates views
#   5. Loads sample data (optional)
# =============================================================================

set -e

echo "Waiting for SQL Server to be ready..."
sleep 10

SA_PASSWORD=${SA_PASSWORD:-YourStrong@Passw0rd123}
SQL_SERVER="sqlserver"

# Function to execute SQL script
execute_sql() {
    local script_file=$1
    echo "Executing: $script_file"
    /opt/mssql-tools/bin/sqlcmd -S "$SQL_SERVER" -U sa -P "$SA_PASSWORD" -i "$script_file" -b
    if [ $? -eq 0 ]; then
        echo "✓ Successfully executed: $script_file"
    else
        echo "✗ Failed to execute: $script_file"
        exit 1
    fi
}

# Create database
echo "Creating DevOpsMetrics database..."
/opt/mssql-tools/bin/sqlcmd -S "$SQL_SERVER" -U sa -P "$SA_PASSWORD" -Q "
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DevOpsMetrics')
BEGIN
    CREATE DATABASE [DevOpsMetrics];
    PRINT 'Database created successfully';
END
ELSE
BEGIN
    PRINT 'Database already exists';
END
" -b

# Execute SQL scripts in order
echo ""
echo "Setting up database schema..."

# Security setup
execute_sql "/sql/01-security-setup.sql"

# Schema
execute_sql "/sql/02-create-schema.sql"

# Views
execute_sql "/sql/03-create-views.sql"

# Sample data (optional - comment out if not needed)
execute_sql "/sql/04-sample-data.sql"

echo ""
echo "=============================================="
echo "✓ Database initialization completed!"
echo "=============================================="
echo ""
echo "Connection details:"
echo "  Server: sqlserver (or localhost:1433 from host)"
echo "  Database: DevOpsMetrics"
echo "  Username: mcp_user"
echo "  Password: McpUser@Pass123"
echo ""
echo "Admin access:"
echo "  Username: sa"
echo "  Password: $SA_PASSWORD"
echo "=============================================="
