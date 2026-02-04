import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { useSettingsStore } from '@/stores/use-settings-store';
import { useCategoryStore } from '@/stores/use-category-store';
import { useAccountStore } from '@/stores/use-account-store';
import { useTransactionStore } from '@/stores/use-transaction-store';
import { useBudgetStore } from '@/stores/use-budget-store';
import { useGoalStore } from '@/stores/use-goal-store';
import { useRecurringStore } from '@/stores/use-recurring-store';
import { generateSeedData } from '@/data/seed';
import { PageHeader } from '@/components/shared/page-header';
import { SettingsTabs } from '@/components/settings/settings-tabs';
import { GeneralSettings } from '@/components/settings/general-settings';
import { CategorySettings } from '@/components/settings/category-settings';
import { DataSettings } from '@/components/settings/data-settings';
import { NotificationSettings } from '@/components/settings/notification-settings';

// =============================================================================
// Settings Page (TASK-057 through TASK-060)
// Orchestrates all settings sub-sections with tabbed navigation.
// =============================================================================

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  // --- Settings store ---
  const settingsStore = useSettingsStore();
  const settings = {
    theme: settingsStore.theme,
    currency: settingsStore.currency,
    locale: settingsStore.locale,
    dateFormat: settingsStore.dateFormat,
    sidebarCollapsed: settingsStore.sidebarCollapsed,
  };

  // --- Category store ---
  const categories = useCategoryStore((s) => s.categories);
  const addCategory = useCategoryStore((s) => s.addCategory);
  const updateCategory = useCategoryStore((s) => s.updateCategory);
  const deleteCategory = useCategoryStore((s) => s.deleteCategory);

  // --- All stores for export ---
  const accounts = useAccountStore((s) => s.accounts);
  const transactions = useTransactionStore((s) => s.transactions);
  const budgets = useBudgetStore((s) => s.budgets);
  const goals = useGoalStore((s) => s.goals);
  const recurringTransactions = useRecurringStore(
    (s) => s.recurringTransactions,
  );

  // ---------------------------------------------------------------------------
  // General settings handler
  // ---------------------------------------------------------------------------
  const handleSettingsUpdate = useCallback(
    (key: string, value: any) => {
      switch (key) {
        case 'theme':
          settingsStore.setTheme(value);
          toast.success(`Theme changed to ${value}`);
          break;
        case 'currency':
          settingsStore.setCurrency(value);
          toast.success(`Currency changed to ${value}`);
          break;
        case 'dateFormat':
          settingsStore.setDateFormat(value);
          toast.success('Date format updated');
          break;
        default:
          break;
      }
    },
    [settingsStore],
  );

  // ---------------------------------------------------------------------------
  // Category CRUD handlers
  // ---------------------------------------------------------------------------
  const handleAddCategory = useCallback(
    (data: any) => {
      addCategory(data);
      toast.success('Category created');
    },
    [addCategory],
  );

  const handleEditCategory = useCallback(
    (id: string, updates: any) => {
      updateCategory(id, updates);
      toast.success('Category updated');
    },
    [updateCategory],
  );

  const handleDeleteCategory = useCallback(
    (id: string) => {
      deleteCategory(id);
      toast.success('Category deleted');
    },
    [deleteCategory],
  );

  // ---------------------------------------------------------------------------
  // Data export handler
  // ---------------------------------------------------------------------------
  const handleExport = useCallback(() => {
    try {
      const exportData = {
        exportedAt: new Date().toISOString(),
        version: '1.0',
        settings,
        accounts,
        transactions,
        budgets,
        categories,
        goals,
        recurringTransactions,
      };

      const json = JSON.stringify(exportData, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `cashflow-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success('Data exported successfully');
    } catch {
      toast.error('Failed to export data');
    }
  }, [
    settings,
    accounts,
    transactions,
    budgets,
    categories,
    goals,
    recurringTransactions,
  ]);

  // ---------------------------------------------------------------------------
  // Data reset handler
  // ---------------------------------------------------------------------------
  const handleReset = useCallback(() => {
    try {
      generateSeedData();
      toast.success('Data reset to demo data');
    } catch {
      toast.error('Failed to reset data');
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Notification settings handler
  // ---------------------------------------------------------------------------
  const handleNotificationUpdate = useCallback(
    (key: string, value: any) => {
      // Notification preferences can be stored via the same settings pattern.
      // For now we show a toast; the notification-settings component manages
      // its own state via the settings object passed to it.
      toast.success(
        `${key === 'budgetAlerts' ? 'Budget alerts' : 'Goal notifications'} ${value ? 'enabled' : 'disabled'}`,
      );
    },
    [],
  );

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Manage your preferences, categories, and data"
      />

      <SettingsTabs activeTab={activeTab} onTabChange={setActiveTab} />

      <div className="mt-6">
        {activeTab === 'general' && (
          <GeneralSettings
            settings={settings}
            onUpdate={handleSettingsUpdate}
          />
        )}

        {activeTab === 'categories' && (
          <CategorySettings
            categories={categories}
            onAdd={handleAddCategory}
            onEdit={handleEditCategory}
            onDelete={handleDeleteCategory}
          />
        )}

        {activeTab === 'data' && (
          <DataSettings onExport={handleExport} onReset={handleReset} />
        )}

        {activeTab === 'notifications' && (
          <NotificationSettings
            settings={settings}
            onUpdate={handleNotificationUpdate}
          />
        )}
      </div>
    </div>
  );
}
