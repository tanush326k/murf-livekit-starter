'use client';

import { ShieldCheck, Lock, AlertTriangle, Info } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { cn } from '@/lib/shadcn/utils';

interface TrustBannerProps {
  variant?: 'welcome' | 'session' | 'compact';
  className?: string;
}

export function TrustBanner({ variant = 'welcome', className }: TrustBannerProps) {
  const { t } = useLanguage();

  if (variant === 'compact') {
    return (
      <div
        className={cn(
          'flex items-center gap-2 rounded-full px-4 py-1.5',
          'text-xs text-muted-foreground',
          'mb-glass',
          className
        )}
      >
        <ShieldCheck className="h-3.5 w-3.5 text-primary/60" />
        <span>{t('trust.responsible')}</span>
      </div>
    );
  }

  if (variant === 'session') {
    return (
      <div
        className={cn(
          'flex flex-col gap-2 rounded-xl p-3',
          'mb-glass',
          className
        )}
      >
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Lock className="h-3.5 w-3.5 text-primary/60 shrink-0" />
          <span>{t('trust.private')}</span>
        </div>
        <div className="flex items-start gap-2 text-xs text-amber-500/80 dark:text-amber-400/70">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <span>{t('trust.neverShare')}</span>
        </div>
      </div>
    );
  }

  // Welcome variant — fuller display
  return (
    <div className={cn('flex flex-col items-center gap-3', className)}>
      <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-primary/60" />
          <span>{t('trust.responsible')}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Lock className="h-3.5 w-3.5 text-primary/60" />
          <span>{t('trust.private')}</span>
        </div>
      </div>
      <div className="flex items-start gap-2 rounded-lg px-4 py-2.5 mb-glass max-w-sm">
        <AlertTriangle className="h-3.5 w-3.5 text-amber-500/70 dark:text-amber-400/60 shrink-0 mt-0.5" />
        <span className="text-xs text-muted-foreground leading-relaxed">
          {t('trust.neverShare')}
        </span>
      </div>
      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground/60">
        <Info className="h-3 w-3" />
        <span>{t('trust.disclaimer')}</span>
      </div>
    </div>
  );
}
