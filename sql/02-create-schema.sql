-- =============================================================================
-- Database Schema - DevOps Metrics Tables
-- =============================================================================
-- This script creates the core tables for tracking build and test metrics:
--   - BuildRuns: CI/CD build execution data
--   - TestRuns: Individual test execution records
--   - TestFailures: Detailed test failure information
--
-- Features:
--   - Primary and foreign key constraints
--   - Appropriate indexes for query performance
--   - Check constraints for data validation
--   - Default values where applicable
-- =============================================================================

USE [DevOpsMetrics];
GO

-- =============================================================================
-- 1. BuildRuns Table
-- =============================================================================
-- Tracks CI/CD build executions across all branches

IF OBJECT_ID('dbo.BuildRuns', 'U') IS NOT NULL
    DROP TABLE dbo.BuildRuns;
GO

CREATE TABLE dbo.BuildRuns (
    BuildRunId INT IDENTITY(1,1) NOT NULL,
    Branch NVARCHAR(255) NOT NULL,
    StartTime DATETIME2(3) NOT NULL,
    EndTime DATETIME2(3) NULL,
    DurationSeconds AS DATEDIFF(SECOND, StartTime, EndTime) PERSISTED,
    Status NVARCHAR(50) NOT NULL,
    TriggeredBy NVARCHAR(255) NOT NULL,
    CommitSha NVARCHAR(40) NULL,
    BuildNumber NVARCHAR(50) NULL,
    CreatedAt DATETIME2(3) NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_BuildRuns PRIMARY KEY CLUSTERED (BuildRunId),
    CONSTRAINT CK_BuildRuns_Status CHECK (Status IN ('Pending', 'Running', 'Success', 'Failed', 'Cancelled')),
    CONSTRAINT CK_BuildRuns_EndTime CHECK (EndTime IS NULL OR EndTime >= StartTime)
);
GO

-- Indexes for common queries
CREATE NONCLUSTERED INDEX IX_BuildRuns_Branch_StartTime
    ON dbo.BuildRuns(Branch, StartTime DESC)
    INCLUDE (Status, DurationSeconds);
GO

CREATE NONCLUSTERED INDEX IX_BuildRuns_Status_StartTime
    ON dbo.BuildRuns(Status, StartTime DESC);
GO

CREATE NONCLUSTERED INDEX IX_BuildRuns_StartTime
    ON dbo.BuildRuns(StartTime DESC);
GO

PRINT 'Created table: BuildRuns';
GO

-- =============================================================================
-- 2. TestRuns Table
-- =============================================================================
-- Tracks individual test executions within each build

IF OBJECT_ID('dbo.TestRuns', 'U') IS NOT NULL
    DROP TABLE dbo.TestRuns;
GO

CREATE TABLE dbo.TestRuns (
    TestRunId INT IDENTITY(1,1) NOT NULL,
    BuildRunId INT NOT NULL,
    TestName NVARCHAR(500) NOT NULL,
    TestSuite NVARCHAR(255) NULL,
    StartTime DATETIME2(3) NOT NULL,
    EndTime DATETIME2(3) NULL,
    Status NVARCHAR(50) NOT NULL,
    DurationSeconds AS DATEDIFF(SECOND, StartTime, EndTime) PERSISTED,
    CreatedAt DATETIME2(3) NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_TestRuns PRIMARY KEY CLUSTERED (TestRunId),
    CONSTRAINT FK_TestRuns_BuildRuns FOREIGN KEY (BuildRunId)
        REFERENCES dbo.BuildRuns(BuildRunId) ON DELETE CASCADE,
    CONSTRAINT CK_TestRuns_Status CHECK (Status IN ('Pending', 'Running', 'Passed', 'Failed', 'Skipped', 'Flaky')),
    CONSTRAINT CK_TestRuns_EndTime CHECK (EndTime IS NULL OR EndTime >= StartTime)
);
GO

-- Indexes for common queries
CREATE NONCLUSTERED INDEX IX_TestRuns_BuildRunId
    ON dbo.TestRuns(BuildRunId)
    INCLUDE (TestName, Status, DurationSeconds);
GO

CREATE NONCLUSTERED INDEX IX_TestRuns_TestName_StartTime
    ON dbo.TestRuns(TestName, StartTime DESC)
    INCLUDE (Status, DurationSeconds);
GO

CREATE NONCLUSTERED INDEX IX_TestRuns_Status_StartTime
    ON dbo.TestRuns(Status, StartTime DESC);
GO

PRINT 'Created table: TestRuns';
GO

-- =============================================================================
-- 3. TestFailures Table
-- =============================================================================
-- Captures detailed information about test failures for debugging

IF OBJECT_ID('dbo.TestFailures', 'U') IS NOT NULL
    DROP TABLE dbo.TestFailures;
GO

CREATE TABLE dbo.TestFailures (
    TestFailureId INT IDENTITY(1,1) NOT NULL,
    TestRunId INT NOT NULL,
    FailureReason NVARCHAR(MAX) NULL,
    ErrorMessage NVARCHAR(MAX) NULL,
    StackTrace NVARCHAR(MAX) NULL,
    FailureCategory NVARCHAR(100) NULL,
    LoggedAt DATETIME2(3) NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_TestFailures PRIMARY KEY CLUSTERED (TestFailureId),
    CONSTRAINT FK_TestFailures_TestRuns FOREIGN KEY (TestRunId)
        REFERENCES dbo.TestRuns(TestRunId) ON DELETE CASCADE
);
GO

-- Indexes
CREATE NONCLUSTERED INDEX IX_TestFailures_TestRunId
    ON dbo.TestFailures(TestRunId);
GO

CREATE NONCLUSTERED INDEX IX_TestFailures_LoggedAt
    ON dbo.TestFailures(LoggedAt DESC);
GO

CREATE NONCLUSTERED INDEX IX_TestFailures_Category
    ON dbo.TestFailures(FailureCategory)
    WHERE FailureCategory IS NOT NULL;
GO

PRINT 'Created table: TestFailures';
GO

-- =============================================================================
-- 4. Summary Statistics
-- =============================================================================

PRINT '';
PRINT '=============================================================================';
PRINT 'Schema creation completed successfully!';
PRINT '=============================================================================';
PRINT '';
PRINT 'Created tables:';
PRINT '  - BuildRuns (tracks CI/CD builds)';
PRINT '  - TestRuns (tracks test executions)';
PRINT '  - TestFailures (captures failure details)';
PRINT '';
PRINT 'Next steps:';
PRINT '  1. Run 03-create-views.sql to create analytics views';
PRINT '  2. Run 04-sample-data.sql to populate sample data';
PRINT '=============================================================================';
GO
