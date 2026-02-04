import { useMemo, useState } from 'react';
import { Plus, Landmark } from 'lucide-react';
import { toast } from 'sonner';
import { useAccountStore } from '@/stores/use-account-store';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { ConfirmDialog } from '@/components/shared/confirm-dialog';
import { NetWorthSummary } from '@/components/accounts/net-worth-summary';
import { AccountGroup } from '@/components/accounts/account-group';
import { AccountModal } from '@/components/accounts/account-modal';
import { Button } from '@/components/ui/button';
import type { Account, AccountType } from '@/types';

const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  checking: 'Checking Accounts',
  savings: 'Savings Accounts',
  credit: 'Credit Cards',
  investment: 'Investment Accounts',
};

const ACCOUNT_TYPE_ORDER: AccountType[] = ['checking', 'savings', 'credit', 'investment'];

export default function AccountsPage() {
  const { accounts, addAccount, updateAccount, deleteAccount } = useAccountStore();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  // Compute totals
  const { totalAssets, totalLiabilities, groupedAccounts } = useMemo(() => {
    let assets = 0;
    let liabilities = 0;
    const grouped: Record<AccountType, Account[]> = {
      checking: [],
      savings: [],
      credit: [],
      investment: [],
    };

    for (const account of accounts) {
      if (account.isActive) {
        grouped[account.type].push(account);

        if (account.balance >= 0) {
          assets += account.balance;
        } else {
          liabilities += Math.abs(account.balance);
        }
      }
    }

    return { totalAssets: assets, totalLiabilities: liabilities, groupedAccounts: grouped };
  }, [accounts]);

  const activeAccounts = accounts.filter((a) => a.isActive);

  // --- Handlers ---
  const handleOpenCreate = () => {
    setEditingAccount(null);
    setModalOpen(true);
  };

  const handleEdit = (account: Account) => {
    setEditingAccount(account);
    setModalOpen(true);
  };

  const handleSave = (data: {
    name: string;
    type: 'checking' | 'savings' | 'credit' | 'investment';
    institution: string;
    balance: number;
    color: string;
    icon: string;
    isActive: boolean;
  }) => {
    if (editingAccount) {
      updateAccount(editingAccount.id, data);
      toast.success('Account updated successfully');
    } else {
      addAccount(data);
      toast.success('Account added successfully');
    }
  };

  const handleRequestDelete = (id: string) => {
    setDeleteId(id);
  };

  const handleConfirmDelete = () => {
    if (deleteId) {
      deleteAccount(deleteId);
      toast.success('Account deleted');
      setDeleteId(null);
    }
  };

  return (
    <div className="p-6">
      <PageHeader title="Accounts" subtitle="Manage your financial accounts">
        <Button onClick={handleOpenCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Add Account
        </Button>
      </PageHeader>

      {activeAccounts.length > 0 ? (
        <>
          <NetWorthSummary totalAssets={totalAssets} totalLiabilities={totalLiabilities} />
          {ACCOUNT_TYPE_ORDER.map((type) => (
            <AccountGroup
              key={type}
              type={type}
              label={ACCOUNT_TYPE_LABELS[type]}
              accounts={groupedAccounts[type]}
              onEdit={handleEdit}
              onDelete={handleRequestDelete}
            />
          ))}
        </>
      ) : (
        <EmptyState
          icon={Landmark}
          title="No accounts yet"
          description="Add your first financial account to start tracking your balances and net worth."
          actionLabel="Add Account"
          onAction={handleOpenCreate}
        />
      )}

      <AccountModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        editItem={editingAccount}
        onSave={handleSave}
      />

      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Account"
        description="Are you sure you want to delete this account? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
      />
    </div>
  );
}
