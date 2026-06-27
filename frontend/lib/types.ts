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
  frameUrl: string | null;
  source: string;
  createdAt: string;
}

export type ModelProvider = "auto" | "roboflow" | "qwen_vision" | "manual_mock" | "compare";

export interface ComparisonDetection {
  uploadId: string;
  frameTimestamp: number | null;
  label: string;
  confidence: number;
  boundingBox: BoundingBox | null;
  source: string;
}

export interface ModelComparisonProviderResult {
  provider: Exclude<ModelProvider, "auto" | "manual_mock" | "compare">;
  source: string;
  available: boolean;
  error: string | null;
  detections: ComparisonDetection[];
}

export interface ModelComparison {
  roboflow: ModelComparisonProviderResult;
  qwen: ModelComparisonProviderResult;
  agreement: {
    matchingLabels: string[];
    roboflowOnly: string[];
    qwenOnly: string[];
    conflicts: string[];
    frames: Array<{
      frameTimestamp: number | null;
      matchingLabels: string[];
      roboflowOnly: string[];
      qwenOnly: string[];
    }>;
  };
}

export interface Upload {
  id: string;
  fileName: string;
  fileType: "image" | "video";
  fileUrl: string;
  locationLabel?: string | null;
  zoneId?: string | null;
  cameraId?: string | null;
  zoneDisplayName?: string | null;
  notes?: string | null;
  sourceType?: "upload" | "camera";
  uploadedAt: string;
  status: "uploaded" | "processing" | "processed" | "failed";
}

export interface Zone {
  id: string;
  displayName: string;
  requiredPpe: string[];
  severityOverrides: Record<string, string>;
  createdAt: string;
}

// Connectivity of a camera's live RTSP feed (only meaningful when monitored).
export type CameraStreamStatus = "offline" | "live" | "error";

// Unified Camera: a zone-assigned location record that can also be a live RTSP
// feed. Registry fields (displayName/zoneId/status) come from the location
// schema; the rtsp*/monitoring/* fields drive continuous monitoring.
export interface Camera {
  id: string;
  displayName: string;
  zoneId?: string | null;
  status: "active" | "inactive";
  createdAt: string;
  // Live RTSP feed (optional — null/offline for location-only cameras)
  rtspUrl?: string | null;
  streamStatus: CameraStreamStatus;
  monitoring: boolean;
  captureIntervalSeconds: number;
  lastCaptureAt?: string | null;
  lastError?: string | null;
  recentEventCount: number;
}

export interface CameraDetail {
  camera: Camera;
  captures: Upload[];
  events: SafetyEvent[];
}

export type EventType = "positive_observation" | "ppe_violation" | "uncertain_review";
export type ViolationType = "no_helmet" | "no_vest";
export type Severity = "low" | "medium" | "high";
export type EventStatus = "open" | "reviewed" | "dismissed" | "resolved";

export interface SafetyEvent {
  id: string;
  uploadId: string;
  upload?: Upload;
  eventType: EventType;
  violationType?: ViolationType;
  severity: Severity;
  confidence: number;
  status: EventStatus;
  statusUpdatedAt?: string | null;
  reviewNote?: string | null;
  suggestedAction: string;
  createdAt: string;
}

export type AlertType =
  | "supervisor_review"
  | "coaching_reminder"
  | "manual_review"
  | "repeated_violation";
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

export interface RepeatedViolation {
  zoneLabel: string;
  violationType: ViolationType;
  count: number;
  distinctUploadCount: number;
  severity: Severity;
  latestEventId: string;
  firstSeenAt: string;
  lastSeenAt: string;
  message: string;
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
  statusBreakdown: {
    open: number;
    reviewed: number;
    dismissed: number;
    resolved: number;
  };
  repeatedViolations: RepeatedViolation[];
}

export interface UploadResults {
  upload: Upload;
  detections: Detection[];
  events: SafetyEvent[];
  alerts: AlertRecord[];
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
  modelProvider: ModelProvider;
  primarySource: string;
  detections: Detection[];
  events: SafetyEvent[];
  alerts: AlertRecord[];
  comparison?: ModelComparison;
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
