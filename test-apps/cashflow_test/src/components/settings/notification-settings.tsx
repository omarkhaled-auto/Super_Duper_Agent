import type { UserPreferences } from '@/types';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

// ---------------------------------------------------------------------------
// Notification Settings (TASK-060)
// Toggle switches for budget alerts and goal milestones.
// ---------------------------------------------------------------------------

interface NotificationSettingsProps {
  settings: UserPreferences;
  onUpdate: (key: string, value: any) => void;
}

export function NotificationSettings({
  settings,
  onUpdate,
}: NotificationSettingsProps) {
  // These preferences are stored as part of UserPreferences extensions.
  // Since UserPreferences doesn't have notification fields in the type yet,
  // we treat them as extra keys and cast through `any` on the settings object.
  const budgetAlerts = (settings as any).budgetAlerts ?? true;
  const goalNotifications = (settings as any).goalNotifications ?? true;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>
            Configure which notifications you receive within the app.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Budget Alert Notifications */}
          <div className="flex items-start gap-3">
            <Checkbox
              id="budget-alerts"
              checked={budgetAlerts}
              onCheckedChange={(checked) =>
                onUpdate('budgetAlerts', Boolean(checked))
              }
            />
            <div className="space-y-1">
              <Label htmlFor="budget-alerts" className="cursor-pointer">
                Budget alert notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Receive alerts when your spending approaches or exceeds budget
                limits.
              </p>
            </div>
          </div>

          {/* Goal Milestone Notifications */}
          <div className="flex items-start gap-3">
            <Checkbox
              id="goal-notifications"
              checked={goalNotifications}
              onCheckedChange={(checked) =>
                onUpdate('goalNotifications', Boolean(checked))
              }
            />
            <div className="space-y-1">
              <Label htmlFor="goal-notifications" className="cursor-pointer">
                Goal milestone notifications
              </Label>
              <p className="text-sm text-muted-foreground">
                Get notified when you reach milestones on your savings goals
                (25%, 50%, 75%, 100%).
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
