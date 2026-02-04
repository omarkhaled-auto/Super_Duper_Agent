import type { UserPreferences } from '@/types';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Moon, Sun, Monitor } from 'lucide-react';

// ---------------------------------------------------------------------------
// General Settings (TASK-058)
// Theme, currency, and date format preferences.
// ---------------------------------------------------------------------------

interface GeneralSettingsProps {
  settings: UserPreferences;
  onUpdate: (key: string, value: any) => void;
}

const CURRENCIES = [
  { value: 'USD', label: 'USD - US Dollar' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'GBP', label: 'GBP - British Pound' },
  { value: 'CAD', label: 'CAD - Canadian Dollar' },
  { value: 'AUD', label: 'AUD - Australian Dollar' },
] as const;

const DATE_FORMATS = [
  { value: 'MMM d, yyyy', label: 'MMM d, yyyy (Jan 1, 2025)' },
  { value: 'dd/MM/yyyy', label: 'dd/MM/yyyy (01/01/2025)' },
  { value: 'yyyy-MM-dd', label: 'yyyy-MM-dd (2025-01-01)' },
] as const;

const THEMES = [
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'system', label: 'System', icon: Monitor },
] as const;

export function GeneralSettings({ settings, onUpdate }: GeneralSettingsProps) {
  return (
    <div className="space-y-6">
      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>
            Choose how CashFlow looks. Select a theme or let your system decide.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Label className="mb-3">Appearance</Label>
          <div className="flex gap-2">
            {THEMES.map(({ value, label, icon: Icon }) => (
              <Button
                key={value}
                variant={settings.theme === value ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => onUpdate('theme', value)}
              >
                <Icon className="size-4" />
                {label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Currency */}
      <Card>
        <CardHeader>
          <CardTitle>Currency</CardTitle>
          <CardDescription>
            Set the default currency used across the app for displaying amounts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Label className="mb-3">Default Currency</Label>
          <Select
            value={settings.currency}
            onValueChange={(value) => onUpdate('currency', value)}
          >
            <SelectTrigger className="w-full max-w-xs">
              <SelectValue placeholder="Select currency" />
            </SelectTrigger>
            <SelectContent>
              {CURRENCIES.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Date Format */}
      <Card>
        <CardHeader>
          <CardTitle>Date Format</CardTitle>
          <CardDescription>
            Choose how dates are displayed throughout the application.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Label className="mb-3">Format</Label>
          <Select
            value={settings.dateFormat}
            onValueChange={(value) => onUpdate('dateFormat', value)}
          >
            <SelectTrigger className="w-full max-w-xs">
              <SelectValue placeholder="Select date format" />
            </SelectTrigger>
            <SelectContent>
              {DATE_FORMATS.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>
    </div>
  );
}
