Safety Sentinel

Safety Sentinel is an AI-powered safety intelligence platform for industrial worksites. It analyzes uploaded images and video clips to detect PPE compliance, identify unsafe conditions, track safety trends over time, and generate management-ready safety summaries.

Rather than treating safety monitoring as a one-off alerting problem, Safety Sentinel turns visual observations into structured operational data. The platform helps teams understand where safety compliance is strong, where violations are recurring, and what actions supervisors can take to reduce preventable risk.

Problem

Industrial worksites generate constant visual evidence of safety behavior, but most of that information is never converted into useful operational insight.

Safety teams often rely on:

* Manual walk-throughs
* Incident reports after something goes wrong
* Spot checks by supervisors
* Delayed compliance reviews
* Incomplete visibility across shifts, zones, and teams

This creates a gap between what is happening on the floor and what safety leaders can measure.

Solution

Safety Sentinel uses computer vision and AI-generated reporting to turn worksite images and videos into safety intelligence.

The initial version focuses on PPE detection:

* Person detection
* Helmet detection
* No-helmet detection
* Safety vest detection
* No-vest detection

Each uploaded image or video is analyzed for safety-relevant events. The system classifies observations as compliant, warning, or violation events, then stores them for trend analysis and reporting.

Core Product Flow

1. A user uploads an image or video clip from an industrial worksite.
2. The system analyzes the visual content for people and required PPE.
3. Safety events are generated from the detection results.
4. Events are stored in a structured log.
5. The dashboard updates compliance metrics and visual trends.
6. The system generates daily, weekly, or monthly AI safety summaries.
7. Mock alert workflows show how supervisors or approved stakeholders could be notified.

Key Features

PPE Compliance Detection

Safety Sentinel detects whether workers appear to be wearing required PPE, including helmets and safety vests.

Initial detection targets:

* Person
* Helmet
* No helmet
* Vest
* No vest

The system can classify each observation into a safety status:

* Compliant: Required PPE appears present.
* Warning: PPE status is uncertain or incomplete.
* Violation: Required PPE appears missing.

Safety Event Log

Each detection result is converted into a structured safety event.

Example event fields:

* Timestamp
* Source image or video
* Detected worker region
* PPE status
* Violation type
* Confidence score
* Severity
* Suggested action
* Review status

This allows the product to move beyond one-off detection and become a historical source of safety intelligence.

Operations Dashboard

The dashboard gives safety and operations teams a clear overview of worksite compliance.

Initial dashboard metrics:

* Overall compliance percentage
* Total violation count
* Violation type breakdown
* Compliance trend over time
* Positive safety observations
* Daily, weekly, and monthly summary cards

AI-Generated Safety Summaries

Safety Sentinel uses an LLM to generate readable safety summaries for supervisors and managers.

Example outputs:

* Daily safety summary
* Weekly compliance report
* Monthly trend analysis
* Most common violation types
* Recommended corrective actions
* Coaching-focused safety reminders

The goal is to help teams understand not only what happened, but what to do next.

Mock Alert Center

The MVP includes a mock alert workflow stored in its own page inside the app.

Alert examples:

* Supervisor review required
* Missing helmet detected
* Missing vest detected
* Repeated PPE issue
* Low-confidence detection requiring human review

The product uses a hybrid alerting philosophy:

* Supervisor review is the default path.
* Direct coaching can be modeled as a future workflow.
* No employee identity is required in the MVP.
* Workers are not personally identified; detections are treated as anonymous safety events.

Product Positioning

Safety Sentinel is designed primarily as an operations intelligence platform, with safety coaching as a secondary benefit.

The product is not surveillance-centric; it focuses on compliance trends and systemic improvements rather than individual monitoring. Instead, it helps industrial teams convert safety observations into measurable insights, better reporting, and proactive coaching workflows.

Target Users

Safety Sentinel is designed for general industrial worksites, including:

* Manufacturing facilities
* Warehouses
* Logistics operations
* Construction-adjacent industrial sites
* Maintenance environments
* Energy and infrastructure worksites

Primary users include:

* Operations leaders
* Safety managers
* Site supervisors
* Compliance teams
* Risk management teams

MVP Scope

The first version focuses on uploaded images and videos.

Included in MVP

* Upload image
* Upload video
* Run visual safety analysis
* Detect person, helmet/no helmet, vest/no vest
* Generate safety events
* View annotated results
* Track violation counts
* View compliance percentage
* View violation type breakdown
* View trends over time
* Generate AI safety summaries
* Display mock alerts in an alert center

Not Included in MVP

* Live camera stream ingestion
* Facial recognition
* Employee identification
* Real SMS/email/Slack alerts
* Production-grade incident escalation
* HR or badge-system integration
* Automated disciplinary workflows

Tech Stack

Frontend

* Next.js
* React
* Recharts for dashboard visualizations

Backend

