"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import {
  FolderKanban,
  Layers,
  Rocket,
  Bug,
  Lightbulb,
  Globe,
  Smartphone,
  Shield,
  Zap,
  BookOpen,
} from "lucide-react";

import { cn } from "@/lib/utils";
import api, { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

// =============================================================================
// Icon & Color options
// =============================================================================

interface IconOption {
  value: string;
  icon: React.ElementType;
  label: string;
}

const ICON_OPTIONS: IconOption[] = [
  { value: "folder", icon: FolderKanban, label: "Folder" },
  { value: "layers", icon: Layers, label: "Layers" },
  { value: "rocket", icon: Rocket, label: "Rocket" },
  { value: "bug", icon: Bug, label: "Bug" },
  { value: "lightbulb", icon: Lightbulb, label: "Idea" },
  { value: "globe", icon: Globe, label: "Web" },
  { value: "mobile", icon: Smartphone, label: "Mobile" },
  { value: "shield", icon: Shield, label: "Security" },
  { value: "zap", icon: Zap, label: "Lightning" },
  { value: "book", icon: BookOpen, label: "Docs" },
];

interface ColorOption {
  value: string;
  label: string;
  class: string;
}

const COLOR_OPTIONS: ColorOption[] = [
  { value: "violet", label: "Violet", class: "bg-violet-500" },
  { value: "blue", label: "Blue", class: "bg-blue-500" },
  { value: "green", label: "Green", class: "bg-green-500" },
  { value: "teal", label: "Teal", class: "bg-teal-500" },
  { value: "cyan", label: "Cyan", class: "bg-cyan-500" },
  { value: "orange", label: "Orange", class: "bg-orange-500" },
  { value: "red", label: "Red", class: "bg-red-500" },
  { value: "pink", label: "Pink", class: "bg-pink-500" },
  { value: "yellow", label: "Yellow", class: "bg-yellow-500" },
  { value: "indigo", label: "Indigo", class: "bg-indigo-500" },
];

// =============================================================================
// CreateProjectDialog Component
// =============================================================================

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated?: () => void;
}

export function CreateProjectDialog({
  open,
  onOpenChange,
  onProjectCreated,
}: CreateProjectDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [icon, setIcon] = useState("folder");
  const [color, setColor] = useState("violet");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // ---------------------------------------------------------------------------
  // Validation
  // ---------------------------------------------------------------------------
  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = "Project name is required";
    } else if (name.trim().length < 2) {
      newErrors.name = "Name must be at least 2 characters";
    } else if (name.trim().length > 50) {
      newErrors.name = "Name must be under 50 characters";
    }

    if (description.length > 200) {
      newErrors.description = "Description must be under 200 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  // ---------------------------------------------------------------------------
  // Submit handler
  // ---------------------------------------------------------------------------
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      await api.post("/projects", {
        name: name.trim(),
        description: description.trim() || undefined,
        icon,
        color,
      });

      toast.success("Project created", {
        description: `"${name.trim()}" has been created successfully.`,
      });

      // Reset form
      setName("");
      setDescription("");
      setIcon("folder");
      setColor("violet");
      setErrors({});

      onOpenChange(false);
      onProjectCreated?.();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.errors) {
          const fieldErrors: Record<string, string> = {};
          err.errors.forEach(({ field, message }) => {
            fieldErrors[field] = message;
          });
          setErrors(fieldErrors);
        }
        toast.error("Failed to create project", {
          description: err.message,
        });
      } else {
        toast.error("Something went wrong", {
          description: "Please try again.",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Reset state when dialog closes
  // ---------------------------------------------------------------------------
  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setName("");
      setDescription("");
      setIcon("folder");
      setColor("violet");
      setErrors({});
    }
    onOpenChange(nextOpen);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create Project</DialogTitle>
            <DialogDescription>
              Add a new project to organize your team&apos;s work.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-6 space-y-5">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="project-name">Name</Label>
              <Input
                id="project-name"
                placeholder="e.g. Website Redesign"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (errors.name) {
                    setErrors((prev) => {
                      const next = { ...prev };
                      delete next.name;
                      return next;
                    });
                  }
                }}
                error={!!errors.name}
                autoFocus
              />
              {errors.name && (
                <p className="text-xs text-error">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="project-description">
                Description{" "}
                <span className="text-text-quaternary font-normal">
                  (optional)
                </span>
              </Label>
              <Input
                id="project-description"
                placeholder="Brief description of the project"
                value={description}
                onChange={(e) => {
                  setDescription(e.target.value);
                  if (errors.description) {
                    setErrors((prev) => {
                      const next = { ...prev };
                      delete next.description;
                      return next;
                    });
                  }
                }}
                error={!!errors.description}
              />
              {errors.description && (
                <p className="text-xs text-error">{errors.description}</p>
              )}
              <p className="text-xs text-text-quaternary">
                {description.length}/200
              </p>
            </div>

            {/* Icon picker */}
            <div className="space-y-2">
              <Label>Icon</Label>
              <div className="flex flex-wrap gap-1.5">
                {ICON_OPTIONS.map((opt) => {
                  const IconComp = opt.icon;
                  const isSelected = icon === opt.value;

                  return (
                    <button
                      key={opt.value}
                      type="button"
                      title={opt.label}
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-md",
                        "transition-all duration-fast",
                        "border",
                        isSelected
                          ? "border-primary bg-violet-muted text-primary"
                          : "border-transparent bg-surface-tertiary text-text-tertiary hover:text-text-secondary hover:bg-surface-hover",
                      )}
                      onClick={() => setIcon(opt.value)}
                    >
                      <IconComp className="h-4 w-4" />
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Color picker */}
            <div className="space-y-2">
              <Label>Color</Label>
              <div className="flex flex-wrap gap-2">
                {COLOR_OPTIONS.map((opt) => {
                  const isSelected = color === opt.value;

                  return (
                    <button
                      key={opt.value}
                      type="button"
                      title={opt.label}
                      className={cn(
                        "h-6 w-6 rounded-full transition-all duration-fast",
                        opt.class,
                        isSelected
                          ? "ring-2 ring-offset-2 ring-offset-background ring-text-primary scale-110"
                          : "hover:scale-110 opacity-70 hover:opacity-100",
                      )}
                      onClick={() => setColor(opt.value)}
                    >
                      <span className="sr-only">{opt.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="ghost"
              onClick={() => handleOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting}>
              Create Project
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
