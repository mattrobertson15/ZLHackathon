"use client";

import { useEffect, useState } from "react";
import { listZones, createZone } from "@/lib/api";
import { Zone } from "@/lib/types";

const PPE_OPTIONS = [
  { value: "helmet", label: "Helmet" },
  { value: "vest", label: "Safety Vest" },
];

const VIOLATION_OPTIONS = [
  { value: "no_helmet", label: "No Helmet" },
  { value: "no_vest", label: "No Vest" },
];

const SEVERITY_OPTIONS = ["low", "medium", "high"];

const SEVERITY_COLORS: Record<string, string> = {
  high: "text-red-700 bg-red-100",
  medium: "text-yellow-700 bg-yellow-100",
  low: "text-green-700 bg-green-100",
};

function ZoneCard({ zone }: { zone: Zone }) {
  return (
    <div className="bg-white rounded-lg shadow p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 text-lg">{zone.displayName}</h3>
          <p className="text-xs font-mono text-gray-400">{zone.id}</p>
        </div>
        <span className="text-xs text-gray-500">{new Date(zone.createdAt).toLocaleDateString()}</span>
      </div>

      <div className="space-y-2 text-sm">
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Required PPE</p>
          {zone.requiredPpe.length === 0 ? (
            <span className="text-gray-400 italic text-xs">None specified</span>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {zone.requiredPpe.map((p) => (
                <span key={p} className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                  {p.replace("_", " ")}
                </span>
              ))}
            </div>
          )}
        </div>

        {Object.keys(zone.severityOverrides).length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Severity Overrides</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(zone.severityOverrides).map(([violation, severity]) => (
                <span key={violation} className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[severity] ?? "bg-gray-100 text-gray-700"}`}>
                  {violation.replace("_", " ")} → {severity}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ZonesPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form state
  const [displayName, setDisplayName] = useState("");
  const [requiredPpe, setRequiredPpe] = useState<string[]>([]);
  const [overrides, setOverrides] = useState<Record<string, string>>({});

  useEffect(() => {
    listZones()
      .then(setZones)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load zones"))
      .finally(() => setLoading(false));
  }, []);

  function togglePpe(value: string) {
    setRequiredPpe((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  }

  function setOverrideSeverity(violation: string, severity: string) {
    setOverrides((prev) => {
      if (!severity) {
        const next = { ...prev };
        delete next[violation];
        return next;
      }
      return { ...prev, [violation]: severity };
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim()) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const newZone = await createZone({
        displayName: displayName.trim(),
        requiredPpe,
        severityOverrides: overrides,
      });
      setZones((prev) => [...prev, newZone]);
      setDisplayName("");
      setRequiredPpe([]);
      setOverrides({});
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create zone");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center">
        <div className="text-gray-600">Loading zones...</div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Zones</h1>
          <p className="text-gray-500 mt-1">Define facility areas and their PPE requirements.</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? "Cancel" : "+ Add Zone"}
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">{error}</div>
      )}

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-lg shadow p-6 mb-6 space-y-5"
        >
          <h2 className="text-lg font-semibold text-gray-900">New Zone</h2>

          {formError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{formError}</div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Zone Name *</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Chemical Storage Area"
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {displayName && (
              <p className="text-xs text-gray-400 mt-1">
                ID: {displayName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Required PPE</label>
            <div className="flex gap-4">
              {PPE_OPTIONS.map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requiredPpe.includes(opt.value)}
                    onChange={() => togglePpe(opt.value)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Severity Overrides</label>
            <p className="text-xs text-gray-500 mb-3">Override the default severity for specific violations in this zone.</p>
            <div className="space-y-2">
              {VIOLATION_OPTIONS.map((opt) => (
                <div key={opt.value} className="flex items-center gap-3">
                  <span className="text-sm text-gray-700 w-24">{opt.label}</span>
                  <select
                    value={overrides[opt.value] ?? ""}
                    onChange={(e) => setOverrideSeverity(opt.value, e.target.value)}
                    className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Default</option>
                    {SEVERITY_OPTIONS.map((s) => (
                      <option key={s} value={s} className="capitalize">{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || !displayName.trim()}
            className="w-full py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? "Creating..." : "Create Zone"}
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {zones.map((zone) => (
          <ZoneCard key={zone.id} zone={zone} />
        ))}
      </div>

      {zones.length === 0 && !showForm && (
        <div className="text-center py-16 text-gray-400">
          No zones configured. Add your first zone to get started.
        </div>
      )}
    </div>
  );
}
