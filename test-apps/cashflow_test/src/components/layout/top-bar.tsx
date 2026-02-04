import { useLocation } from 'react-router-dom';
import { Search, Sun, Moon, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSettingsStore } from '@/stores/use-settings-store';

const pageTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/transactions': 'Transactions',
  '/budgets': 'Budgets',
  '/accounts': 'Accounts',
  '/analytics': 'Analytics',
  '/goals': 'Goals',
  '/settings': 'Settings',
};

interface TopBarProps {
  onOpenSearch: () => void;
}

export function TopBar({ onOpenSearch }: TopBarProps) {
  const location = useLocation();
  const theme = useSettingsStore((s) => s.theme);
  const setTheme = useSettingsStore((s) => s.setTheme);

  const title = pageTitles[location.pathname] ?? 'CashFlow';

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background px-4 md:px-6">
      {/* Page title */}
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>

      {/* Right section */}
      <div className="flex items-center gap-2">
        {/* Search trigger */}
        <Button
          variant="outline"
          className="hidden sm:flex items-center gap-2 text-muted-foreground"
          onClick={onOpenSearch}
        >
          <Search className="h-4 w-4" />
          <span className="text-sm">Search...</span>
          <kbd className="pointer-events-none ml-2 hidden select-none rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground sm:inline-block">
            {"\u2318"}K
          </kbd>
        </Button>

        {/* Mobile search button */}
        <Button
          variant="ghost"
          size="icon"
          className="sm:hidden"
          onClick={onOpenSearch}
        >
          <Search className="h-4 w-4" />
        </Button>

        {/* Theme toggle */}
        <Button variant="ghost" size="icon" onClick={toggleTheme}>
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>

        {/* Notifications placeholder */}
        <Button variant="ghost" size="icon">
          <Bell className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
