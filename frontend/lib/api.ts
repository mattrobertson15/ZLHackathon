import {
  Upload,
  Detection,
  SafetyEvent,
  AlertRecord,
  AnalyticsOverview,
  AnalyticsTrends,
  SafetySummary,
  AnalyzeResponse,
  ModelProvider,
} from "./types";
import type { DemoScenarioResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production" ? "/_/backend" : "http://localhost:8000");

// Upload media is served either as an absolute Vercel Blob URL or as a
// "/media/..." path relative to the backend, depending on storage backend.
export function resolveMediaUrl(fileUrl: string): string {
  if (/^https?:\/\//.test(fileUrl)) {
    return fileUrl;
  }
  return `${API_BASE_URL}${fileUrl}`;
}

async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "API request failed");
  }

  return response.json();
}

// Uploads API
export async function listUploads(): Promise<Upload[]> {
  const data = await apiCall<{ uploads: Upload[] }>("/uploads");
  return data.uploads;
}

export async function getUpload(uploadId: string): Promise<Upload> {
  const data = await apiCall<{ upload: Upload }>(`/uploads/${uploadId}`);
  return data.upload;
}

export async function uploadFile(
  file: File,
  locationLabel?: string,
  notes?: string
): Promise<Upload> {
  const formData = new FormData();
  formData.append("file", file);
  if (locationLabel) formData.append("locationLabel", locationLabel);
  if (notes) formData.append("notes", notes);

  const response = await fetch(`${API_BASE_URL}/uploads`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "Upload failed");
  }

  const data = await response.json();
  return data.upload;
}

// Detection API
export async function getDetections(uploadId: string): Promise<Detection[]> {
  const data = await apiCall<{ uploadId: string; detections: Detection[] }>(
    `/uploads/${uploadId}/detections`
  );
  return data.detections;
}

// Analysis API
export async function analyzeUpload(
  uploadId: string,
  createEvents = true,
  createAlerts = true,
  modelProvider: ModelProvider = "auto"
): Promise<AnalyzeResponse> {
  return apiCall<AnalyzeResponse>(`/uploads/${uploadId}/analyze`, {
    method: "POST",
    body: JSON.stringify({
      modelProvider,
      createEvents,
      createAlerts,
    }),
  });
}

// Safety Events API
export async function listEvents(params?: {
  status?: string;
  eventType?: string;
  violationType?: string;
  severity?: string;
  limit?: number;
}): Promise<SafetyEvent[]> {
  const query = new URLSearchParams();
  if (params?.status) query.append("status", params.status);
  if (params?.eventType) query.append("eventType", params.eventType);
  if (params?.violationType) query.append("violationType", params.violationType);
  if (params?.severity) query.append("severity", params.severity);
  if (params?.limit) query.append("limit", params.limit.toString());

  const data = await apiCall<{ events: SafetyEvent[] }>(
    `/events?${query.toString()}`
  );
  return data.events;
}

export async function getEvent(eventId: string): Promise<SafetyEvent> {
  const data = await apiCall<{ event: SafetyEvent }>(`/events/${eventId}`);
  return data.event;
}

export async function updateEvent(
  eventId: string,
  status: string
): Promise<SafetyEvent> {
  const data = await apiCall<{ event: SafetyEvent }>(`/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  return data.event;
}

// Alerts API
export async function listAlerts(params?: {
  status?: string;
  alertType?: string;
  limit?: number;
}): Promise<AlertRecord[]> {
  const query = new URLSearchParams();
  if (params?.status) query.append("status", params.status);
  if (params?.alertType) query.append("alertType", params.alertType);
  if (params?.limit) query.append("limit", params.limit.toString());

  const data = await apiCall<{ alerts: AlertRecord[] }>(
    `/alerts?${query.toString()}`
  );
  return data.alerts;
}

export async function updateAlert(
  alertId: string,
  status: string
): Promise<AlertRecord> {
  const data = await apiCall<{ alert: AlertRecord }>(`/alerts/${alertId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  return data.alert;
}

// Analytics API
export async function getAnalyticsOverview(
  period = "weekly"
): Promise<AnalyticsOverview> {
  return apiCall<AnalyticsOverview>(`/analytics/overview?period=${period}`);
}

export async function getAnalyticsTrends(
  period = "daily"
): Promise<AnalyticsTrends> {
  return apiCall<AnalyticsTrends>(`/analytics/trends?period=${period}`);
}

// Summaries API
export async function generateSummary(
  period: string,
  startDate: string,
  endDate: string
): Promise<SafetySummary> {
  const data = await apiCall<{ summary: SafetySummary }>(
    "/summaries/generate",
    {
      method: "POST",
      body: JSON.stringify({ period, startDate, endDate }),
    }
  );
  return data.summary;
}

export async function listSummaries(params?: {
  period?: string;
  limit?: number;
}): Promise<SafetySummary[]> {
  const query = new URLSearchParams();
  if (params?.period) query.append("period", params.period);
  if (params?.limit) query.append("limit", params.limit.toString());

  const data = await apiCall<{ summaries: SafetySummary[] }>(
    `/summaries?${query.toString()}`
  );
  return data.summaries;
}

export async function getSummary(summaryId: string): Promise<SafetySummary> {
  const data = await apiCall<{ summary: SafetySummary }>(
    `/summaries/${summaryId}`
  );
  return data.summary;
}

// Admin API
export async function resetIncidents(): Promise<{ status: string; message: string }> {
  return apiCall<{ status: string; message: string }>("/admin/reset", {
    method: "POST",
  });
}

export async function loadDemoScenario(): Promise<DemoScenarioResponse> {
  return apiCall<DemoScenarioResponse>("/admin/demo-scenario", {
    method: "POST",
  });
}
