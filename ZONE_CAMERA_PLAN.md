# Zone & Camera Logic — Unified Implementation Plan

This plan reconciles two proposals that both depend on location/camera logic:

1. **Zone-Based PPE Rules** — make detection results produce different safety
   events depending on the physical area (zone) the image came from, with
   cameras pre-registered to a zone so uploads inherit it automatically.
2. **Repeated Zone Violation Detection** — flag zones that accumulate the same
   violation repeatedly (e.g. "Loading Dock has 3 no-vest violations this
   week") without any employee identity, surfacing the insight on the dashboard
   and as a mock alert.

The two plans were drafted independently and disagree on one thing: the first
wants to **replace** the free-text `location_label` with a structured `zone_id`,
while the second **groups by `location_label`**. This plan resolves that by
making zones the canonical location and keying repeated-violation detection on a
**single resolved location key** that prefers `zone_id` and falls back to
`location_label`. That one decision lets both features share the same schema and
the same demo dataset.

---

## 1. Shared location schema

This is the foundation both features build on.

### Zone

A named physical area with a PPE policy.

```
id:                 "loading-dock"          # stable slug, PK
display_name:       "Loading Dock"
required_ppe:       ["vest"]                 # JSON array
severity_overrides: {"no_vest": "high"}      # JSON object, optional per-rule escalation
```

### Camera

A logical clip source pre-assigned to a zone. Cameras are seeded for the demo;
**no authenticated ingest endpoint and no API-key issuance is built in this
pass** (explicitly deferred — see Non-Goals). Cameras exist so that an upload can
be *assigned* to a camera and inherit that camera's zone.

```
id:           "cam-02"
display_name: "Dock Camera North"
zone_id:      "loading-dock"
status:       "active" | "inactive"
```

### Upload (extended)

Two new nullable columns, plus the existing `location_label` retained for
backward compatibility and as the legacy fallback grouping key:

```
zone_id:        nullable FK → zones.id      # canonical location
camera_id:      nullable FK → cameras.id    # set when assigned to a camera
location_label: nullable string             # legacy / free-text fallback
```

### Resolved location key (the reconciliation point)

Everywhere we need "which location is this", we use one helper:

```
resolved_key(upload)   = upload.zone_id  or  upload.location_label  or  None
resolved_label(upload) = zone.display_name (if zone_id)  or  upload.location_label
```

- Zone-aware rules use `zone_id` directly (a real zone, or none → legacy global rules).
- Repeated-violation grouping uses `resolved_key` so zone-tagged and legacy
  location-tagged uploads both participate, but never collide.

---

## 2. Data model changes

### New table `zones`

| column             | type     | notes                                  |
|--------------------|----------|----------------------------------------|
| id                 | string   | PK slug, e.g. `loading-dock`           |
| display_name       | string   |                                        |
| required_ppe       | text     | JSON array `["helmet","vest"]`         |
| severity_overrides | text     | JSON object `{"no_vest":"high"}`       |
| created_at         | datetime |                                        |

### New table `cameras`

| column       | type     | notes                       |
|--------------|----------|-----------------------------|
| id           | string   | PK slug, e.g. `cam-02`      |
| display_name | string   |                             |
| zone_id      | string   | FK → zones.id               |
| status       | string   | `active` \| `inactive`      |
| created_at   | datetime |                             |

### `uploads` (add columns)

- `zone_id` (nullable, FK → zones.id)
- `camera_id` (nullable, FK → cameras.id)
- `location_label` kept (nullable)

Tables are created on startup and **seeded if empty** — no migration UI. SQLite
with `create_all` adds the new tables; the new upload columns are additive and
nullable so existing rows are unaffected.

---

## 3. Zone-aware rule engine

`evaluate(detections, upload_id, zone=None)`:

- **`zone is None`** → unchanged legacy behavior (global `_PPE_RULES`). This
  preserves backward compatibility for untagged uploads and keeps the existing
  tests/behavior intact.
- **zone present**, per PPE detection:
  - Positive item (`helmet`/`vest`): if the item is in `zone.required_ppe` →
    `positive_observation`; otherwise **no event** (not required here).
  - Violation item (`no_helmet`/`no_vest`): map to its PPE item; if that item is
    in `zone.required_ppe` → `ppe_violation` with severity taken from
    `zone.severity_overrides[label]` if present, else the global default;
    otherwise **no event** (not required here).
  - `suggestedAction` names the zone, e.g. *"Supervisor review recommended.
    Safety vest required in Loading Dock. Safety vest appears missing."*
- `uncertain_review` (person visible, PPE state unknown) is unchanged — it is a
  detection-quality signal, not a zone policy outcome.

This makes a `no_vest` in a helmet-only zone a non-event, and lets a vest-required
zone escalate `no_vest` to `high`.

---

## 4. Repeated zone violation detection

A small service aggregates `ppe_violation` events over a rolling **7-day**
window, grouped by **`resolved_key` + `violationType`**, threshold **≥ 3**.

Insight shape (camelCase, served to the frontend):

```ts
{
  zoneLabel: string;            // resolved_label
  violationType: "no_helmet" | "no_vest";
  count: number;
  distinctUploadCount: number;
  severity: "medium" | "high";  // max severity in the group
  latestEventId: string;
  firstSeenAt: string;
  lastSeenAt: string;
  message: string;              // "Loading Dock has 3 no-vest violations in the past week."
}
```

- Returned as `repeatedViolations: RepeatedViolation[]` on `GET /analytics/overview`
  (always computed on the weekly window, independent of the overview `period`).
- The aggregation is a **pure function** `aggregate_repeated_violations(events,
  uploads_by_id, zones_by_id, threshold)` so it is unit-testable without a DB.

### Mock repeated-violation alert

A new alert type `repeated_violation` is added to the union. During analysis,
after new events are persisted, if a newly created violation pushes its
`(resolved_key, violationType)` group to the threshold and no `repeated_violation`
alert already covers that group within the window, one `AlertRecord` is created,
linked to the latest event in the group:

> **Repeated Vest Issue** — "Loading Dock has 3 no-vest violations in the past
> week. Supervisor coaching review is recommended."

Dedup is by resolving each existing `repeated_violation` alert's event back to
its group, so re-analyzing does not spam duplicate alerts.

---

## 5. Backend API surface

- `GET /zones`, `GET /zones/{zone_id}` — list/detail (powers the upload dropdown).
- `GET /cameras`, `GET /cameras/{camera_id}` — list/detail (demo/admin display).
- `POST /uploads` — accept optional `zoneId` and `cameraId` form fields. If
  `cameraId` is given, the upload inherits the camera's zone (assignment path);
  otherwise `zoneId` is used directly. `locationLabel` still accepted.
- `POST /uploads/{id}/analyze` — resolve the upload's zone and pass it to the
  rule engine; after persisting events, generate repeated-violation alerts.
- `GET /analytics/overview` — add `repeatedViolations`.
- Upload serialization (uploads, events, admin) gains `zoneId`, `cameraId`, and
  `zoneDisplayName` (resolved where a zone lookup is available).

---

## 6. Frontend

- **types.ts** — add `Zone`, `Camera`, `RepeatedViolation`; extend `Upload`
  (`zoneId`, `cameraId`, `zoneDisplayName`), `AlertType` (`repeated_violation`),
  and `AnalyticsOverview` (`repeatedViolations`).
- **api.ts** — `listZones()`, `listCameras()`; `uploadFile` accepts `zoneId`.
- **Upload page** — replace the free-text location input with a zone dropdown
  populated from `GET /zones` ("No specific zone" sends nothing).
- **Results page** — show the zone (display name) in upload info.
- **Dashboard** — a "Repeated Zone Issues" card listing zone, violation type,
  count, and last occurrence; render cleanly when empty.
- **Alerts page / AlertCard** — color, label, and filter support for
  `repeated_violation`.
- **report.ts** — include repeated-zone issues in the dashboard markdown export.

---

## 7. Sample dataset (demo scenario)

`POST /admin/demo-scenario` is rewritten so the seeded data exercises **both**
features and stays internally consistent with the zone-aware rules (the seeded
events match what the rule engine would produce for each zone):

- Uploads tagged with `zone_id` + `camera_id` across `loading-dock`,
  `general-floor`, and `welding-station`, plus one legacy `location_label`-only
  upload (no zone) to prove the fallback path.
- **Suppressed-vs-triggered**: a `no_vest` detection at `general-floor`
  (helmet-only) produces **no event**, while `no_vest` at `loading-dock`
  produces a `high` violation — same detection, different outcome by zone. A
  `no_helmet` at `loading-dock` is likewise suppressed.
- **Repeated trigger**: three `no_vest` violations at `loading-dock` across three
  uploads within the week → one `repeated_violation` alert.
- Positive observations at `welding-station` (helmet + vest) and `general-floor`
  (helmet) keep the compliance percentage realistic.
- Alert coverage: `supervisor_review` (high dock violations), `coaching_reminder`
  (legacy medium no_vest), `manual_review` (uncertain), and `repeated_violation`.

Seeded zones/cameras come from the startup seed; the demo scenario only seeds
uploads/detections/events/alerts and references those zone/camera IDs.

---

## 8. Out of scope (this pass)

- Authenticated camera ingest endpoint and API-key issuance/rotation (cameras
  are seeded and used only for zone assignment + display).
- Employee identity, facial recognition, or person re-identification — repeated
  detection is intentionally *same zone / same violation type* only.
- GPS/geofencing — zones are logical labels, not spatial polygons.
- A UI to create/edit zones or cameras — both are seeded.
- Configurable thresholds — the weekly window and `≥ 3` threshold are constants.

---

## 9. Implementation order

1. Schema: `zones`, `cameras`, `zone_id`/`camera_id` on `uploads`; startup seed.
2. Repositories: `get_zone`, `list_zones`, `get_camera`, `list_cameras`.
3. Zone-aware rule engine.
4. Repeated-violation service (pure aggregation + alert generation).
5. Routes: zones, cameras, upload fields, analyze wiring, overview field.
6. Demo scenario rewrite (the sample dataset).
7. Frontend: types, api, upload dropdown, results, dashboard card, alerts, report.
8. Docs: ARCHITECTURE, API, README, DEMOSCRIPT.
9. Tests: rule-engine zone logic + repeated-violation aggregation.
