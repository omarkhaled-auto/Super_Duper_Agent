import { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ConfirmDialog } from '@/components/shared/confirm-dialog';
import { Download, RotateCcw } from 'lucide-react';

// ---------------------------------------------------------------------------
// Data Settings (TASK-059)
// Export and reset functionality for user data.
// ---------------------------------------------------------------------------

interface DataSettingsProps {
  onExport: () => void;
  onReset: () => void;
}

export function DataSettings({ onExport, onReset }: DataSettingsProps) {
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetConfirmText, setResetConfirmText] = useState('');

  const handleConfirmReset = () => {
    onReset();
    setResetDialogOpen(false);
    setResetConfirmText('');
  };

  return (
    <div className="space-y-6">
      {/* Export */}
      <Card>
        <CardHeader>
          <CardTitle>Export Data</CardTitle>
          <CardDescription>
            Download all your data as a JSON file. This includes accounts,
            transactions, budgets, categories, goals, and recurring rules.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={onExport}>
            <Download className="size-4" />
            Export JSON
          </Button>
        </CardContent>
      </Card>

      {/* Reset to Demo Data */}
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">
            Reset to Demo Data
          </CardTitle>
          <CardDescription>
            This is a destructive action. It will replace ALL your current data
            (accounts, transactions, budgets, categories, goals, and recurring
            rules) with the default demo data set. This cannot be undone.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={() => setResetDialogOpen(true)}
          >
            <RotateCcw className="size-4" />
            Reset to Demo Data
          </Button>
        </CardContent>
      </Card>

      {/* Reset Confirmation Dialog */}
      <ConfirmDialog
        open={resetDialogOpen}
        onClose={() => {
          setResetDialogOpen(false);
          setResetConfirmText('');
        }}
        onConfirm={handleConfirmReset}
        title="Reset All Data"
        description="This will replace all your data with demo data. This action cannot be undone. Are you sure you want to continue?"
        confirmLabel="Reset All Data"
        variant="destructive"
      />
    </div>
  );
}
