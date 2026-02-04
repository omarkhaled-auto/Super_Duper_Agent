import { useState } from 'react';
import type { Category } from '@/types';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ConfirmDialog } from '@/components/shared/confirm-dialog';
import { Plus, Pencil, Trash2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Category Settings (TASK-059)
// CRUD management for transaction categories.
// ---------------------------------------------------------------------------

interface CategorySettingsProps {
  categories: Category[];
  onAdd: (data: Omit<Category, 'id' | 'createdAt' | 'updatedAt'>) => void;
  onEdit: (id: string, updates: Partial<Category>) => void;
  onDelete: (id: string) => void;
}

interface CategoryFormData {
  name: string;
  icon: string;
  color: string;
  type: 'income' | 'expense';
}

const DEFAULT_FORM: CategoryFormData = {
  name: '',
  icon: 'Circle',
  color: '#6366F1',
  type: 'expense',
};

export function CategorySettings({
  categories,
  onAdd,
  onEdit,
  onDelete,
}: CategorySettingsProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [form, setForm] = useState<CategoryFormData>(DEFAULT_FORM);

  const handleOpenAdd = () => {
    setEditingId(null);
    setForm(DEFAULT_FORM);
    setDialogOpen(true);
  };

  const handleOpenEdit = (cat: Category) => {
    setEditingId(cat.id);
    setForm({
      name: cat.name,
      icon: cat.icon,
      color: cat.color,
      type: cat.type,
    });
    setDialogOpen(true);
  };

  const handleSave = () => {
    if (!form.name.trim()) return;

    if (editingId) {
      onEdit(editingId, {
        name: form.name.trim(),
        icon: form.icon.trim(),
        color: form.color,
        type: form.type,
      });
    } else {
      onAdd({
        name: form.name.trim(),
        icon: form.icon.trim(),
        color: form.color,
        type: form.type,
        isDefault: false,
        sortOrder: categories.length,
      });
    }

    setDialogOpen(false);
    setEditingId(null);
    setForm(DEFAULT_FORM);
  };

  const handleConfirmDelete = () => {
    if (deleteId) {
      onDelete(deleteId);
      setDeleteId(null);
    }
  };

  const sortedCategories = [...categories].sort(
    (a, b) => a.sortOrder - b.sortOrder,
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Categories</CardTitle>
          <CardDescription>
            Manage the categories used to classify your transactions and budgets.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Button onClick={handleOpenAdd}>
              <Plus className="size-4" />
              Add Category
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">Color</TableHead>
                <TableHead>Icon</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedCategories.map((cat) => (
                <TableRow key={cat.id}>
                  <TableCell>
                    <span
                      className="inline-block size-4 rounded-full"
                      style={{ backgroundColor: cat.color }}
                    />
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {cat.icon}
                  </TableCell>
                  <TableCell className="font-medium">{cat.name}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        cat.type === 'income' ? 'default' : 'secondary'
                      }
                    >
                      {cat.type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => handleOpenEdit(cat)}
                      >
                        <Pencil className="size-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => setDeleteId(cat.id)}
                      >
                        <Trash2 className="size-3.5 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {sortedCategories.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="text-center text-muted-foreground py-8"
                  >
                    No categories yet. Click &quot;Add Category&quot; to create
                    one.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingId ? 'Edit Category' : 'Add Category'}
            </DialogTitle>
            <DialogDescription>
              {editingId
                ? 'Update the details for this category.'
                : 'Create a new category for your transactions.'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="cat-name">Name</Label>
              <Input
                id="cat-name"
                placeholder="e.g. Groceries"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cat-icon">Icon (Lucide icon name)</Label>
              <Input
                id="cat-icon"
                placeholder="e.g. ShoppingCart"
                value={form.icon}
                onChange={(e) => setForm({ ...form, icon: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cat-color">Color</Label>
              <div className="flex items-center gap-3">
                <Input
                  id="cat-color"
                  type="color"
                  className="w-12 h-9 p-1 cursor-pointer"
                  value={form.color}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                />
                <Input
                  placeholder="#6366F1"
                  value={form.color}
                  onChange={(e) => setForm({ ...form, color: e.target.value })}
                  className="flex-1"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Type</Label>
              <Select
                value={form.type}
                onValueChange={(value: 'income' | 'expense') =>
                  setForm({ ...form, type: value })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="expense">Expense</SelectItem>
                  <SelectItem value="income">Income</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!form.name.trim()}>
              {editingId ? 'Save Changes' : 'Add Category'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Category"
        description="Are you sure you want to delete this category? Transactions using this category will not be deleted, but they will lose their category assignment."
        confirmLabel="Delete"
        variant="destructive"
      />
    </div>
  );
}
