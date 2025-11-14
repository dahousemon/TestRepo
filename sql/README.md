# SQL Database Scripts

This directory contains SQL scripts for setting up and managing the DevOps Metrics database.

## Scripts Overview

| Script | Purpose | Run Order |
|--------|---------|-----------|
| `01-security-setup.sql` | Creates read-only SQL login and user | 1 |
| `01-security-setup-aad.sql` | Creates read-only Azure AD user (optional) | 1 (alternative) |
| `02-create-schema.sql` | Creates tables (BuildRuns, TestRuns, TestFailures) | 2 |
| `03-create-views.sql` | Creates analytical views | 3 |
| `04-sample-data.sql` | Inserts sample data for testing | 4 (optional) |

## Quick Start

### 1. Create Database

```sql
CREATE DATABASE [DevOpsMetrics];
GO
```

### 2. Run Security Setup

Choose one authentication method:

**Option A: SQL Authentication**
```bash
sqlcmd -S <server>.database.windows.net -U <admin> -P <password> -i 01-security-setup.sql
```

**Option B: Azure AD Authentication**
```bash
sqlcmd -S <server>.database.windows.net -G -i 01-security-setup-aad.sql
```

### 3. Create Schema and Views

```bash
sqlcmd -S <server>.database.windows.net -U <admin> -P <password> -i 02-create-schema.sql
sqlcmd -S <server>.database.windows.net -U <admin> -P <password> -i 03-create-views.sql
```

### 4. (Optional) Load Sample Data

```bash
sqlcmd -S <server>.database.windows.net -U <admin> -P <password> -i 04-sample-data.sql
```

## Database Schema

### BuildRuns
Tracks CI/CD build executions.

**Columns:**
- `BuildRunId` (PK): Unique identifier
- `Branch`: Git branch name
- `StartTime`: Build start timestamp
- `EndTime`: Build end timestamp
- `DurationSeconds`: Calculated duration
- `Status`: Build status (Pending, Running, Success, Failed, Cancelled)
- `TriggeredBy`: User or system that triggered the build
- `CommitSha`: Git commit SHA
- `BuildNumber`: Build identifier

### TestRuns
Tracks individual test executions within builds.

**Columns:**
- `TestRunId` (PK): Unique identifier
- `BuildRunId` (FK): Reference to BuildRuns
- `TestName`: Name of the test
- `TestSuite`: Test suite/category
- `StartTime`: Test start timestamp
- `EndTime`: Test end timestamp
- `Status`: Test status (Pending, Running, Passed, Failed, Skipped, Flaky)
- `DurationSeconds`: Calculated duration

### TestFailures
Captures detailed failure information.

**Columns:**
- `TestFailureId` (PK): Unique identifier
- `TestRunId` (FK): Reference to TestRuns
- `FailureReason`: Short description
- `ErrorMessage`: Full error message
- `StackTrace`: Stack trace
- `FailureCategory`: Category (Timeout, Infrastructure, Logic Error, etc.)
- `LoggedAt`: Timestamp

## Analytical Views

### vw_TestFlakiness
Identifies flaky tests with scoring metrics.

**Key Columns:**
- `FlakinessScore`: 0-100 score (higher = more flaky)
- `FlakinessCategory`: Classification
- `PassRate`: Percentage of successful runs

### vw_BuildStatsDaily
Daily aggregated build statistics.

**Key Columns:**
- `BuildDate`: Date of builds
- `SuccessRate`: Percentage of successful builds
- `TestPassRate`: Percentage of passing tests

### vw_RecentBuildSummary
Recent builds (30 days) with test metrics.

### vw_TopFailingTests
Most frequently failing tests (last 30 days).

## Example Queries

### Find flaky tests
```sql
SELECT *
FROM vw_TestFlakiness
WHERE FlakinessScore > 50
ORDER BY FlakinessScore DESC;
```

### Build trends (last 7 days)
```sql
SELECT *
FROM vw_BuildStatsDaily
WHERE BuildDate >= DATEADD(DAY, -7, GETUTCDATE())
ORDER BY BuildDate DESC;
```

### Recent build failures
```sql
SELECT
    br.BuildRunId,
    br.Branch,
    br.StartTime,
    COUNT(DISTINCT tf.TestFailureId) AS FailureCount
FROM BuildRuns br
INNER JOIN TestRuns tr ON br.BuildRunId = tr.BuildRunId
INNER JOIN TestFailures tf ON tr.TestRunId = tf.TestRunId
WHERE br.Status = 'Failed'
    AND br.StartTime >= DATEADD(DAY, -7, GETUTCDATE())
GROUP BY br.BuildRunId, br.Branch, br.StartTime
ORDER BY br.StartTime DESC;
```

## Security Notes

- The `mcp_user` login has **read-only** access
- All write operations (INSERT, UPDATE, DELETE) are explicitly denied
- Use Azure Key Vault to store credentials
- For production, prefer Azure AD Managed Identity authentication

## Maintenance

### Backup
```sql
-- Automated backups are configured in Azure SQL
-- Manual backup:
BACKUP DATABASE [DevOpsMetrics]
TO URL = 'https://<storage>.blob.core.windows.net/backups/DevOpsMetrics.bak';
```

### Index Maintenance
```sql
-- Rebuild fragmented indexes
ALTER INDEX ALL ON dbo.BuildRuns REBUILD;
ALTER INDEX ALL ON dbo.TestRuns REBUILD;
ALTER INDEX ALL ON dbo.TestFailures REBUILD;
```

### Statistics Update
```sql
UPDATE STATISTICS dbo.BuildRuns WITH FULLSCAN;
UPDATE STATISTICS dbo.TestRuns WITH FULLSCAN;
UPDATE STATISTICS dbo.TestFailures WITH FULLSCAN;
```
