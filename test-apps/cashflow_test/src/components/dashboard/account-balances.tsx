import {
  Landmark,
  PiggyBank,
  CreditCard,
  TrendingUp,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import type { Account, AccountType } from '@/types';

// ---------------------------------------------------------------------------
// AccountBalances (TASK-035)
// Grouped list of accounts by type with balances.
// All monetary values are INTEGER CENTS.
// ---------------------------------------------------------------------------

interface AccountBalancesProps {
  accounts: Account[];
}

const typeLabels: Record<AccountType, string> = {
  checking: 'Checking',
  savings: 'Savings',
  credit: 'Credit Cards',
  investment: 'Investments',
};

const typeIcons: Record<AccountType, React.ComponentType<{ className?: string }>> = {
  checking: Landmark,
  savings: PiggyBank,
  credit: CreditCard,
  investment: TrendingUp,
};

/** Group accounts by their type, preserving only non-empty groups. */
function groupByType(accounts: Account[]): Map<AccountType, Account[]> {
  const groups = new Map<AccountType, Account[]>();
  const order: AccountType[] = ['checking', 'savings', 'credit', 'investment'];

  for (const type of order) {
    const filtered = accounts.filter((a) => a.type === type && a.isActive);
    if (filtered.length > 0) {
      groups.set(type, filtered);
    }
  }
  return groups;
}

export function AccountBalances({ accounts }: AccountBalancesProps) {
  const groups = groupByType(accounts);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Balances</CardTitle>
      </CardHeader>
      <CardContent>
        {groups.size === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No accounts added
          </p>
        ) : (
          <div className="space-y-5">
            {Array.from(groups.entries()).map(([type, accts]) => {
              const TypeIcon = typeIcons[type];
              return (
                <div key={type} className="space-y-2">
                  {/* Group header */}
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <TypeIcon className="h-3.5 w-3.5" />
                    {typeLabels[type]}
                  </div>

                  {/* Account rows */}
                  {accts.map((account) => (
                    <div
                      key={account.id}
                      className="flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-muted/50"
                    >
                      <div className="flex min-w-0 flex-col">
                        <span className="truncate text-sm font-medium text-foreground">
                          {account.name}
                        </span>
                        <span className="truncate text-xs text-muted-foreground">
                          {account.institution}
                        </span>
                      </div>
                      <CurrencyDisplay
                        amount={account.balance}
                        className="shrink-0 text-sm"
                      />
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
