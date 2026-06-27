DEMO_SCRIPT.md

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

Step 1: Open the Dashboard

Start on the Safety Sentinel dashboard.

Show:

* Compliance percentage
* Total violation count
* Violation type breakdown
* Compliance trend over time
* Recent safety events
* Recent mock alerts

Suggested narration:

This is the operations dashboard. Safety Sentinel gives supervisors a live view of safety performance based on visual observations from uploaded images and videos. Instead of manually reviewing footage or waiting for incident reports, teams can see compliance trends, violation types, and coaching opportunities.

Step 2: Upload an Image or Video

Navigate to the upload page.

Upload a sample industrial worksite image or short video clip.

Suggested narration:

For the MVP, we start with uploaded images and videos rather than live camera feeds. A supervisor can upload a clip from a worksite, a warehouse floor, or an inspection review.

Step 3: Run PPE Analysis

Click the analyze button.

Show loading state if available.

Suggested narration:

The backend sends the image or sampled video frames to a vision model. The model looks for people, helmets, missing helmets, safety vests, and missing vests.

Step 4: Show Detection Results

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

Step 5: Show Generated Safety Events

Scroll or navigate to the event log.

Show structured events.

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

Step 6: Show Mock Alert Center

Navigate to the alerts page.

Show mock alerts created from safety events.

Suggested narration:

Safety Sentinel uses a hybrid alerting approach. By default, violations go to supervisor review. The MVP does not identify employees or send real messages. Instead, it creates mock alerts that demonstrate how the workflow could integrate with Slack, Teams, email, or internal safety systems later.

Suggested alert examples:

Missing Helmet Detected
High severity
Supervisor review recommended
Missing Vest Detected
Medium severity
Coaching reminder recommended
Uncertain PPE Status
Manual review recommended

Step 7: Show Analytics

Return to dashboard or analytics page.

Highlight:

* Compliance percentage
* Total violations
* Violation type breakdown
* Trend over time

Suggested narration:

Over time, each detection becomes part of a larger safety intelligence picture. Operations leaders can see whether compliance is improving, which PPE issues are most common, and whether interventions are working.

Step 8: Generate AI Safety Summary

Navigate to the summaries page.

Generate a daily, weekly, or monthly summary.

Suggested narration:

Finally, Safety Sentinel uses an LLM to convert the event data into a readable safety summary. This gives managers an immediate explanation of what happened, what changed, and what actions they should take next.

Example summary:

This week, Safety Sentinel analyzed 248 visual safety observations. Overall PPE compliance was 87%. The most common issue was missing safety vests, followed by missing helmets. Most violations were medium severity and suitable for supervisor review. Recommended actions include reinforcing PPE requirements during pre-shift briefings and reviewing signage near high-traffic zones.

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
0:30 - 1:00  Dashboard overview
1:00 - 1:45  Upload image/video
1:45 - 2:30  PPE analysis results
2:30 - 3:15  Safety event log
3:15 - 4:00  Alert center
4:00 - 4:45  Analytics dashboard
4:45 - 5:30  AI safety summary
5:30 - 6:00  Closing value proposition

Possible Q&A Answers

Why uploaded images and videos instead of live cameras?

The MVP starts with uploads to reduce implementation complexity and avoid unnecessary surveillance concerns. The same architecture can later support live camera feeds or periodic frame sampling.

Why no employee identification?

The product is designed around anonymous safety observations. For the hackathon MVP, we intentionally avoid facial recognition or employee identity. The focus is worksite-level safety intelligence and supervisor review.

What happens if the model is wrong?

Low-confidence detections can be routed to manual review. The platform is designed to support human-in-the-loop workflows rather than automatic enforcement.

How is this different from a simple PPE detector?

A PPE detector produces labels. Safety Sentinel creates a full operations workflow: event logging, analytics, mock alerts, trend reporting, and AI-generated summaries.

Who would use this?

Operations leaders, site supervisors, safety managers, compliance teams, and risk teams at industrial worksites.

What would you build next?

The next features would be live feed support, zone-based PPE rules, real alert integrations, human review queues, customer-specific model fine-tuning, and exportable compliance reports.