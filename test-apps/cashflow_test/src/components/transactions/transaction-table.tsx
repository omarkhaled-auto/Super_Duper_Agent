import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { ArrowUpDown, MoreHorizontal, Pencil, Trash2 } from 'lucide-react';
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import { formatDate } from '@/lib/format';
import type { Transaction, Category, Account } from '@/types';

interface TransactionTableProps {
  transactions: Transaction[];
  categories: Category[];
  accounts: Account[];
  onEdit: (txn: Transaction) => void;
  onDelete: (id: string) => void;
}

export function TransactionTable({
  transactions,
  categories,
  accounts,
  onEdit,
  onDelete,
}: TransactionTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  // Build lookup maps for fast access
  const categoryMap = useMemo(
    () => new Map(categories.map((c) => [c.id, c])),
    [categories],
  );
  const accountMap = useMemo(
    () => new Map(accounts.map((a) => [a.id, a])),
    [accounts],
  );

  const columns = useMemo<ColumnDef<Transaction>[]>(
    () => [
      // Date column: sortable
      {
        accessorKey: 'date',
        header: ({ column }) => (
          <Button
            variant="ghost"
            size="sm"
            className="-ml-3 h-8"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Date
            <ArrowUpDown className="ml-1 h-3.5 w-3.5" />
          </Button>
        ),
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">
            {formatDate(row.getValue('date'))}
          </span>
        ),
      },
      // Description column: text, truncated
      {
        accessorKey: 'description',
        header: 'Description',
        cell: ({ row }) => (
          <span className="text-sm font-medium truncate block max-w-[200px]">
            {row.getValue('description')}
          </span>
        ),
      },
      // Category column: lookup name/color, Badge with dot
      {
        accessorKey: 'categoryId',
        header: 'Category',
        cell: ({ row }) => {
          const category = categoryMap.get(row.original.categoryId);
          if (!category) return <span className="text-sm text-muted-foreground">--</span>;
          return (
            <Badge variant="secondary" className="gap-1.5 font-normal">
              <span
                className="h-2 w-2 rounded-full shrink-0"
                style={{ backgroundColor: category.color }}
              />
              {category.name}
            </Badge>
          );
        },
      },
      // Account column: lookup name
      {
        accessorKey: 'accountId',
        header: 'Account',
        cell: ({ row }) => {
          const account = accountMap.get(row.original.accountId);
          return (
            <span className="text-sm text-muted-foreground">
              {account?.name ?? 'Unknown'}
            </span>
          );
        },
      },
      // Amount column: sortable, right-aligned, colored
      {
        accessorKey: 'amount',
        header: ({ column }) => (
          <div className="text-right">
            <Button
              variant="ghost"
              size="sm"
              className="-mr-3 h-8"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === 'asc')
              }
            >
              Amount
              <ArrowUpDown className="ml-1 h-3.5 w-3.5" />
            </Button>
          </div>
        ),
        cell: ({ row }) => {
          const txn = row.original;
          // Income is positive (green), expense is negative (red), transfer neutral
          const displayAmount =
            txn.type === 'expense' ? -txn.amount : txn.amount;
          return (
            <div className="text-right">
              <CurrencyDisplay amount={displayAmount} />
            </div>
          );
        },
      },
      // Actions column: DropdownMenu with Edit/Delete
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => {
          const txn = row.original;
          return (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-xs">
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(txn)}>
                  <Pencil className="h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  variant="destructive"
                  onClick={() => onDelete(txn.id)}
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
      },
    ],
    [categoryMap, accountMap, onEdit, onDelete],
  );

  const table = useReactTable({
    data: transactions,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No transactions found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
