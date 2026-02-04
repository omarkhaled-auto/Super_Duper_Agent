"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { useAuth } from "@/contexts/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Sun, Moon, Monitor, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

// =============================================================================
// Settings Page -- User profile, theme preferences, account management
// =============================================================================

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  const initials = (user?.name ?? "U")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const themeOptions = [
    { value: "dark", label: "Dark", icon: Moon },
    { value: "light", label: "Light", icon: Sun },
    { value: "system", label: "System", icon: Monitor },
  ] as const;

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-8 max-w-2xl mx-auto">
      {/* ---- Page Header ---- */}
      <div>
        <h1 className="text-2xl font-heading font-bold tracking-tight text-text-primary">
          Settings
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Manage your account and preferences
        </p>
      </div>

      {/* ---- Profile Section ---- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Avatar size="lg">
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium text-text-primary">
                {user?.name ?? "Anonymous"}
              </p>
              <p className="text-xs text-text-tertiary">
                {user?.email ?? ""}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ---- Theme Section ---- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <Label className="text-sm text-text-secondary mb-3 block">
            Theme
          </Label>
          <div className="grid grid-cols-3 gap-2">
            {themeOptions.map((opt) => {
              const Icon = opt.icon;
              const isActive = theme === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setTheme(opt.value)}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-lg border p-4",
                    "transition-all duration-fast",
                    isActive
                      ? "border-primary bg-surface-selected text-text-primary"
                      : "border-border-subtle bg-surface-secondary text-text-tertiary hover:border-border-strong hover:text-text-primary",
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs font-medium">{opt.label}</span>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ---- Account Section ---- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-text-primary">
                Sign out
              </p>
              <p className="text-xs text-text-tertiary">
                End your current session
              </p>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => void logout()}
              className="gap-2"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
