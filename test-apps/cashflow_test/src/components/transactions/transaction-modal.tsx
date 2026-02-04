import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import type { Transaction, Account, Category } from '@/types';

// ---------------------------------------------------------------------------
// Zod schema
// ---------------------------------------------------------------------------

const transactionSchema = z.object({
  type: z.enum(['income', 'expense', 'transfer']),
  amount: z
    .string()
    .min(1, 'Amount is required')
    .refine(
      (v) => !isNaN(Number(v)) && Number(v) > 0,
      'Must be positive',
    ),
  date: z.string().min(1, 'Date is required'),
  description: z
    .string()
    .min(1, 'Description is required')
    .max(200),
  categoryId: z.string().min(1, 'Category is required'),
  accountId: z.string().min(1, 'Account is required'),
  notes: z.string().optional(),
  tags: z.string().optional(),
});

type TransactionFormValues = z.infer<typeof transactionSchema>;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface TransactionModalProps {
  open: boolean;
  onClose: () => void;
  editItem?: Transaction | null;
  onSave: (data: TransactionFormValues & { amountCents: number }) => void;
  accounts: Account[];
  categories: Category[];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function TransactionModal({
  open,
  onClose,
  editItem,
  onSave,
  accounts,
  categories,
}: TransactionModalProps) {
  const isEditing = !!editItem;

  const form = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      type: 'expense',
      amount: '',
      date: new Date().toISOString().split('T')[0],
      description: '',
      categoryId: '',
      accountId: '',
      notes: '',
      tags: '',
    },
  });

  const watchedType = form.watch('type');

  // Filter categories by selected type (income/expense). Transfer shows all.
  const filteredCategories = useMemo(
    () =>
      watchedType === 'transfer'
        ? categories
        : categories.filter((c) => c.type === watchedType),
    [watchedType, categories],
  );

  // Pre-populate when editItem is provided (convert cents to dollars)
  useEffect(() => {
    if (open && editItem) {
      form.reset({
        type: editItem.type,
        amount: (editItem.amount / 100).toFixed(2),
        date: editItem.date.split('T')[0],
        description: editItem.description,
        categoryId: editItem.categoryId,
        accountId: editItem.accountId,
        notes: editItem.notes ?? '',
        tags: editItem.tags?.join(', ') ?? '',
      });
    } else if (open && !editItem) {
      form.reset({
        type: 'expense',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        description: '',
        categoryId: '',
        accountId: '',
        notes: '',
        tags: '',
      });
    }
  }, [open, editItem]);

  // Reset category when type changes so stale category does not persist
  useEffect(() => {
    const currentCatId = form.getValues('categoryId');
    if (currentCatId) {
      const isValid = filteredCategories.some((c) => c.id === currentCatId);
      if (!isValid) {
        form.setValue('categoryId', '');
      }
    }
  }, [watchedType, filteredCategories]);

  const handleSubmit = (values: TransactionFormValues) => {
    // Convert dollars to cents: multiply by 100, round to avoid float issues
    const amountCents = Math.round(Number(values.amount) * 100);
    onSave({ ...values, amountCents });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Transaction' : 'Add Transaction'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the details of this transaction.'
              : 'Create a new transaction record.'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-4"
          >
            {/* Type */}
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="income">Income</SelectItem>
                      <SelectItem value="expense">Expense</SelectItem>
                      <SelectItem value="transfer">Transfer</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Amount + Date row */}
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Amount ($)</FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        inputMode="decimal"
                        placeholder="0.00"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Description */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g. Grocery shopping at Whole Foods"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Category */}
            <FormField
              control={form.control}
              name="categoryId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {filteredCategories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Account */}
            <FormField
              control={form.control}
              name="accountId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Account</FormLabel>
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                  >
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {accounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Notes */}
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes (optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="Additional notes..." {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Tags */}
            <FormField
              control={form.control}
              name="tags"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tags (optional, comma-separated)</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. food, weekly" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit">
                {isEditing ? 'Save Changes' : 'Add Transaction'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
