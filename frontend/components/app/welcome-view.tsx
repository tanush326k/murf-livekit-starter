'use client';

import { motion } from 'motion/react';
import { Mic } from 'lucide-react';
import { MoneyBuddyAvatar } from '@/components/moneybuddy/avatar';
import { TrustBanner } from '@/components/moneybuddy/trust-banner';
import { useLanguage } from '@/hooks/useLanguage';
import { cn } from '@/lib/shadcn/utils';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const { t } = useLanguage();

  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center text-center px-6 py-8 gap-4">
        {/* Animated avatar entrance */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          <MoneyBuddyAvatar state="idle" size="lg" />
        </motion.div>

        {/* Welcome text */}
        <motion.div
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5, ease: 'easeOut' }}
          className="flex flex-col items-center gap-2 max-w-md"
        >
          <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
            {t('welcome.greeting')}
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
            {t('welcome.subtitle')}
          </p>
        </motion.div>

        {/* Start button */}
        <motion.div
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5, ease: 'easeOut' }}
          className="pt-2"
        >
          <button
            onClick={onStartCall}
            className={cn(
              'group relative flex items-center gap-3 rounded-full px-8 py-4',
              'bg-gradient-to-r from-emerald-500 to-teal-500',
              'dark:from-emerald-400 dark:to-teal-400',
              'text-white dark:text-gray-900',
              'font-semibold text-base',
              'shadow-lg shadow-emerald-500/25 dark:shadow-emerald-400/20',
              'hover:shadow-xl hover:shadow-emerald-500/35 dark:hover:shadow-emerald-400/30',
              'hover:scale-[1.03] active:scale-[0.97]',
              'transition-all duration-300 ease-out',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2'
            )}
          >
            {/* Mic icon with pulse */}
            <div className="relative">
              <Mic className="h-5 w-5" />
              <div className="absolute inset-0 animate-ping rounded-full bg-white/30 group-hover:bg-white/40" />
            </div>
            <span>{t('welcome.startButton')}</span>
          </button>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5, ease: 'easeOut' }}
          className="pt-4"
        >
          <TrustBanner variant="welcome" />
        </motion.div>
      </section>
    </div>
  );
};
