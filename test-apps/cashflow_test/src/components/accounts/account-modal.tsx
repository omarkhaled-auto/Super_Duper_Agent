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
import type { Account } from '@/types';

const accountSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['checking', 'savings', 'credit', 'investment']),
  institution: z.string().min(1, 'Institution is required'),
  balance: z.number({ coerce: true }),
  color: z.string().min(1, 'Color is required').regex(/^#[0-9A-Fa-f]{6}$/, 'Must be a valid hex color (e.g. #3B82F6)'),
});

type AccountFormValues = z.infer<typeof accountSchema>;

interface AccountModalProps {
  open: boolean;
  onClose: () => void;
  editItem?: Account | null;
  onSave: (data: {
    name: string;
    type: 'checking' | 'savings' | 'credit' | 'investment';
    institution: string;
    balance: number;
    color: string;
    icon: string;
    isActive: boolean;
  }) => void;
}

const TYPE_ICONS: Record<string, string> = {
  checking: 'Landmark',
  savings: 'PiggyBank',
  credit: 'CreditCard',
  investment: 'TrendingUp',
};

export function AccountModal({
  open,
  onClose,
  editItem,
  onSave,
}: AccountModalProps) {
  const form = useForm<AccountFormValues>({
    resolver: zodResolver(accountSchema),
    defaultValues: {
      name: '',
      type: 'checking',
      institution: '',
      balance: 0,
      color: '#3B82F6',
    },
  });

  useEffect(() => {
    if (open) {
      if (editItem) {
        form.reset({
          name: editItem.name,
          type: editItem.type,
          institution: editItem.institution,
          balance: editItem.balance / 100, // cents to dollars for display
          color: editItem.color,
        });
      } else {
        form.reset({
          name: '',
          type: 'checking',
          institution: '',
          balance: 0,
          color: '#3B82F6',
        });
      }
    }
  }, [open, editItem, form]);

  const handleSubmit = (values: AccountFormValues) => {
    onSave({
      name: values.name,
      type: values.type,
      institution: values.institution,
      balance: Math.round(values.balance * 100), // dollars to cents
      color: values.color,
      icon: TYPE_ICONS[values.type] ?? 'Landmark',
      isActive: true,
    });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editItem ? 'Edit Account' : 'Add Account'}</DialogTitle>
          <DialogDescription>
            {editItem
              ? 'Update the account details below.'
              : 'Add a new financial account to track.'}
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
                    <Input placeholder="e.g. Main Checking" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select account type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="checking">Checking</SelectItem>
                      <SelectItem value="savings">Savings</SelectItem>
                      <SelectItem value="credit">Credit Card</SelectItem>
                      <SelectItem value="investment">Investment</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="institution"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Institution</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Chase Bank" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="balance"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Balance ($)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
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
              name="color"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Color</FormLabel>
                  <div className="flex items-center gap-2">
                    <FormControl>
                      <Input placeholder="#3B82F6" {...field} />
                    </FormControl>
                    <div
                      className="h-9 w-9 rounded-md border shrink-0"
                      style={{ backgroundColor: field.value }}
                    />
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit">
                {editItem ? 'Save Changes' : 'Add Account'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
