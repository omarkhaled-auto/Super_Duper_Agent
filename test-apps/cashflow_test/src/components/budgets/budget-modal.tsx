import { useEffect } from 'react';
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
  FormControl,
  FormField,
  FormItem,
  FormLabel,
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
import type { Budget, Category } from '@/types';

const budgetSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  categoryId: z.string().min(1, 'Category is required'),
  amount: z
    .number({ coerce: true })
    .positive('Amount must be greater than zero'),
  period: z.enum(['monthly', 'weekly', 'yearly']),
  alertThreshold: z
    .number({ coerce: true })
    .min(0, 'Threshold must be 0-100')
    .max(100, 'Threshold must be 0-100'),
});

type BudgetFormValues = z.infer<typeof budgetSchema>;

interface BudgetModalProps {
  open: boolean;
  onClose: () => void;
  editItem?: Budget | null;
  onSave: (data: {
    name: string;
    categoryId: string;
    amount: number;
    period: 'monthly' | 'weekly' | 'yearly';
    alertThreshold: number;
    isActive: boolean;
  }) => void;
  categories: Category[];
}

export function BudgetModal({
  open,
  onClose,
  editItem,
  onSave,
  categories,
}: BudgetModalProps) {
  const expenseCategories = categories.filter((c) => c.type === 'expense');

  const form = useForm<BudgetFormValues>({
    resolver: zodResolver(budgetSchema),
    defaultValues: {
      name: '',
      categoryId: '',
      amount: 0,
      period: 'monthly',
      alertThreshold: 80,
    },
  });

  useEffect(() => {
    if (open) {
      if (editItem) {
        form.reset({
          name: editItem.name,
          categoryId: editItem.categoryId,
          amount: editItem.amount / 100, // cents to dollars for display
          period: editItem.period,
          alertThreshold: editItem.alertThreshold,
        });
      } else {
        form.reset({
          name: '',
          categoryId: '',
          amount: 0,
          period: 'monthly',
          alertThreshold: 80,
        });
      }
    }
  }, [open, editItem, form]);

  const handleSubmit = (values: BudgetFormValues) => {
    onSave({
      name: values.name,
      categoryId: values.categoryId,
      amount: Math.round(values.amount * 100), // dollars to cents
      period: values.period,
      alertThreshold: values.alertThreshold,
      isActive: true,
    });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editItem ? 'Edit Budget' : 'Create Budget'}</DialogTitle>
          <DialogDescription>
            {editItem
              ? 'Update the budget details below.'
              : 'Set a spending limit for a category.'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Groceries Budget" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="categoryId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {expenseCategories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.icon} {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Limit ($)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
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
              name="period"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Period</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select period" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                      <SelectItem value="yearly">Yearly</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="alertThreshold"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Alert Threshold (%)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      placeholder="80"
                      {...field}
                    />
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
                {editItem ? 'Save Changes' : 'Create Budget'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
