import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

// ---------------------------------------------------------------------------
// AnalyticsTabs (TASK-050)
// Tab bar for switching between analytics views.
// ---------------------------------------------------------------------------

interface AnalyticsTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function AnalyticsTabs({ activeTab, onTabChange }: AnalyticsTabsProps) {
  return (
    <Tabs value={activeTab} onValueChange={onTabChange} className="mb-6">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="income-expenses">Income & Expenses</TabsTrigger>
        <TabsTrigger value="categories">Categories</TabsTrigger>
        <TabsTrigger value="net-worth">Net Worth</TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
