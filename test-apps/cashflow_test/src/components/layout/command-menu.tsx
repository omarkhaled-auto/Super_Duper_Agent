import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ArrowLeftRight,
  PieChart,
  Wallet,
  BarChart3,
  Target,
  Settings,
  Plus,
  FileDown,
} from 'lucide-react';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from '@/components/ui/command';
import { useKeyboardShortcut } from '@/hooks/use-keyboard-shortcut';

const pages = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { label: 'Transactions', icon: ArrowLeftRight, path: '/transactions' },
  { label: 'Budgets', icon: PieChart, path: '/budgets' },
  { label: 'Accounts', icon: Wallet, path: '/accounts' },
  { label: 'Analytics', icon: BarChart3, path: '/analytics' },
  { label: 'Goals', icon: Target, path: '/goals' },
  { label: 'Settings', icon: Settings, path: '/settings' },
] as const;

const quickActions = [
  { label: 'Add Transaction', icon: Plus, path: '/transactions' },
  { label: 'Add Budget', icon: Plus, path: '/budgets' },
  { label: 'Add Account', icon: Plus, path: '/accounts' },
  { label: 'Export Data', icon: FileDown, path: '/settings' },
] as const;

interface CommandMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandMenu({ open, onOpenChange }: CommandMenuProps) {
  const navigate = useNavigate();

  const handleSelect = (path: string) => {
    onOpenChange(false);
    navigate(path);
  };

  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Command Menu"
      description="Search for pages or actions..."
    >
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Pages">
          {pages.map((page) => {
            const Icon = page.icon;
            return (
              <CommandItem
                key={page.path}
                onSelect={() => handleSelect(page.path)}
              >
                <Icon className="h-4 w-4" />
                <span>{page.label}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Quick Actions">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <CommandItem
                key={action.label}
                onSelect={() => handleSelect(action.path)}
              >
                <Icon className="h-4 w-4" />
                <span>{action.label}</span>
              </CommandItem>
            );
          })}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
