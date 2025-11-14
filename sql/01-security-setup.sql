-- =============================================================================
-- SQL Security Setup - Read-Only User Configuration
-- =============================================================================
-- This script creates a read-only SQL login and user for the MCP server
-- to enforce least-privilege access to the database.
--
-- Prerequisites:
--   - Run this with sysadmin or securityadmin privileges
--   - Update the password to a strong value (stored in Azure Key Vault)
-- =============================================================================

USE [master];
GO

-- =============================================================================
-- 1. Create SQL Login (SQL Authentication)
-- =============================================================================

-- Check if login exists, drop if needed (for dev/test environments)
IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'mcp_user')
BEGIN
    DROP LOGIN [mcp_user];
    PRINT 'Dropped existing login: mcp_user';
END
GO

-- Create login with strong password
-- IMPORTANT: Replace this password and store it securely in Azure Key Vault
CREATE LOGIN [mcp_user]
WITH PASSWORD = 'REPLACE_WITH_STRONG_PASSWORD_FROM_KEYVAULT';
GO

PRINT 'Created SQL login: mcp_user';
GO

-- =============================================================================
-- 2. Create Database User and Grant Permissions
-- =============================================================================

-- Switch to your database (update database name as needed)
USE [DevOpsMetrics];
GO

-- Create user from login
IF EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'mcp_user')
BEGIN
    DROP USER [mcp_user];
    PRINT 'Dropped existing user: mcp_user';
END
GO

CREATE USER [mcp_user] FOR LOGIN [mcp_user];
GO

PRINT 'Created database user: mcp_user';
GO

-- =============================================================================
-- 3. Grant Read-Only Permissions
-- =============================================================================

-- Add to db_datareader role (SELECT on all tables/views)
ALTER ROLE db_datareader ADD MEMBER [mcp_user];
GO

PRINT 'Granted db_datareader role to mcp_user';
GO

-- Grant EXECUTE on INFORMATION_SCHEMA views (for metadata queries)
GRANT VIEW DEFINITION TO [mcp_user];
GO

PRINT 'Granted VIEW DEFINITION to mcp_user';
GO

-- =============================================================================
-- 4. Explicitly DENY Destructive Operations
-- =============================================================================

-- Deny all write operations to ensure read-only access
DENY INSERT, UPDATE, DELETE, ALTER, CREATE, DROP TO [mcp_user];
GO

PRINT 'Denied write permissions to mcp_user';
GO

-- =============================================================================
-- 5. Verify Permissions
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
WHERE dp.name = 'mcp_user'
ORDER BY ObjectName, permission_name;
GO

-- Show role memberships
SELECT
    dp.name AS UserName,
    r.name AS RoleName
FROM sys.database_role_members drm
INNER JOIN sys.database_principals dp ON drm.member_principal_id = dp.principal_id
INNER JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
WHERE dp.name = 'mcp_user';
GO

PRINT 'Security setup completed successfully!';
GO
