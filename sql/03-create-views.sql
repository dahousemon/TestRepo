-- =============================================================================
-- Analytics Views - DevOps Metrics
-- =============================================================================
-- This script creates analytical views for:
--   - Test flakiness detection
--   - Daily build statistics
--   - Additional operational insights
-- =============================================================================

USE [DevOpsMetrics];
GO

-- =============================================================================
-- 1. vw_TestFlakiness
-- =============================================================================
-- Identifies flaky tests by analyzing pass/fail patterns over time
-- Flaky tests are tests that sometimes pass and sometimes fail without code changes

IF OBJECT_ID('dbo.vw_TestFlakiness', 'V') IS NOT NULL
    DROP VIEW dbo.vw_TestFlakiness;
GO

CREATE VIEW dbo.vw_TestFlakiness
AS
WITH TestStats AS (
    SELECT
        tr.TestName,
        tr.TestSuite,
        COUNT(*) AS TotalRuns,
        SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) AS PassedRuns,
        SUM(CASE WHEN tr.Status = 'Failed' THEN 1 ELSE 0 END) AS FailedRuns,
        SUM(CASE WHEN tr.Status = 'Flaky' THEN 1 ELSE 0 END) AS FlakyRuns,
        MIN(tr.StartTime) AS FirstRunDate,
        MAX(tr.StartTime) AS LastRunDate,
        AVG(CAST(tr.DurationSeconds AS FLOAT)) AS AvgDurationSeconds,
        MAX(tr.DurationSeconds) AS MaxDurationSeconds,
        MIN(tr.DurationSeconds) AS MinDurationSeconds
    FROM dbo.TestRuns tr
    WHERE tr.Status IN ('Passed', 'Failed', 'Flaky')
    GROUP BY tr.TestName, tr.TestSuite
)
SELECT
    TestName,
    TestSuite,
    TotalRuns,
    PassedRuns,
    FailedRuns,
    FlakyRuns,
    -- Calculate pass rate
    CAST(ROUND((PassedRuns * 100.0 / NULLIF(TotalRuns, 0)), 2) AS DECIMAL(5,2)) AS PassRate,
    -- Calculate flakiness score (0-100, higher = more flaky)
    CASE
        WHEN TotalRuns < 5 THEN NULL -- Not enough data
        WHEN PassedRuns = 0 OR PassedRuns = TotalRuns THEN 0 -- Consistently failing or passing
        ELSE CAST(ROUND(((FailedRuns * 100.0 / NULLIF(TotalRuns, 0)) * (1.0 - ABS(PassedRuns - FailedRuns) / CAST(TotalRuns AS FLOAT))), 2) AS DECIMAL(5,2))
    END AS FlakinessScore,
    FirstRunDate,
    LastRunDate,
    DATEDIFF(DAY, FirstRunDate, LastRunDate) AS DaysSinceFirstRun,
    ROUND(AvgDurationSeconds, 2) AS AvgDurationSeconds,
    MaxDurationSeconds,
    MinDurationSeconds,
    -- Categorize flakiness
    CASE
        WHEN TotalRuns < 5 THEN 'Insufficient Data'
        WHEN PassedRuns = 0 THEN 'Always Failing'
        WHEN PassedRuns = TotalRuns THEN 'Stable'
        WHEN PassedRuns * 100.0 / TotalRuns >= 80 AND FailedRuns > 0 THEN 'Occasionally Flaky'
        WHEN PassedRuns * 100.0 / TotalRuns >= 50 THEN 'Moderately Flaky'
        ELSE 'Highly Flaky'
    END AS FlakinessCategory
FROM TestStats;
GO

PRINT 'Created view: vw_TestFlakiness';
GO

-- =============================================================================
-- 2. vw_BuildStatsDaily
-- =============================================================================
-- Daily aggregated build statistics for trend analysis

IF OBJECT_ID('dbo.vw_BuildStatsDaily', 'V') IS NOT NULL
    DROP VIEW dbo.vw_BuildStatsDaily;
GO

CREATE VIEW dbo.vw_BuildStatsDaily
AS
SELECT
    CAST(br.StartTime AS DATE) AS BuildDate,
    br.Branch,
    COUNT(*) AS TotalBuilds,
    SUM(CASE WHEN br.Status = 'Success' THEN 1 ELSE 0 END) AS SuccessfulBuilds,
    SUM(CASE WHEN br.Status = 'Failed' THEN 1 ELSE 0 END) AS FailedBuilds,
    SUM(CASE WHEN br.Status = 'Cancelled' THEN 1 ELSE 0 END) AS CancelledBuilds,
    -- Success rate
    CAST(ROUND((SUM(CASE WHEN br.Status = 'Success' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)), 2) AS DECIMAL(5,2)) AS SuccessRate,
    -- Duration statistics
    AVG(CAST(br.DurationSeconds AS FLOAT)) AS AvgDurationSeconds,
    MAX(br.DurationSeconds) AS MaxDurationSeconds,
    MIN(br.DurationSeconds) AS MinDurationSeconds,
    -- Total test runs
    COUNT(DISTINCT tr.TestRunId) AS TotalTestRuns,
    SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) AS PassedTests,
    SUM(CASE WHEN tr.Status = 'Failed' THEN 1 ELSE 0 END) AS FailedTests,
    -- Test pass rate
    CAST(ROUND((SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(DISTINCT tr.TestRunId), 0)), 2) AS DECIMAL(5,2)) AS TestPassRate
