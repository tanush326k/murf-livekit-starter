'use client';

import { motion, AnimatePresence } from 'motion/react';
import { type AgentState } from '@livekit/components-react';
import { Mic, Volume2, Loader, Radio, CheckCircle, MicOff } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { cn } from '@/lib/shadcn/utils';

export type CustomAgentState = AgentState | 'ended' | 'mic-off' | 'connecting';

interface StateIndicatorProps {
  state: CustomAgentState;
  className?: string;
}

function getStateConfig(state: StateIndicatorProps['state'], t: (key: any) => string) {
  switch (state) {
    case 'listening':
      return {
        label: t('state.listening'),
        icon: Mic,
        colorClass: 'text-emerald-500 dark:text-emerald-400',
        bgClass: 'bg-emerald-500/10 dark:bg-emerald-400/10',
        dotClass: 'bg-emerald-500',
        animate: true,
      };
    case 'speaking':
      return {
        label: t('state.speaking'),
        icon: Volume2,
        colorClass: 'text-sky-500 dark:text-sky-400',
        bgClass: 'bg-sky-500/10 dark:bg-sky-400/10',
        dotClass: 'bg-sky-500',
        animate: true,
      };
    case 'thinking':
      return {
        label: t('state.thinking'),
        icon: Loader,
        colorClass: 'text-amber-500 dark:text-amber-400',
        bgClass: 'bg-amber-500/10 dark:bg-amber-400/10',
        dotClass: 'bg-amber-500',
        animate: true,
      };
    case 'connecting':
    case 'initializing':
      return {
        label: t('state.connecting'),
        icon: Radio,
        colorClass: 'text-amber-500 dark:text-amber-400',
        bgClass: 'bg-amber-500/10 dark:bg-amber-400/10',
        dotClass: 'bg-amber-500',
        animate: true,
      };
    case 'ended':
      return {
        label: t('state.ended'),
        icon: CheckCircle,
        colorClass: 'text-muted-foreground',
        bgClass: 'bg-muted',
        dotClass: 'bg-muted-foreground',
        animate: false,
      };
    case 'mic-off':
      return {
        label: 'Microphone is off',
        icon: MicOff,
        colorClass: 'text-destructive dark:text-red-400',
        bgClass: 'bg-destructive/10 dark:bg-red-500/10',
        dotClass: 'bg-destructive',
        animate: false,
      };
    default:
      return {
        label: t('state.ready'),
        icon: Mic,
        colorClass: 'text-primary',
        bgClass: 'bg-primary/10',
        dotClass: 'bg-primary',
        animate: false,
      };
  }
}

export function StateIndicator({ state, className }: StateIndicatorProps) {
  const { t } = useLanguage();
  const config = getStateConfig(state, t);
  const Icon = config.icon;

  return (
    <div className={cn('flex items-center justify-center', className)}>
      <AnimatePresence mode="wait">
        <motion.div
          key={state}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className={cn(
            'flex items-center gap-2.5 rounded-full px-4 py-2',
            config.bgClass,
            'transition-colors duration-300'
          )}
        >
          {/* Animated dot */}
          {config.animate && (
            <span className="relative flex h-2 w-2">
              <span
                className={cn(
                  'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
                  config.dotClass
                )}
              />
              <span
                className={cn(
                  'relative inline-flex h-2 w-2 rounded-full',
                  config.dotClass
                )}
              />
            </span>
          )}

          <Icon
            className={cn(
              'h-4 w-4',
              config.colorClass,
              state === 'thinking' && 'animate-spin'
            )}
          />

          <span className={cn('text-sm font-medium', config.colorClass)}>
            {config.label}
          </span>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
