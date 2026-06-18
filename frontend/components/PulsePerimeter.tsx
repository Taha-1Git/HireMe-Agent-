'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export function PulsePerimeter({
  score,
  children,
}: {
  score: number;
  children: ReactNode;
}) {
  const ringClass =
    score > 66
      ? 'ring-red-500'
      : score > 33
        ? 'ring-yellow-500'
        : 'ring-emerald-500';

  return (
    <div className={cn('rounded-lg ring-2 ring-offset-2 ring-offset-slate-950', ringClass)}>
      {children}
    </div>
  );
}
