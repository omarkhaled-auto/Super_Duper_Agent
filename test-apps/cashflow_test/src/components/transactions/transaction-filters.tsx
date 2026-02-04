import { useState, useEffect, useCallback } from 'react';
import { Search, X, CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { cn } from '@/lib/utils';
import type { Account, Category, TransactionFilters } from '@/types';

interface TransactionFiltersProps {
  accounts: Account[];
  categories: Category[];
  filters: TransactionFilters;
  onFilterChange: (filters: TransactionFilters) => void;
}

const EMPTY_FILTERS: TransactionFilters = {
  search: '',
  type: null,
  categoryId: null,
  accountId: null,
  dateRange: { start: null, end: null },
  amountRange: { min: null, max: null },
};

export function TransactionFiltersBar({
  accounts,
  categories,
  filters,
  onFilterChange,
}: TransactionFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search);

  // Debounced search: 300ms delay via setTimeout
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== filters.search) {
        onFilterChange({ ...filters, search: searchInput });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Filter categories by selected type when applicable
  const filteredCategories = filters.type && filters.type !== 'transfer'
    ? categories.filter((c) => c.type === filters.type)
    : categories;

  const handleTypeChange = useCallback(
    (value: string) => {
      const type = value === 'all' ? null : (value as 'income' | 'expense' | 'transfer');
      // Reset category when type changes since category may no longer be valid
      onFilterChange({ ...filters, type, categoryId: null });
    },
    [filters, onFilterChange],
  );

  const handleCategoryChange = useCallback(
    (value: string) => {
      onFilterChange({ ...filters, categoryId: value === 'all' ? null : value });
    },
    [filters, onFilterChange],
  );

  const handleAccountChange = useCallback(
    (value: string) => {
      onFilterChange({ ...filters, accountId: value === 'all' ? null : value });
    },
    [filters, onFilterChange],
  );

  const handleDateStartChange = useCallback(
    (date: Date | undefined) => {
      onFilterChange({
        ...filters,
        dateRange: { ...filters.dateRange, start: date ?? null },
      });
    },
    [filters, onFilterChange],
  );

  const handleDateEndChange = useCallback(
    (date: Date | undefined) => {
      onFilterChange({
        ...filters,
        dateRange: { ...filters.dateRange, end: date ?? null },
      });
    },
    [filters, onFilterChange],
  );

  const handleAmountMinChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value === '' ? null : Number(e.target.value);
      onFilterChange({
        ...filters,
        amountRange: { ...filters.amountRange, min: value },
      });
    },
    [filters, onFilterChange],
  );

  const handleAmountMaxChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value === '' ? null : Number(e.target.value);
      onFilterChange({
        ...filters,
        amountRange: { ...filters.amountRange, max: value },
      });
    },
    [filters, onFilterChange],
  );

  const handleClearFilters = useCallback(() => {
    setSearchInput('');
    onFilterChange(EMPTY_FILTERS);
  }, [onFilterChange]);

  const hasActiveFilters =
    filters.search !== '' ||
    filters.type !== null ||
    filters.categoryId !== null ||
    filters.accountId !== null ||
    filters.dateRange.start !== null ||
    filters.dateRange.end !== null ||
    filters.amountRange.min !== null ||
    filters.amountRange.max !== null;

  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Search Input */}
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search transactions..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Type Select */}
      <Select
        value={filters.type ?? 'all'}
        onValueChange={handleTypeChange}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="All Types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          <SelectItem value="income">Income</SelectItem>
          <SelectItem value="expense">Expense</SelectItem>
          <SelectItem value="transfer">Transfer</SelectItem>
        </SelectContent>
      </Select>

      {/* Category Select */}
      <Select
        value={filters.categoryId ?? 'all'}
        onValueChange={handleCategoryChange}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Categories" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Categories</SelectItem>
          {filteredCategories.map((cat) => (
            <SelectItem key={cat.id} value={cat.id}>
              {cat.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Account Select */}
      <Select
        value={filters.accountId ?? 'all'}
        onValueChange={handleAccountChange}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Accounts" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Accounts</SelectItem>
          {accounts.map((acc) => (
            <SelectItem key={acc.id} value={acc.id}>
              {acc.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Date Range: From */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              'w-[150px] justify-start text-left font-normal',
              !filters.dateRange.start && 'text-muted-foreground',
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {filters.dateRange.start
              ? format(filters.dateRange.start, 'MMM d, yyyy')
              : 'From date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={filters.dateRange.start ?? undefined}
            onSelect={handleDateStartChange}
          />
        </PopoverContent>
      </Popover>

      {/* Date Range: To */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              'w-[150px] justify-start text-left font-normal',
              !filters.dateRange.end && 'text-muted-foreground',
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {filters.dateRange.end
              ? format(filters.dateRange.end, 'MMM d, yyyy')
              : 'To date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={filters.dateRange.end ?? undefined}
            onSelect={handleDateEndChange}
          />
        </PopoverContent>
      </Popover>

      {/* Amount Range */}
      <div className="flex items-center gap-2">
        <Label className="text-sm text-muted-foreground whitespace-nowrap">$</Label>
        <Input
          type="number"
          placeholder="Min"
          value={filters.amountRange.min ?? ''}
          onChange={handleAmountMinChange}
          className="w-[90px]"
          min={0}
          step="0.01"
        />
        <span className="text-muted-foreground">-</span>
        <Input
          type="number"
          placeholder="Max"
          value={filters.amountRange.max ?? ''}
          onChange={handleAmountMaxChange}
          className="w-[90px]"
          min={0}
          step="0.01"
        />
      </div>

      {/* Clear Filters Button */}
      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={handleClearFilters}>
          <X className="h-4 w-4 mr-1" />
          Clear
        </Button>
      )}
    </div>
  );
}
