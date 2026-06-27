"use client";

import { useState } from "react";
import { Detection } from "@/lib/types";

interface BoundingBoxOverlayProps {
  src: string;
  alt: string;
  detections: Detection[];
}

const VIOLATION_LABELS = new Set(["no_helmet", "no_vest"]);
const COMPLIANT_LABELS = new Set(["helmet", "vest"]);

function boxColor(label: string): string {
  if (VIOLATION_LABELS.has(label)) return "border-red-500 bg-red-500/10 text-red-50";
  if (COMPLIANT_LABELS.has(label)) return "border-green-500 bg-green-500/10 text-green-50";
  return "border-blue-500 bg-blue-500/10 text-blue-50";
}

function tagColor(label: string): string {
  if (VIOLATION_LABELS.has(label)) return "bg-red-600";
  if (COMPLIANT_LABELS.has(label)) return "bg-green-600";
  return "bg-blue-600";
}

export default function BoundingBoxOverlay({ src, alt, detections }: BoundingBoxOverlayProps) {
  const [naturalSize, setNaturalSize] = useState<{ width: number; height: number } | null>(null);

  const boxDetections = detections.filter((d) => d.boundingBox);

  return (
    <div className="relative inline-block w-full">
      <img
        src={src}
        alt={alt}
        className="max-w-full h-auto rounded-lg border border-gray-200 block"
        onLoad={(e) => {
          const img = e.currentTarget;
          setNaturalSize({ width: img.naturalWidth, height: img.naturalHeight });
        }}
      />
      {naturalSize &&
        boxDetections.map((detection) => {
          const { x, y, width, height } = detection.boundingBox!;
          const left = (x / naturalSize.width) * 100;
          const top = (y / naturalSize.height) * 100;
          const boxWidth = (width / naturalSize.width) * 100;
          const boxHeight = (height / naturalSize.height) * 100;

          return (
            <div
              key={detection.id}
              className={`absolute border-2 ${boxColor(detection.label)}`}
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${boxWidth}%`,
                height: `${boxHeight}%`,
              }}
            >
              <span
                className={`absolute -top-6 left-0 whitespace-nowrap px-1.5 py-0.5 text-xs font-medium rounded text-white ${tagColor(
                  detection.label
                )}`}
              >
                {detection.label.replace(/_/g, " ")} {(detection.confidence * 100).toFixed(0)}%
              </span>
            </div>
          );
        })}
    </div>
  );
}
