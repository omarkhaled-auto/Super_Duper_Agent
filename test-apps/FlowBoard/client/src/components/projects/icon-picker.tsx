"use client";

import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Briefcase,
  Bug,
  Calendar,
  Camera,
  Cloud,
  Code,
  Compass,
  Cpu,
  Database,
  FileText,
  Flame,
  Folder,
  Gamepad2,
  Globe,
  Heart,
  Home,
  Image,
  Layers,
  Layout,
  Lightbulb,
  Lock,
  Mail,
  Map,
  MessageSquare,
  Monitor,
  Music,
  Package,
  Palette,
  PenTool,
  Phone,
  Rocket,
  Search,
  Settings,
  Shield,
  ShoppingCart,
  Star,
  Target,
  Terminal,
  Truck,
  Users,
  Video,
  Wand2,
  Zap,
  BookOpen,
  BarChart3,
  type LucideIcon,
} from "lucide-react";

// =============================================================================
// IconPicker — grid of Lucide icons for project icon selection
// =============================================================================

/** Registry of available project icons, keyed by a stable identifier. */
const PROJECT_ICONS: Record<string, { icon: LucideIcon; label: string }> = {
  briefcase: { icon: Briefcase, label: "Briefcase" },
  bug: { icon: Bug, label: "Bug" },
  calendar: { icon: Calendar, label: "Calendar" },
  camera: { icon: Camera, label: "Camera" },
  cloud: { icon: Cloud, label: "Cloud" },
  code: { icon: Code, label: "Code" },
  compass: { icon: Compass, label: "Compass" },
  cpu: { icon: Cpu, label: "CPU" },
  database: { icon: Database, label: "Database" },
  "file-text": { icon: FileText, label: "Document" },
  flame: { icon: Flame, label: "Flame" },
  folder: { icon: Folder, label: "Folder" },
  gamepad: { icon: Gamepad2, label: "Gamepad" },
  globe: { icon: Globe, label: "Globe" },
  heart: { icon: Heart, label: "Heart" },
  home: { icon: Home, label: "Home" },
  image: { icon: Image, label: "Image" },
  layers: { icon: Layers, label: "Layers" },
  layout: { icon: Layout, label: "Layout" },
  lightbulb: { icon: Lightbulb, label: "Lightbulb" },
  lock: { icon: Lock, label: "Lock" },
  mail: { icon: Mail, label: "Mail" },
  map: { icon: Map, label: "Map" },
  message: { icon: MessageSquare, label: "Message" },
  monitor: { icon: Monitor, label: "Monitor" },
  music: { icon: Music, label: "Music" },
  package: { icon: Package, label: "Package" },
  palette: { icon: Palette, label: "Palette" },
  "pen-tool": { icon: PenTool, label: "Pen Tool" },
  phone: { icon: Phone, label: "Phone" },
  rocket: { icon: Rocket, label: "Rocket" },
  search: { icon: Search, label: "Search" },
  settings: { icon: Settings, label: "Settings" },
  shield: { icon: Shield, label: "Shield" },
  "shopping-cart": { icon: ShoppingCart, label: "Shopping Cart" },
  star: { icon: Star, label: "Star" },
  target: { icon: Target, label: "Target" },
  terminal: { icon: Terminal, label: "Terminal" },
  truck: { icon: Truck, label: "Truck" },
  users: { icon: Users, label: "Users" },
  video: { icon: Video, label: "Video" },
  wand: { icon: Wand2, label: "Wand" },
  zap: { icon: Zap, label: "Zap" },
  "book-open": { icon: BookOpen, label: "Book" },
  "bar-chart": { icon: BarChart3, label: "Chart" },
};

const ICON_KEYS = Object.keys(PROJECT_ICONS);

interface IconPickerProps {
  /** Currently selected icon key (e.g. "rocket"). */
  value: string | null;
  /** Called when the user selects an icon. */
  onChange: (iconKey: string) => void;
  /** Optional project color for the selected icon tint. */
  color?: string | null;
  /** Optional additional class name on the wrapper. */
  className?: string;
}

export function IconPicker({
  value,
  onChange,
  color,
  className,
}: IconPickerProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return ICON_KEYS;
    const query = search.toLowerCase().trim();
    return ICON_KEYS.filter((key) => {
      const entry = PROJECT_ICONS[key];
      if (!entry) return false;
      return (
        key.includes(query) ||
        entry.label.toLowerCase().includes(query)
      );
    });
  }, [search]);

  return (
    <div className={cn("space-y-3", className)}>
      {/* Search input */}
      <Input
        placeholder="Search icons..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        inputSize="sm"
        aria-label="Filter icons"
      />

      {/* Icon grid */}
      <ScrollArea className="h-[200px]">
        <div
          className="grid grid-cols-8 gap-1.5 pr-3"
          role="radiogroup"
          aria-label="Project icon"
        >
          {filtered.map((key) => {
            const entry = PROJECT_ICONS[key];
            if (!entry) return null;
            const Icon = entry.icon;
            const isSelected = value === key;

            return (
              <button
                key={key}
                type="button"
                role="radio"
                aria-checked={isSelected}
                aria-label={entry.label}
                title={entry.label}
                onClick={() => onChange(key)}
                className={cn(
                  "flex items-center justify-center rounded-md p-2",
                  "transition-all duration-fast",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 ring-offset-background",
                  "hover:bg-surface-hover",
                  isSelected
                    ? "bg-primary/10 ring-1 ring-primary"
                    : "text-text-secondary hover:text-text-primary",
                )}
              >
                <Icon
                  className="h-5 w-5"
                  style={
                    isSelected && color
                      ? { color }
                      : undefined
                  }
                  aria-hidden="true"
                />
              </button>
            );
          })}

          {filtered.length === 0 && (
            <p className="col-span-8 py-6 text-center text-sm text-text-tertiary">
              No icons match your search.
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

/**
 * Resolve an icon key to the corresponding Lucide icon component.
 * Returns `null` if the key is not found.
 */
export function getProjectIcon(key: string | null | undefined): LucideIcon | null {
  if (!key) return null;
  return PROJECT_ICONS[key]?.icon ?? null;
}

export { PROJECT_ICONS };
