import type { LucideIcon } from 'lucide-react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { formatPercent } from '@/lib/format';

// ---------------------------------------------------------------------------
// KPICard (TASK-031)
// Single KPI metric card with icon, value, and trend indicator.
// ---------------------------------------------------------------------------

interface KPICardProps {
  title: string;
  value: string;
  trend: number;
  trendDirection: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
  className?: string;
}

export function KPICard({
  title,
  value,
  trend,
  trendDirection,
  icon: Icon,
  className,
}: KPICardProps) {
  // Determine trend color: "up" means the value went up.
  // For expenses, the caller sets trendDirection='down' when trend is positive
  // (meaning expenses went down, which is good => green).
  const isPositiveTrend =
    trendDirection === 'up'
      ? trend >= 0
      : trendDirection === 'down'
        ? trend <= 0
        : true;

  const trendColor = isPositiveTrend ? 'text-positive' : 'text-negative';

  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <CardContent className="flex items-start justify-between">
        {/* Left: title, value, trend */}
        <div className="flex flex-col gap-1">
          <span className="text-sm text-muted-foreground">{title}</span>
          <span className="text-2xl font-bold tracking-tight text-foreground">
            {value}
          </span>

          {/* Trend badge */}
          <div className={cn('flex items-center gap-1 text-xs font-medium', trendColor)}>
            {trend > 0 ? (
              <ArrowUp className="h-3 w-3" />
            ) : trend < 0 ? (
              <ArrowDown className="h-3 w-3" />
            ) : null}
            <span>{formatPercent(trend)}</span>
            <span className="text-muted-foreground">vs last month</span>
          </div>
        </div>

        {/* Right: icon in accent circle */}
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </CardContent>
    </Card>
  );
}
