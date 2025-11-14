-- =============================================================================
-- SQL Security Setup - Azure AD Authentication (Optional)
-- =============================================================================
-- This script creates a read-only Azure AD user for the MCP server
-- using Azure Managed Identity for passwordless authentication.
--
-- Prerequisites:
--   - Azure SQL Database with Azure AD authentication enabled
--   - Managed Identity created for the MCP server container app
--   - Run this with Azure AD admin privileges
-- =============================================================================

-- Switch to your database (update database name as needed)
USE [DevOpsMetrics];
GO

-- =============================================================================
-- 1. Create User from Azure AD Managed Identity
-- =============================================================================

-- Replace 'mcp-server-identity' with your Managed Identity name
-- The identity name can be found in Azure Portal -> Container App -> Identity

DECLARE @identityName NVARCHAR(128) = 'mcp-server-identity';
DECLARE @sql NVARCHAR(MAX);

-- Check if user exists
IF EXISTS (SELECT 1 FROM sys.database_principals WHERE name = @identityName)
BEGIN
    SET @sql = 'DROP USER [' + @identityName + ']';
    EXEC sp_executesql @sql;
    PRINT 'Dropped existing Azure AD user: ' + @identityName;
END
GO

-- Create user from external provider (Azure AD)
-- Note: The identity must be created in Azure first
DECLARE @identityName NVARCHAR(128) = 'mcp-server-identity';
DECLARE @sql NVARCHAR(MAX);

SET @sql = 'CREATE USER [' + @identityName + '] FROM EXTERNAL PROVIDER';
EXEC sp_executesql @sql;

PRINT 'Created Azure AD user: ' + @identityName;
GO

-- =============================================================================
-- 2. Grant Read-Only Permissions
-- =============================================================================

DECLARE @identityName NVARCHAR(128) = 'mcp-server-identity';

-- Add to db_datareader role
EXEC sp_addrolemember 'db_datareader', @identityName;

PRINT 'Granted db_datareader role to ' + @identityName;
GO

-- Grant VIEW DEFINITION for metadata queries
DECLARE @identityName NVARCHAR(128) = 'mcp-server-identity';
DECLARE @sql NVARCHAR(MAX);

SET @sql = 'GRANT VIEW DEFINITION TO [' + @identityName + ']';
EXEC sp_executesql @sql;

PRINT 'Granted VIEW DEFINITION to ' + @identityName;
GO

-- =============================================================================
-- 3. Explicitly DENY Destructive Operations
-- =============================================================================

DECLARE @identityName NVARCHAR(128) = 'mcp-server-identity';
DECLARE @sql NVARCHAR(MAX);

SET @sql = 'DENY INSERT, UPDATE, DELETE, ALTER, CREATE, DROP TO [' + @identityName + ']';
EXEC sp_executesql @sql;

PRINT 'Denied write permissions to ' + @identityName;
GO

-- =============================================================================
-- 4. Verify Permissions
-- =============================================================================

-- Show granted permissions
SELECT
    dp.name AS UserName,
    dp.type_desc AS UserType,
    o.name AS ObjectName,
    o.type_desc AS ObjectType,
    p.permission_name,
    p.state_desc AS PermissionState
FROM sys.database_permissions p
INNER JOIN sys.database_principals dp ON p.grantee_principal_id = dp.principal_id
LEFT JOIN sys.objects o ON p.major_id = o.object_id
WHERE dp.name = 'mcp-server-identity'
ORDER BY ObjectName, permission_name;
GO

-- Show role memberships
SELECT
    dp.name AS UserName,
    r.name AS RoleName
FROM sys.database_role_members drm
INNER JOIN sys.database_principals dp ON drm.member_principal_id = dp.principal_id
INNER JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
WHERE dp.name = 'mcp-server-identity';
GO

PRINT 'Azure AD security setup completed successfully!';
PRINT 'Remember to update the connection string to use Managed Identity authentication';
GO

-- =============================================================================
-- Connection String Example for Managed Identity:
-- =============================================================================
-- Server=tcp:<server>.database.windows.net,1433;
-- Database=DevOpsMetrics;
-- Authentication=Active Directory Managed Identity;
-- Encrypt=True;
-- TrustServerCertificate=False;
-- =============================================================================
