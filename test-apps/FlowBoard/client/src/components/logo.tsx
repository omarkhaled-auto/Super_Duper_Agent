"use client";

import { Layers } from "lucide-react";
import { cn } from "@/lib/utils";

// =============================================================================
// FlowBoard Logo
//
// Geometric layers icon + "FlowBoard" wordmark in Space Grotesk.
// Three sizes: sm (nav), md (auth pages), lg (splash).
// =============================================================================

interface LogoProps {
  /** Visual size preset */
  size?: "sm" | "md" | "lg";
  /** Additional class names */
  className?: string;
  /** Whether to show the wordmark text alongside the icon */
  showText?: boolean;
}

const sizeMap = {
  sm: { icon: 18, text: "text-base", gap: "gap-2" },
  md: { icon: 24, text: "text-xl", gap: "gap-2.5" },
  lg: { icon: 32, text: "text-2xl", gap: "gap-3" },
} as const;

export function Logo({ size = "md", className, showText = true }: LogoProps) {
  const { icon, text, gap } = sizeMap[size];

  return (
    <div className={cn("flex items-center", gap, className)}>
      <div className="relative flex items-center justify-center">
        <div className="absolute inset-0 rounded-lg bg-primary/20 blur-sm" />
        <Layers
          size={icon}
          className="relative text-primary"
          strokeWidth={2.25}
        />
      </div>
      {showText && (
        <span
          className={cn(
            "font-heading font-bold tracking-tight text-text-primary",
            text,
          )}
        >
          FlowBoard
        </span>
      )}
    </div>
  );
}
