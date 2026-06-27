// API Response Types based on API.md

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Detection {
  id: string;
  uploadId: string;
  frameTimestamp: number | null;
  label: string;
  confidence: number;
  boundingBox: BoundingBox;
  source: string;
  createdAt: string;
}

export interface Upload {
  id: string;
  fileName: string;
  fileType: "image" | "video";
  fileUrl: string;
  locationLabel?: string | null;
  notes?: string | null;
  uploadedAt: string;
  status: "uploaded" | "processing" | "processed" | "failed";
}

export type EventType = "positive_observation" | "ppe_violation" | "uncertain_review";
export type ViolationType = "no_helmet" | "no_vest";
export type Severity = "low" | "medium" | "high";
export type EventStatus = "open" | "reviewed" | "dismissed" | "resolved";

export interface SafetyEvent {
  id: string;
  uploadId: string;
  eventType: EventType;
  violationType?: ViolationType;
  severity: Severity;
  confidence: number;
  status: EventStatus;
  suggestedAction: string;
  createdAt: string;
}

export type AlertType = "supervisor_review" | "coaching_reminder" | "manual_review";
export type AlertStatus = "draft" | "queued" | "sent_mock" | "dismissed";

export interface AlertRecord {
  id: string;
  safetyEventId: string;
  alertType: AlertType;
  title: string;
  message: string;
  status: AlertStatus;
  createdAt: string;
}

export interface AnalyticsOverview {
  period: string;
  compliancePercentage: number;
  totalObservations: number;
  totalViolations: number;
  positiveObservations: number;
  openEvents: number;
  severityBreakdown: {
    low: number;
    medium: number;
    high: number;
  };
  violationBreakdown: {
    no_helmet: number;
    no_vest: number;
  };
}

export interface TrendPoint {
  date: string;
  compliancePercentage: number;
  totalViolations: number;
  noHelmet: number;
  noVest: number;
}

export interface AnalyticsTrends {
  period: string;
  points: TrendPoint[];
}

export interface SafetySummary {
  id: string;
  period: string;
  startDate: string;
  endDate: string;
  executiveSummary: string;
  topViolations: string;
  trendAnalysis: string;
  recommendedActions: string;
  createdAt: string;
}

export interface AnalyzeResponse {
  uploadId: string;
  status: string;
  detections: Detection[];
  events: SafetyEvent[];
  alerts: AlertRecord[];
}

export interface DemoScenarioResponse {
  status: string;
  scenario: string;
  message: string;
  uploads: Upload[];
  counts: {
    uploads: number;
    detections: number;
    events: number;
    alerts: number;
  };
}
