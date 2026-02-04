import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Landmark,
  PiggyBank,
  CreditCard,
  TrendingUp,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { CurrencyDisplay } from '@/components/shared/currency-display';
import type { Account, AccountType } from '@/types';

const ACCOUNT_TYPE_ICONS: Record<AccountType, typeof Landmark> = {
  checking: Landmark,
  savings: PiggyBank,
  credit: CreditCard,
  investment: TrendingUp,
};

interface AccountCardProps {
  account: Account;
  onEdit: (a: Account) => void;
  onDelete: (id: string) => void;
}

export function AccountCard({ account, onEdit, onDelete }: AccountCardProps) {
  const Icon = ACCOUNT_TYPE_ICONS[account.type];

  return (
    <Card
      className="overflow-hidden"
      style={{ borderLeftWidth: '4px', borderLeftColor: account.color }}
    >
      <CardContent className="pt-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{ backgroundColor: account.color + '20', color: account.color }}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold text-sm">{account.name}</p>
              <p className="text-muted-foreground text-sm">{account.institution}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <CurrencyDisplay amount={account.balance} className="text-lg font-bold" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-xs">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(account)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  variant="destructive"
                  onClick={() => onDelete(account.id)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