* FastAPI
* REST API for inference, event creation, analytics, and summaries

Computer Vision

* Qwen Vision model for visual understanding and PPE detection, evaluated for inference cost and accuracy
* Potential fallback or comparison path:
    * Roboflow-hosted model
    * YOLO model trained or fine-tuned on PPE datasets
* Decision point: API-based (Qwen) vs. self-hosted (YOLO) will depend on latency and cost requirements

LLM Summaries

* Claude API for daily, weekly, and monthly safety summaries

Data Storage

The app stores safety events, upload metadata, detection results, summary outputs, and mock alerts.

Suggested entities:

* Uploads
* Detection results
* Safety events
* Compliance summaries
* Alert records

Alerting

* Mock alert center inside the application
* Future integration targets:
    * Slack
    * Microsoft Teams
    * Email
    * SMS
    * Internal safety management systems

Data Model Draft

The following schema is exploratory and will be finalized during backend implementation.

Upload

Represents an image or video submitted for analysis.

type Upload = {
  id: string;
  fileName: string;
  fileType: "image" | "video";
  fileUrl: string;
  uploadedAt: string;
  status: "uploaded" | "processing" | "processed" | "failed";
};

DetectionResult

Represents model output from an uploaded image or video frame.

type DetectionResult = {
  id: string;
  uploadId: string;
  frameTimestamp?: number;
  label: "person" | "helmet" | "no_helmet" | "vest" | "no_vest";
  confidence: number;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  createdAt: string;
};

SafetyEvent

Represents a structured compliance event generated from detections.

type SafetyEvent = {
  id: string;
  uploadId: string;
  eventType: "positive_observation" | "ppe_violation" | "uncertain_review";
  violationType?: "no_helmet" | "no_vest";
  severity: "low" | "medium" | "high";
  confidence: number;
  status: "open" | "reviewed" | "dismissed" | "resolved";
  suggestedAction: string;
  createdAt: string;
};

AlertRecord

Represents a mock alert generated from a safety event.

type AlertRecord = {
  id: string;
  safetyEventId: string;
  alertType: "supervisor_review" | "coaching_reminder" | "manual_review";
  title: string;
  message: string;
  status: "draft" | "queued" | "sent" | "dismissed"; // "sent" represents mock delivery in MVP
  createdAt: string;
};

SafetySummary

Represents an AI-generated daily, weekly, or monthly report.

type SafetySummary = {
  id: string;
  period: "daily" | "weekly" | "monthly";
  startDate: string;
  endDate: string;
  compliancePercentage: number;
  totalViolations: number;
  topViolationTypes: string[];
  summaryText: string;
  recommendedActions: string[];
  createdAt: string;
};

Example AI Summary

**[Generated Example]**

This week, Safety Sentinel analyzed 248 visual safety observations across uploaded worksite images and videos. Overall PPE compliance was 87%. The most common issue was missing safety vests, followed by missing helmets. Most violations were medium severity and suitable for supervisor review rather than immediate escalation. Recommended actions include reinforcing PPE expectations during pre-shift briefings, reviewing signage near high-traffic zones, and conducting a targeted vest-compliance reminder for floor teams.

Example User Journey

A site supervisor uploads a short video from the warehouse floor.

Safety Sentinel processes the video and identifies several workers. Most appear compliant, but one worker is detected without a visible safety vest.

The system creates a medium-severity safety event, adds it to the event log, updates the compliance dashboard, and creates a mock supervisor alert.

At the end of the day, the supervisor opens the summary page and receives an AI-generated report explaining the day’s compliance percentage, top violation types, and suggested corrective actions.

Hackathon Demo Plan

Demo Step 1: Upload

Upload a worksite image or short video clip.

Demo Step 2: Analyze

Run PPE detection and show detected people, helmets, and vests.

Demo Step 3: Generate Events

Convert model output into structured safety events.

Demo Step 4: Dashboard

Show compliance percentage, violation count, violation type breakdown, and trend over time.

Demo Step 5: Alerts

Display mock alerts generated from safety events.

Demo Step 6: AI Summary

Generate a daily or weekly safety report using the stored event data.

Why This Matters

Safety Sentinel helps industrial teams shift from reactive safety management to proactive safety intelligence.

Instead of waiting for incidents or manually reviewing footage, teams can use AI to continuously convert visual safety observations into measurable compliance trends, coaching opportunities, and operational insight.

Future Enhancements

* Live camera feed support
* Zone-based PPE rules
* Location-aware compliance analytics
* Real alert integrations
* Human review workflow
* Supervisor approval queue
* Custom PPE policy configuration
* Multi-site benchmarking
* Exportable compliance reports
* Integration with existing safety management systems
* Model fine-tuning on customer-specific worksites

Project Status

Safety Sentinel is a hackathon MVP focused on demonstrating how computer vision and LLM-generated reporting can turn industrial safety observations into actionable operations intelligence.