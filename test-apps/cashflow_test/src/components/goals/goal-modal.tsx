import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import { Button } from '@/components/ui/button';
import type { Goal } from '@/types';

// ---------------------------------------------------------------------------
// GoalModal (TASK-056)
// Create / Edit dialog for goals. Uses React Hook Form + Zod validation.
// Dollar inputs are converted to/from cents for the store.
// ---------------------------------------------------------------------------

const goalSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  targetAmount: z
    .number({ invalid_type_error: 'Enter a valid amount' })
    .positive('Target must be greater than 0'),
  currentAmount: z
    .number({ invalid_type_error: 'Enter a valid amount' })
    .min(0, 'Cannot be negative'),
  deadline: z.string().optional(),
  monthlyContribution: z
    .number({ invalid_type_error: 'Enter a valid amount' })
    .min(0, 'Cannot be negative'),
  icon: z.string().min(1),
  color: z.string().min(1),
});

type GoalFormValues = z.infer<typeof goalSchema>;

interface GoalModalProps {
  open: boolean;
  onClose: () => void;
  editItem?: Goal | null;
  onSave: (data: {
    name: string;
    description: string;
    targetAmount: number;
    currentAmount: number;
    deadline: string | null;
    monthlyContribution: number;
    icon: string;
    color: string;
    status: Goal['status'];
    linkedAccountId: string | null;
  }) => void;
}

export function GoalModal({ open, onClose, editItem, onSave }: GoalModalProps) {
  const form = useForm<GoalFormValues>({
    resolver: zodResolver(goalSchema),
    defaultValues: {
      name: '',
      description: '',
      targetAmount: 0,
      currentAmount: 0,
      deadline: '',
      monthlyContribution: 0,
      icon: 'Target',
      color: '#5E6AD2',
    },
  });

  // Reset form when the modal opens / editItem changes
  useEffect(() => {
    if (open) {
      if (editItem) {
        form.reset({
          name: editItem.name,
          description: editItem.description ?? '',
          targetAmount: editItem.targetAmount / 100,
          currentAmount: editItem.currentAmount / 100,
          deadline: editItem.deadline ?? '',
          monthlyContribution: editItem.monthlyContribution / 100,
          icon: editItem.icon || 'Target',
          color: editItem.color || '#5E6AD2',
        });
      } else {
        form.reset({
          name: '',
          description: '',
          targetAmount: 0,
          currentAmount: 0,
          deadline: '',
          monthlyContribution: 0,
          icon: 'Target',
          color: '#5E6AD2',
        });
      }
    }
  }, [open, editItem, form]);

  const handleSubmit = (values: GoalFormValues) => {
    onSave({
      name: values.name,
      description: values.description ?? '',
      targetAmount: Math.round(values.targetAmount * 100),
      currentAmount: Math.round(values.currentAmount * 100),
      deadline: values.deadline || null,
      monthlyContribution: Math.round(values.monthlyContribution * 100),
      icon: values.icon,
      color: values.color,
      status: editItem?.status ?? 'on-track',
      linkedAccountId: editItem?.linkedAccountId ?? null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>{editItem ? 'Edit Goal' : 'New Goal'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            {/* Name */}
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g. Emergency Fund" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Description */}
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="What is this goal for?" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Target Amount (dollars) */}
            <FormField
              control={form.control}
              name="targetAmount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Target Amount ($)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="10000.00"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Current Amount (dollars) */}
            <FormField
              control={form.control}
              name="currentAmount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Current Amount ($)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Deadline */}
            <FormField
              control={form.control}
              name="deadline"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Deadline</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Monthly Contribution (dollars) */}
            <FormField
              control={form.control}
              name="monthlyContribution"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Monthly Contribution ($)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="500.00"
                      {...field}
                      onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              {/* Icon */}
              <FormField
                control={form.control}
                name="icon"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Icon</FormLabel>
                    <FormControl>
                      <Input placeholder="Target" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Color */}
              <FormField
                control={form.control}
                name="color"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Color</FormLabel>
                    <FormControl>
                      <Input type="color" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit">
                {editItem ? 'Save Changes' : 'Create Goal'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
