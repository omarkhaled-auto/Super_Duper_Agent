import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings, Tag, Database, Bell } from 'lucide-react';

// ---------------------------------------------------------------------------
// Settings Tabs (TASK-057)
// Tab navigation for the Settings page.
// ---------------------------------------------------------------------------

interface SettingsTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const TABS = [
  { value: 'general', label: 'General', icon: Settings },
  { value: 'categories', label: 'Categories', icon: Tag },
  { value: 'data', label: 'Data', icon: Database },
  { value: 'notifications', label: 'Notifications', icon: Bell },
] as const;

export function SettingsTabs({ activeTab, onTabChange }: SettingsTabsProps) {
  return (
    <Tabs value={activeTab} onValueChange={onTabChange}>
      <TabsList>
        {TABS.map(({ value, label, icon: Icon }) => (
          <TabsTrigger key={value} value={value}>
            <Icon className="size-4" />
            {label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
