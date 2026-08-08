'use client';

import { motion } from 'motion/react';
import { MicOff, Settings, RefreshCw } from 'lucide-react';
import { MoneyBuddyAvatar } from '@/components/moneybuddy/avatar';
import { useLanguage } from '@/hooks/useLanguage';
import { cn } from '@/lib/shadcn/utils';

interface MicPermissionProps {
  onRetry: () => void;
  className?: string;
}

export function MicPermission({ onRetry, className }: MicPermissionProps) {
  const { t } = useLanguage();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={cn(
        'flex flex-col items-center justify-center text-center px-6 py-12 gap-6',
        className
      )}
    >
      {/* Avatar in subdued state */}
      <MoneyBuddyAvatar state="ended" size="md" />

      {/* Error icon */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="relative"
      >
        <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
          <MicOff className="h-7 w-7 text-destructive/70" />
        </div>
      </motion.div>

      {/* Message */}
      <motion.div
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        className="flex flex-col gap-3 max-w-sm"
      >
        <h2 className="text-lg font-semibold text-foreground">
          {t('mic.required')}
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {t('mic.howTo')}
        </p>
      </motion.div>

      {/* How-to steps */}
      <motion.div
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.4 }}
        className="flex flex-col gap-2 rounded-xl p-4 mb-glass max-w-xs w-full text-left"
      >
        <div className="flex items-start gap-3 text-xs text-muted-foreground">
          <Settings className="h-4 w-4 shrink-0 mt-0.5 text-primary/60" />
          <span>
            Click the <strong>lock/camera icon</strong> in your browser&apos;s address bar and
            allow microphone access for this site.
          </span>
        </div>
      </motion.div>

      {/* Retry button */}
      <motion.button
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.4 }}
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={onRetry}
        className={cn(
          'flex items-center gap-2 rounded-full px-8 py-3',
          'bg-primary text-primary-foreground',
          'font-semibold text-sm',
          'shadow-lg shadow-primary/20',
          'hover:shadow-xl hover:shadow-primary/30',
          'transition-shadow duration-300',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2'
        )}
      >
        <RefreshCw className="h-4 w-4" />
        {t('mic.tryAgain')}
      </motion.button>
    </motion.div>
  );
}
