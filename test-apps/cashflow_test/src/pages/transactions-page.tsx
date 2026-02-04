import { useState, useMemo, useCallback } from 'react';
import { Plus, ArrowLeftRight } from 'lucide-react';
import { toast } from 'sonner';
import { useTransactionStore } from '@/stores/use-transaction-store';
import { useAccountStore } from '@/stores/use-account-store';
import { useCategoryStore } from '@/stores/use-category-store';
import { PageHeader } from '@/components/shared/page-header';
import { EmptyState } from '@/components/shared/empty-state';
import { Button } from '@/components/ui/button';
import { TransactionFiltersBar } from '@/components/transactions/transaction-filters';
import { TransactionTable } from '@/components/transactions/transaction-table';
import { TransactionPagination } from '@/components/transactions/transaction-pagination';
import { TransactionModal } from '@/components/transactions/transaction-modal';
import type { Transaction, TransactionFilters } from '@/types';

// ---------------------------------------------------------------------------
// Default filters
// ---------------------------------------------------------------------------

const DEFAULT_FILTERS: TransactionFilters = {
  search: '',
  type: null,
  categoryId: null,
  accountId: null,
  dateRange: { start: null, end: null },
  amountRange: { min: null, max: null },
};

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function TransactionsPage() {
  // --- Stores ---
  const transactions = useTransactionStore((s) => s.transactions);
  const addTransaction = useTransactionStore((s) => s.addTransaction);
  const updateTransaction = useTransactionStore((s) => s.updateTransaction);
  const deleteTransaction = useTransactionStore((s) => s.deleteTransaction);
  const getTransactionById = useTransactionStore((s) => s.getTransactionById);

  const accounts = useAccountStore((s) => s.accounts);
  const updateBalance = useAccountStore((s) => s.updateBalance);

  const categories = useCategoryStore((s) => s.categories);

  // --- Local state ---
  const [filters, setFilters] = useState<TransactionFilters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] =
    useState<Transaction | null>(null);

  // --- Filter logic ---
  const filteredTransactions = useMemo(() => {
    let result = [...transactions];

    // Search filter: match description, notes, and tags (case-insensitive)
    if (filters.search) {
      const query = filters.search.toLowerCase();
      result = result.filter(
        (t) =>
          t.description.toLowerCase().includes(query) ||
          t.notes.toLowerCase().includes(query) ||
          t.tags.join(' ').toLowerCase().includes(query),
      );
    }

    // Type filter
    if (filters.type) {
      result = result.filter((t) => t.type === filters.type);
    }

    // Category filter
    if (filters.categoryId) {
      result = result.filter((t) => t.categoryId === filters.categoryId);
    }

    // Account filter
    if (filters.accountId) {
      result = result.filter((t) => t.accountId === filters.accountId);
    }

    // Date range filter
    if (filters.dateRange.start) {
      const startTime = filters.dateRange.start.getTime();
      result = result.filter((t) => new Date(t.date).getTime() >= startTime);
    }
    if (filters.dateRange.end) {
      const endTime = filters.dateRange.end.getTime();
      result = result.filter((t) => new Date(t.date).getTime() <= endTime);
    }

    // Amount range filter (user enters dollars, stored as cents)
    if (filters.amountRange.min !== null) {
      const minCents = filters.amountRange.min * 100;
      result = result.filter((t) => t.amount >= minCents);
    }
    if (filters.amountRange.max !== null) {
      const maxCents = filters.amountRange.max * 100;
      result = result.filter((t) => t.amount <= maxCents);
    }

    // Sort by date descending (default)
    result.sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
    );

    return result;
  }, [transactions, filters]);

  // --- Pagination: slice filtered results ---
  const totalCount = filteredTransactions.length;
  const paginatedTransactions = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredTransactions.slice(start, start + pageSize);
  }, [filteredTransactions, page, pageSize]);

  // Reset to page 1 when filters or pageSize change
  const handleFilterChange = useCallback((newFilters: TransactionFilters) => {
    setFilters(newFilters);
    setPage(1);
  }, []);

  const handlePageSizeChange = useCallback((size: number) => {
    setPageSize(size);
    setPage(1);
  }, []);

  // --- CRUD handlers with cross-store coordination (WIRE-021/022/023) ---

  const handleSave = useCallback(
    (data: {
      type: 'income' | 'expense' | 'transfer';
      amount: string;
      amountCents: number;
      date: string;
      description: string;
      categoryId: string;
      accountId: string;
      notes?: string;
      tags?: string;
    }) => {
      const tags = data.tags
        ? data.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : [];

      if (editingTransaction) {
        // --- EDIT: compute delta, update transaction + adjust balance ---
        const oldTxn = editingTransaction;
        const newAmountCents = data.amountCents;

        // Reverse old balance impact
        if (oldTxn.type === 'income') {
          updateBalance(oldTxn.accountId, -oldTxn.amount);
        } else if (oldTxn.type === 'expense') {
          updateBalance(oldTxn.accountId, oldTxn.amount);
        }

        // Apply new balance impact
        if (data.type === 'income') {
          updateBalance(data.accountId, newAmountCents);
        } else if (data.type === 'expense') {
          updateBalance(data.accountId, -newAmountCents);
        }

        updateTransaction(oldTxn.id, {
          type: data.type,
          amount: newAmountCents,
          date: data.date + 'T12:00:00.000Z',
          description: data.description,
          categoryId: data.categoryId,
          accountId: data.accountId,
          notes: data.notes ?? '',
          tags,
        });

        toast.success('Transaction updated');
      } else {
        // --- ADD: add transaction + update account balance ---
        addTransaction({
          type: data.type,
          amount: data.amountCents,
          date: data.date + 'T12:00:00.000Z',
          description: data.description,
          categoryId: data.categoryId,
          accountId: data.accountId,
          notes: data.notes ?? '',
          tags,
          isRecurring: false,
          recurringId: null,
          transferToAccountId: null,
        });

        // Cross-store: update account balance (WIRE-021)
        if (data.type === 'income') {
          updateBalance(data.accountId, data.amountCents);
        } else if (data.type === 'expense') {
          updateBalance(data.accountId, -data.amountCents);
        }

        toast.success('Transaction added');
      }

      setEditingTransaction(null);
    },
    [editingTransaction, addTransaction, updateTransaction, updateBalance],
  );

  const handleEdit = useCallback((txn: Transaction) => {
    setEditingTransaction(txn);
    setModalOpen(true);
  }, []);

  const handleDelete = useCallback(
    (id: string) => {
      // Get transaction before deleting for cross-store coordination (WIRE-023)
      const txn = getTransactionById(id);
      const deleted = deleteTransaction(id);

      if (deleted && txn) {
        // Reverse balance impact
        if (txn.type === 'income') {
          updateBalance(txn.accountId, -txn.amount);
        } else if (txn.type === 'expense') {
          updateBalance(txn.accountId, txn.amount);
        }
        toast.success('Transaction deleted');
      }
    },
    [deleteTransaction, getTransactionById, updateBalance],
  );

  const handleOpenAdd = useCallback(() => {
    setEditingTransaction(null);
    setModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setModalOpen(false);
    setEditingTransaction(null);
  }, []);

  // --- Render ---

  const isEmpty = transactions.length === 0;

  return (
    <div className="space-y-6">
      {/* Page Header with "Add Transaction" button */}
      <PageHeader title="Transactions" subtitle="Manage your income, expenses, and transfers">
        <Button onClick={handleOpenAdd}>
          <Plus className="h-4 w-4" />
          Add Transaction
        </Button>
      </PageHeader>

      {isEmpty ? (
        <EmptyState
          icon={ArrowLeftRight}
          title="No transactions yet"
          description="Start tracking your finances by adding your first transaction."
          actionLabel="Add Transaction"
          onAction={handleOpenAdd}
        />
      ) : (
        <>
          {/* Filters */}
          <TransactionFiltersBar
            accounts={accounts}
            categories={categories}
            filters={filters}
            onFilterChange={handleFilterChange}
          />

          {/* Table */}
          <TransactionTable
            transactions={paginatedTransactions}
            categories={categories}
            accounts={accounts}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />

          {/* Pagination */}
          <TransactionPagination
            currentPage={page}
            pageSize={pageSize}
            totalCount={totalCount}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
          />
        </>
      )}

      {/* Modal */}
      <TransactionModal
        open={modalOpen}
        onClose={handleCloseModal}
        editItem={editingTransaction}
        onSave={handleSave}
        accounts={accounts}
        categories={categories}
      />
    </div>
  );
}
