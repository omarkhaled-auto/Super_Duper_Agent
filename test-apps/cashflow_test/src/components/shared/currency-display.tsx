import { formatCurrency } from '@/lib/format';
import { cn } from '@/lib/utils';

interface CurrencyDisplayProps {
  amount: number; // integer cents
  className?: string;
}

export function CurrencyDisplay({ amount, className }: CurrencyDisplayProps) {
  const isPositive = amount >= 0;

  return (
    <span
      className={cn(
        'font-mono tabular-nums',
        isPositive ? 'text-positive' : 'text-negative',
        className,
      )}
    >
      {formatCurrency(amount)}
    </span>
  );
}
