import { Target, PiggyBank, TrendingUp } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CurrencyDisplay } from '@/components/shared/currency-display';

// ---------------------------------------------------------------------------
// GoalSummaryBar (TASK-056)
// Three summary stat cards: active goals count, total saved, total target.
// All monetary amounts are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface GoalSummaryBarProps {
  activeCount: number;
  totalSaved: number; // cents
  totalTarget: number; // cents
}

export function GoalSummaryBar({
  activeCount,
  totalSaved,
  totalTarget,
}: GoalSummaryBarProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      {/* Active Goals */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Goals
            </CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-foreground">{activeCount}</p>
        </CardContent>
      </Card>

      {/* Total Saved */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Saved
            </CardTitle>
            <PiggyBank className="h-4 w-4 text-positive" />
          </div>
        </CardHeader>
        <CardContent>
          <CurrencyDisplay amount={totalSaved} className="text-2xl font-bold" />
        </CardContent>
      </Card>

      {/* Total Target */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Target
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <CurrencyDisplay amount={totalTarget} className="text-2xl font-bold" />
        </CardContent>
      </Card>
    </div>
  );
}
