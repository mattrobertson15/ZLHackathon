import type { AnalyticsOverview, AnalyticsTrends, SafetySummary } from "./types";

function formatDate(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleDateString();
}

function formatDateTime(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function safeFilePart(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

export function downloadMarkdownReport(markdown: string, fileName: string): void {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function buildSummaryReport(summary: SafetySummary): {
  fileName: string;
  markdown: string;
} {
  const periodLabel = titleCase(summary.period);
  const dateRange = `${formatDate(summary.startDate)} - ${formatDate(summary.endDate)}`;
  const createdAt = formatDateTime(summary.createdAt);
  const fileName = `safety-sentinel-${safeFilePart(summary.period)}-summary-${safeFilePart(
    summary.startDate
  )}-to-${safeFilePart(summary.endDate)}.md`;

  return {
    fileName,
    markdown: `# Safety Sentinel ${periodLabel} Report

**Reporting period:** ${dateRange}
**Generated:** ${createdAt}
**Report ID:** ${summary.id}

## Executive Summary

${summary.executiveSummary}

## Top Violations

${summary.topViolations}

## Trend Analysis

${summary.trendAnalysis}

## Recommended Actions

${summary.recommendedActions}

---

Prepared by Safety Sentinel. Observations are anonymous safety events for supervisor review and operations intelligence.
`,
  };
}

export function buildDashboardReport(
  overview: AnalyticsOverview,
  trends: AnalyticsTrends | null
): {
  fileName: string;
  markdown: string;
} {
  const generatedAt = new Date();

  const repeated = overview.repeatedViolations || [];
  const repeatedViolationLabels: Record<string, string> = {
    no_helmet: "Missing helmet",
    no_vest: "Missing vest",
  };
  const repeatedRows =
    repeated.length > 0
      ? repeated
          .map(
            (item) =>
              `| ${item.zoneLabel} | ${
                repeatedViolationLabels[item.violationType] || item.violationType
              } | ${item.count} | ${item.distinctUploadCount} | ${item.severity} | ${formatDate(
                item.lastSeenAt
              )} |`
          )
          .join("\n")
      : "| No repeated zone issues this week | - | - | - | - | - |";

  const trendRows =
    trends && trends.points.length > 0
      ? trends.points
          .map(
            (point) =>
              `| ${point.date} | ${point.compliancePercentage}% | ${point.totalViolations} | ${point.noHelmet} | ${point.noVest} |`
          )
          .join("\n")
      : "| No trend data available | - | - | - | - |";

  return {
    fileName: `safety-sentinel-dashboard-${safeFilePart(
      generatedAt.toISOString().split("T")[0]
    )}.md`,
    markdown: `# Safety Sentinel Dashboard Report

**Dashboard period:** ${titleCase(overview.period)}
**Generated:** ${formatDateTime(generatedAt)}

## Compliance Snapshot

| Metric | Value |
| --- | ---: |
| Compliance percentage | ${overview.compliancePercentage}% |
| Total observations | ${overview.totalObservations} |
| Positive observations | ${overview.positiveObservations} |
| Safety violations | ${overview.totalViolations} |
| Pending reviews | ${overview.openEvents} |

## Violation Breakdown

| Violation type | Count |
| --- | ---: |
| Missing helmet | ${overview.violationBreakdown.no_helmet} |
| Missing vest | ${overview.violationBreakdown.no_vest} |

## Severity Breakdown

| Severity | Count |
| --- | ---: |
| High | ${overview.severityBreakdown.high} |
| Medium | ${overview.severityBreakdown.medium} |
| Low | ${overview.severityBreakdown.low} |

## Repeated Zone Issues

Zones with the same violation recurring within the past 7 days (threshold: 3).
Employee identity is intentionally out of scope.

| Zone | Violation | Count | Uploads | Severity | Last seen |
| --- | --- | ---: | ---: | --- | --- |
${repeatedRows}

## Compliance Trends

| Date | Compliance | Violations | Missing helmet | Missing vest |
| --- | ---: | ---: | ---: | ---: |
${trendRows}

---

Prepared by Safety Sentinel. Use this export as a manager-ready operational snapshot; confirm low-confidence events before taking action.
`,
  };
}
