DEMOSCRIPT.md

Safety Sentinel Demo Script

This document provides a concise demo flow for presenting Safety Sentinel during the hackathon.

Demo Goal

Show that Safety Sentinel can turn uploaded worksite images or videos into structured safety intelligence.

The demo should communicate three ideas:

1. The system detects PPE compliance from visual inputs.
2. It converts detections into operational safety events.
3. It summarizes safety trends for supervisors and operations leaders.

One-Sentence Pitch

Safety Sentinel is an AI-powered safety intelligence platform that turns industrial worksite images and videos into PPE compliance analytics, mock alerts, and AI-generated safety summaries.

30-Second Intro

Industrial worksites generate constant visual evidence of safety behavior, but most of that information is never converted into usable operational data.

Safety Sentinel analyzes uploaded worksite images and videos to detect whether workers are wearing required PPE, such as helmets and safety vests. It converts those detections into structured safety events, tracks compliance trends over time, and generates daily, weekly, or monthly safety summaries for operations teams.

The goal is not employee surveillance. The goal is operations intelligence and proactive safety coaching.

Demo Flow

Step 1: Load the Demo Scenario

Start on the Demo page.

Click "Load Demo Scenario" to seed the warehouse shift scenario.

Show:

* Seven zone-tagged uploads (Loading Dock, General Floor, Welding Station, plus
  a legacy upload with no zone)
* Generated PPE detections
* Safety events across violations, positive observations, and manual review
* Mock alerts for supervisor review, coaching reminders, manual review, and a
  repeated zone violation

Suggested narration:

For demo reliability, Safety Sentinel includes a repeatable warehouse shift scenario.
It uses the same upload, detection, event, alert, and analytics tables as the live
ingestion workflow, so the rest of the product behaves exactly like a real run. The
uploads are tagged with zones, so the same no-vest detection is a high-severity
violation at the Loading Dock but produces no event on the General Floor where vests
are not required — and three no-vest violations at the Loading Dock this week raise a
repeated zone violation alert, all without identifying any employee.

Step 2: Open the Dashboard

Start on the Safety Sentinel dashboard.

Show:

* Compliance percentage
* Total violation count
* Violation type breakdown
* Repeated Zone Issues card (Loading Dock — 3 no-vest violations this week)
* Compliance trend over time
* Recent safety events
* Recent mock alerts
* Download Report button for a manager-ready markdown dashboard export
  (includes the repeated-zone issues table)

Suggested narration:

This is the operations dashboard. Safety Sentinel gives supervisors a live view of safety performance based on visual observations from uploaded images and videos. Instead of manually reviewing footage or waiting for incident reports, teams can see compliance trends, violation types, and coaching opportunities.

Step 3: Upload an Image or Video

Navigate to the upload page.

Upload a sample industrial worksite image or short video clip.

Suggested narration:

For the MVP, we start with uploaded images and videos rather than live camera feeds. A supervisor can upload a clip from a worksite, a warehouse floor, or an inspection review.

Step 4: Run PPE Analysis

Click the analyze button.

Show loading state if available.

Suggested narration:

The backend sends the image or sampled video frames to the vision inference layer. By default, Safety Sentinel uses the Roboflow PPE detector first because it is trained for object detection, then falls back to Qwen Vision or deterministic mock detections if needed. The model looks for people, helmets, missing helmets, safety vests, and missing vests.

Optional technical note:

The backend also supports a compare mode that runs Roboflow and Qwen side by side, then reports where the two models agree or disagree. Operational safety events still come from the primary detector.

Step 5: Show Detection Results

Navigate to the results page.

Show annotated image or frame-level results.

Highlight:

* Person detections
* Helmet/no-helmet detections
* Vest/no-vest detections
* Confidence scores
* Safety status

Suggested narration:

The model output is normalized into detection results. These detections are then passed through a safety rule engine. For example, if a person is detected without a visible helmet, the system creates a high-severity PPE violation. If a vest is missing, it creates a medium-severity violation.

