'use client';

import { motion } from 'motion/react';
import { MessageSquare, RotateCcw } from 'lucide-react';
import { MoneyBuddyAvatar } from '@/components/moneybuddy/avatar';
import { TrustBanner } from '@/components/moneybuddy/trust-banner';
import { useLanguage } from '@/hooks/useLanguage';
import { cn } from '@/lib/shadcn/utils';

interface CallEndedViewProps {
  messageCount?: number;
  onRestart: () => void;
  className?: string;
}

export function CallEndedView({ messageCount = 0, onRestart, className }: CallEndedViewProps) {
  const { t } = useLanguage();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className={cn(
        'flex flex-col items-center justify-center text-center px-6 gap-6',
        className
      )}
    >
      {/* Avatar in ended/calm state */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <MoneyBuddyAvatar state="ended" size="lg" />
      </motion.div>

      {/* Ended message */}
      <motion.div
        initial={{ y: 12, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.25, duration: 0.4 }}
        className="flex flex-col gap-2"
      >
        <h2 className="text-xl font-semibold text-foreground">
          {t('ended.title')}
        </h2>
        <p className="text-sm text-muted-foreground">
          {t('ended.subtitle')}
        </p>
      </motion.div>

      {/* Conversation summary */}
      {messageCount > 0 && (
        <motion.div
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.35, duration: 0.4 }}
          className="flex items-center gap-2 rounded-full px-4 py-2 mb-glass"
        >
          <MessageSquare className="h-4 w-4 text-primary/60" />
          <span className="text-sm text-muted-foreground">
            {messageCount} {t('ended.messagesCount')}
          </span>
        </motion.div>
      )}

      {/* Start Again button */}
      <motion.button
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.45, duration: 0.4 }}
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={onRestart}
        className={cn(
          'flex items-center gap-2.5 rounded-full px-8 py-3.5',
          'bg-gradient-to-r from-emerald-500 to-teal-500',
          'dark:from-emerald-400 dark:to-teal-400',
          'text-white dark:text-gray-900',
          'font-semibold text-sm',
          'shadow-lg shadow-emerald-500/20 dark:shadow-emerald-400/20',
          'hover:shadow-xl hover:shadow-emerald-500/30',
          'transition-shadow duration-300',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2'
        )}
      >
        <RotateCcw className="h-4 w-4" />
        {t('ended.startAgain')}
      </motion.button>

      {/* Trust reminder */}
      <motion.div
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.55, duration: 0.4 }}
      >
        <TrustBanner variant="compact" />
      </motion.div>
    </motion.div>
  );
}
