import { AccountCard } from './account-card';
import { formatCurrency } from '@/lib/format';
import type { Account, AccountType } from '@/types';

interface AccountGroupProps {
  type: AccountType;
  label: string;
  accounts: Account[];
  onEdit: (a: Account) => void;
  onDelete: (id: string) => void;
}

export function AccountGroup({
  type,
  label,
  accounts,
  onEdit,
  onDelete,
}: AccountGroupProps) {
  if (accounts.length === 0) return null;

  const subtotal = accounts.reduce((sum, a) => sum + a.balance, 0);

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">{label}</h2>
        <span className="text-sm font-medium text-muted-foreground font-mono tabular-nums">
          {formatCurrency(subtotal)}
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {accounts.map((account) => (
          <AccountCard
            key={account.id}
            account={account}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>
    </section>
  );
}