Step 6: Show Generated Safety Events

Scroll or navigate to the event log.

Show structured events.
Select an event and show the source image or video in the review panel so the
supervisor can visually confirm whether the AI output is correct before marking
the event reviewed, dismissed, or resolved.

Example events:

Missing helmet detected
Severity: High
Status: Open
Suggested action: Supervisor review recommended
Missing vest detected
Severity: Medium
Status: Open
Suggested action: Coaching reminder recommended
PPE compliant observation
Severity: Low
Status: Logged
Suggested action: No action required

Suggested narration:

The important part is that Safety Sentinel does not stop at object detection. It converts model outputs into structured safety events that can be tracked over time. This creates an operational data layer for safety teams.

Step 7: Show Mock Alert Center

Navigate to the alerts page.

Show mock alerts created from safety events.

Suggested narration:

Safety Sentinel uses a hybrid alerting approach. By default, violations go to supervisor review. The MVP does not identify employees or send real messages. Instead, it creates mock alerts that demonstrate how the workflow could integrate with Slack, Teams, email, or internal safety systems later.

Suggested alert examples:

Missing Vest Detected
High severity (Loading Dock — vest required)
Supervisor review recommended
Missing Vest Detected
Medium severity (Packout Line)
Coaching reminder recommended
Uncertain PPE Status
Manual review recommended
Repeated Vest Issue
Loading Dock has 3 no-vest violations in the past week
Supervisor coaching review recommended

Step 8: Show Analytics

Return to dashboard or analytics page.

Highlight:

* Compliance percentage
* Total violations
* Violation type breakdown
* Trend over time

Suggested narration:

Over time, each detection becomes part of a larger safety intelligence picture. Operations leaders can see whether compliance is improving, which PPE issues are most common, and whether interventions are working.

Step 9: Generate AI Safety Summary

Navigate to the summaries page.

Generate a daily, weekly, or monthly summary.
Open or download the generated report.

Suggested narration:

Finally, Safety Sentinel uses an LLM to convert the event data into a readable safety summary. This gives managers an immediate explanation of what happened, what changed, and what actions they should take next.

The summary can also be downloaded as a markdown safety report, so a supervisor
can attach it to a shift recap, print it, or share it with operations leadership
without needing to keep the dashboard open.

Example summary:

This week, Safety Sentinel analyzed 248 visual safety observations. Overall PPE compliance was 87%. The most common issue was missing safety vests, followed by missing helmets. Most violations were medium severity and suitable for supervisor review. Recommended actions include reinforcing PPE requirements during pre-shift briefings and reviewing signage near high-traffic zones.

Optional Demo Step: Live Camera (RTSP) Emulation

This step shows Safety Sentinel watching a "live CCTV camera" instead of a
one-off upload. The camera is emulated by looping a video file into an RTSP
server, so it behaves like a real feed without needing a physical camera.

Setup (before the demo):

1. Build demo footage (once): `./emulator/make-sample-video.sh`
   (or drop your own clip in as `emulator/media/demo-worksite.mp4`).
2. Start the stack: `docker compose up --build`
   This runs mediamtx (RTSP server) + ffmpeg (restream loop) + the backend.

During the demo:

1. Go to the Cameras page.
2. Register a camera with RTSP URL `rtsp://mediamtx:8554/worksite-demo`
   (use `rtsp://localhost:8554/worksite-demo` if the backend runs on the host).
3. Click "Start monitoring." The live snapshot preview appears and the status
   flips to "Live."
4. Wait one interval (default 15s) — new PPE events appear automatically on the
   Dashboard, Events, and Alerts pages, attributed to the camera.

Suggested narration:

