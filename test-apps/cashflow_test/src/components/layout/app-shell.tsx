import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useSettingsStore } from '@/stores/use-settings-store';
import { useKeyboardShortcut } from '@/hooks/use-keyboard-shortcut';
import { cn } from '@/lib/utils';
import { Sidebar } from '@/components/layout/sidebar';
import { TopBar } from '@/components/layout/top-bar';
import { MobileNav } from '@/components/layout/mobile-nav';
import { CommandMenu } from '@/components/layout/command-menu';

export function AppShell() {
  const sidebarCollapsed = useSettingsStore((s) => s.sidebarCollapsed);
  const [commandOpen, setCommandOpen] = useState(false);

  useKeyboardShortcut('k', () => setCommandOpen(true), { metaKey: true });

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <TopBar onOpenSearch={() => setCommandOpen(true)} />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-20 md:pb-6">
          <Outlet />
        </main>
      </div>

      {/* Mobile navigation */}
      <MobileNav />

      {/* Command palette (global) */}
      <CommandMenu open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
