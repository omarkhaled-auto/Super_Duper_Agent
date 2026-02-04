"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

// =============================================================================
// ColorPicker — predefined color palette matching the FlowBoard design system
// =============================================================================

/** Predefined project colors with human-readable labels. */
const PROJECT_COLORS = [
  { value: "#7c3aed", label: "Violet" },
  { value: "#6366f1", label: "Indigo" },
  { value: "#3b82f6", label: "Blue" },
  { value: "#0ea5e9", label: "Sky" },
  { value: "#06b6d4", label: "Cyan" },
  { value: "#14b8a6", label: "Teal" },
  { value: "#10b981", label: "Emerald" },
  { value: "#22c55e", label: "Green" },
  { value: "#84cc16", label: "Lime" },
  { value: "#eab308", label: "Yellow" },
  { value: "#f97316", label: "Orange" },
  { value: "#ef4444", label: "Red" },
  { value: "#ec4899", label: "Pink" },
  { value: "#f43f5e", label: "Rose" },
  { value: "#8b5cf6", label: "Purple" },
  { value: "#64748b", label: "Slate" },
] as const;

export type ProjectColor = (typeof PROJECT_COLORS)[number]["value"];

interface ColorPickerProps {
  /** Currently selected color hex value. */
  value: string | null;
  /** Called when the user picks a color. */
  onChange: (color: string) => void;
  /** Optional additional class name on the wrapper. */
  className?: string;
}

export function ColorPicker({ value, onChange, className }: ColorPickerProps) {
  return (
    <div
      className={cn("flex flex-wrap gap-2", className)}
      role="radiogroup"
      aria-label="Project color"
    >
      {PROJECT_COLORS.map((color) => {
        const isSelected = value === color.value;
        return (
          <button
            key={color.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            aria-label={color.label}
            title={color.label}
            onClick={() => onChange(color.value)}
            className={cn(
              "relative h-8 w-8 rounded-full transition-all duration-fast",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background",
              "hover:scale-110 active:scale-95",
              isSelected && "ring-2 ring-offset-2 ring-offset-background",
            )}
            style={{
              backgroundColor: color.value,
              // Use the same color for the ring when selected
              ...(isSelected ? { "--tw-ring-color": color.value } as React.CSSProperties : {}),
            }}
          >
            {isSelected && (
              <Check
                className="absolute inset-0 m-auto h-4 w-4 text-white drop-shadow-sm"
                strokeWidth={3}
                aria-hidden="true"
              />
            )}
          </button>
        );
      })}
    </div>
  );
}

export { PROJECT_COLORS };