The same pipeline that analyzes uploads also runs against a live RTSP camera.
Here we've emulated a worksite camera by restreaming a video file, but to Safety
Sentinel it's just an RTSP URL — the kind a real CCTV system exposes. Once
monitoring starts, the backend captures frames on an interval, runs PPE
inference, and raises safety events continuously, with no human in the loop.
This is how the product moves from reviewing clips to always-on monitoring.

Technical note: continuous monitoring needs an always-on process, so this stack
runs as containers on a persistent host rather than on serverless. The RTSP feed
stays on a private network — only the API is exposed.

Closing Pitch

Suggested closing:

Safety Sentinel helps industrial teams move from reactive safety management to proactive safety intelligence. By combining computer vision, structured event tracking, mock alert workflows, and AI-generated summaries, the platform gives safety and operations leaders a clearer view of worksite risk without requiring employee identity or live surveillance in the MVP.

Judge-Friendly Value Proposition

Safety Sentinel provides value in four ways:

1. Detection
    * Finds PPE issues in uploaded worksite images and videos.
2. Structure
    * Converts raw detections into safety events.
3. Analytics
    * Tracks compliance trends and violation patterns.
4. Action
    * Generates alerts and management-ready summaries.

Key Differentiator

The core insight is that PPE detection by itself is not enough.

Safety Sentinel turns detection into an operational safety intelligence loop:

Visual input -> PPE detection -> Safety event -> Alert -> Analytics -> AI summary -> Coaching action

MVP Boundaries

Be clear about what the MVP does and does not do.

MVP Includes

* Uploaded images
* Uploaded videos
* PPE detection
* Safety events
* Dashboard metrics
* Mock alerts
* AI-generated summaries
* Exportable markdown safety reports

MVP Does Not Include

* Facial recognition
* Employee identification
* Real-time camera monitoring
* Real alert delivery
* Automated disciplinary action

Suggested narration:

We intentionally avoided employee identity and disciplinary workflows. The MVP is focused on anonymous safety observations, supervisor review, and operations intelligence.

Backup Demo Plan

If live model inference fails, use seeded detections and explain the architecture.

Backup narration:

For demo reliability, this sample uses pre-seeded model outputs in the same format produced by our inference layer. The rest of the system — event creation, dashboard analytics, alert generation, and AI summaries — runs against the same data model.

Ideal Demo Timing

0:00 - 0:30  Problem and pitch
0:30 - 0:55  Load Demo scenario
0:55 - 1:25  Dashboard overview
1:25 - 2:05  Upload image/video or open seeded result
2:05 - 2:45  PPE analysis results
2:45 - 3:25  Safety event log
3:25 - 4:05  Alert center
4:05 - 4:45  Analytics dashboard
4:45 - 5:30  AI safety summary
5:30 - 6:00  Closing value proposition

Possible Q&A Answers

Why uploaded images and videos instead of live cameras?

The MVP starts with uploads to reduce complexity and avoid unnecessary
surveillance concerns, but the same architecture already supports live RTSP
cameras — we demo this with an emulated camera (a video file restreamed over
RTSP). The backend captures frames on an interval and runs the identical
detection-to-event pipeline, so live monitoring and uploads share one code path.

Why no employee identification?

The product is designed around anonymous safety observations. For the hackathon MVP, we intentionally avoid facial recognition or employee identity. The focus is worksite-level safety intelligence and supervisor review.

What happens if the model is wrong?

Low-confidence detections can be routed to manual review. The platform is designed to support human-in-the-loop workflows rather than automatic enforcement.

How is this different from a simple PPE detector?

A PPE detector produces labels. Safety Sentinel creates a full operations workflow: event logging, analytics, mock alerts, trend reporting, and AI-generated summaries.

Who would use this?

Operations leaders, site supervisors, safety managers, compliance teams, and risk teams at industrial worksites.

What would you build next?

Zone-based PPE rules and repeated zone violation detection are already in the
product. The next features would be live feed support, authenticated camera
ingestion, real alert integrations, human review queues, customer-specific model
fine-tuning, and exportable compliance reports.