FROM dbo.BuildRuns br
LEFT JOIN dbo.TestRuns tr ON br.BuildRunId = tr.BuildRunId
WHERE br.Status IN ('Success', 'Failed', 'Cancelled')
    AND br.EndTime IS NOT NULL
GROUP BY CAST(br.StartTime AS DATE), br.Branch;
GO

PRINT 'Created view: vw_BuildStatsDaily';
GO

-- =============================================================================
-- 3. vw_RecentBuildSummary
-- =============================================================================
-- Summary of recent builds with test metrics (last 30 days)

IF OBJECT_ID('dbo.vw_RecentBuildSummary', 'V') IS NOT NULL
    DROP VIEW dbo.vw_RecentBuildSummary;
GO

CREATE VIEW dbo.vw_RecentBuildSummary
AS
SELECT
    br.BuildRunId,
    br.Branch,
    br.StartTime,
    br.EndTime,
    br.DurationSeconds,
    br.Status AS BuildStatus,
    br.TriggeredBy,
    br.CommitSha,
    br.BuildNumber,
    -- Test metrics
    COUNT(DISTINCT tr.TestRunId) AS TotalTests,
    SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) AS PassedTests,
    SUM(CASE WHEN tr.Status = 'Failed' THEN 1 ELSE 0 END) AS FailedTests,
    SUM(CASE WHEN tr.Status = 'Skipped' THEN 1 ELSE 0 END) AS SkippedTests,
    -- Failure details
    COUNT(DISTINCT tf.TestFailureId) AS TotalFailures,
    -- Test pass rate
    CASE
        WHEN COUNT(DISTINCT tr.TestRunId) > 0
        THEN CAST(ROUND((SUM(CASE WHEN tr.Status = 'Passed' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT tr.TestRunId)), 2) AS DECIMAL(5,2))
        ELSE NULL
    END AS TestPassRate
FROM dbo.BuildRuns br
LEFT JOIN dbo.TestRuns tr ON br.BuildRunId = tr.BuildRunId
LEFT JOIN dbo.TestFailures tf ON tr.TestRunId = tf.TestRunId
WHERE br.StartTime >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY
    br.BuildRunId,
    br.Branch,
    br.StartTime,
    br.EndTime,
    br.DurationSeconds,
    br.Status,
    br.TriggeredBy,
    br.CommitSha,
    br.BuildNumber;
GO

PRINT 'Created view: vw_RecentBuildSummary';
GO

-- =============================================================================
-- 4. vw_TopFailingTests
-- =============================================================================
-- Identifies the most frequently failing tests

IF OBJECT_ID('dbo.vw_TopFailingTests', 'V') IS NOT NULL
    DROP VIEW dbo.vw_TopFailingTests;
GO

CREATE VIEW dbo.vw_TopFailingTests
AS
SELECT TOP 100
    tr.TestName,
    tr.TestSuite,
    COUNT(*) AS FailureCount,
    COUNT(DISTINCT br.Branch) AS AffectedBranches,
    MIN(tr.StartTime) AS FirstFailure,
    MAX(tr.StartTime) AS LastFailure,
    -- Most common failure category
    (
        SELECT TOP 1 tf2.FailureCategory
        FROM dbo.TestFailures tf2
        INNER JOIN dbo.TestRuns tr2 ON tf2.TestRunId = tr2.TestRunId
        WHERE tr2.TestName = tr.TestName
            AND tf2.FailureCategory IS NOT NULL
        GROUP BY tf2.FailureCategory
        ORDER BY COUNT(*) DESC
    ) AS MostCommonFailureCategory,
    AVG(CAST(tr.DurationSeconds AS FLOAT)) AS AvgDurationSeconds
FROM dbo.TestRuns tr
INNER JOIN dbo.TestFailures tf ON tr.TestRunId = tf.TestRunId
INNER JOIN dbo.BuildRuns br ON tr.BuildRunId = br.BuildRunId
WHERE tr.Status = 'Failed'
    AND tr.StartTime >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY tr.TestName, tr.TestSuite
ORDER BY FailureCount DESC;
GO

PRINT 'Created view: vw_TopFailingTests';
GO

-- =============================================================================
-- Summary
-- =============================================================================

PRINT '';
PRINT '=============================================================================';
PRINT 'Analytics views created successfully!';
PRINT '=============================================================================';
PRINT '';
PRINT 'Created views:';
PRINT '  - vw_TestFlakiness: Identifies flaky tests with scoring';
PRINT '  - vw_BuildStatsDaily: Daily build metrics and trends';
PRINT '  - vw_RecentBuildSummary: Summary of recent builds (30 days)';
PRINT '  - vw_TopFailingTests: Most frequently failing tests';
PRINT '';
PRINT 'Example queries:';
PRINT '  SELECT * FROM vw_TestFlakiness WHERE FlakinessScore > 50 ORDER BY FlakinessScore DESC;';
PRINT '  SELECT * FROM vw_BuildStatsDaily WHERE BuildDate >= DATEADD(DAY, -7, GETUTCDATE());';
PRINT '  SELECT * FROM vw_TopFailingTests;';
PRINT '=============================================================================';
GO
