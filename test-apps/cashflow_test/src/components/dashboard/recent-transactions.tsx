import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from '@/components/ui/card';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import { formatRelativeDate } from '@/lib/format';
import type { Transaction, Category, Account } from '@/types';

// ---------------------------------------------------------------------------
// RecentTransactions (TASK-033)
// Displays the most recent 10 transactions in a compact list.
// All monetary values are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface RecentTransactionsProps {
  transactions: Transaction[];
  categories: Category[];
  accounts: Account[];
}

export function RecentTransactions({
  transactions,
  categories,
  accounts,
}: RecentTransactionsProps) {
  // Sort by date descending, take first 10
  const recent = [...transactions]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 10);

  const categoryMap = new Map(categories.map((c) => [c.id, c]));
  const accountMap = new Map(accounts.map((a) => [a.id, a]));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Transactions</CardTitle>
        <CardAction>
          <Link
            to="/transactions"
            className="flex items-center gap-1 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            View All
            <ArrowRight className="h-4 w-4" />
          </Link>
        </CardAction>
      </CardHeader>
      <CardContent>
        {recent.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No transactions yet
          </p>
        ) : (
          <div className="space-y-3">
            {recent.map((txn) => {
              const category = categoryMap.get(txn.categoryId);
              const _account = accountMap.get(txn.accountId);
              const displayAmount =
                txn.type === 'expense' ? -txn.amount : txn.amount;

              return (
                <div
                  key={txn.id}
                  className="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted/50"
                >
                  {/* Category color dot */}
                  <div
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{
                      backgroundColor: category?.color ?? '#6b7280',
                    }}
                  />

                  {/* Description + category icon name */}
                  <div className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate text-sm font-medium text-foreground">
                      {txn.description}
                    </span>
                    <span className="truncate text-xs text-muted-foreground">
                      {category?.icon ?? 'tag'} &middot;{' '}
                      {category?.name ?? 'Uncategorized'}
                    </span>
                  </div>

                  {/* Date */}
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {formatRelativeDate(txn.date)}
                  </span>

                  {/* Amount */}
                  <CurrencyDisplay
                    amount={displayAmount}
                    className="shrink-0 text-sm"
                  />
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
