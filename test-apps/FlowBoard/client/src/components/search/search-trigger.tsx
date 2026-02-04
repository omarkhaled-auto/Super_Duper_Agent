"use client";

import React from "react";
import { Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// =============================================================================
// SearchTrigger — Button in the top bar that opens the command palette
//
// Shows a magnifying glass icon, "Search..." placeholder text, and a Cmd+K
// keyboard shortcut badge. Clicking opens the command palette.
// =============================================================================

interface SearchTriggerProps {
  onClick: () => void;
  className?: string;
}

export function SearchTrigger({ onClick, className }: SearchTriggerProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "gap-2 text-text-tertiary hover:text-text-primary",
            className,
          )}
          onClick={onClick}
        >
          <Search className="h-4 w-4" />
          <span className="hidden lg:inline text-xs text-text-quaternary">
            Search...
          </span>
          <kbd className="hidden lg:inline-flex h-5 items-center gap-0.5 rounded border border-edge-subtle bg-surface-secondary px-1.5 font-mono text-[10px] text-text-quaternary">
            <span className="text-xs">&#8984;</span>K
          </kbd>
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        Search{" "}
        <kbd className="ml-1 font-mono text-[10px]">Cmd+K</kbd>
      </TooltipContent>
    </Tooltip>
  );
}
