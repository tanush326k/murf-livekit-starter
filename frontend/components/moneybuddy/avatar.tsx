'use client';

import { type ComponentProps } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { type AgentState } from '@livekit/components-react';
import { type CustomAgentState } from '@/components/moneybuddy/state-indicator';
import { cn } from '@/lib/shadcn/utils';

interface MoneyBuddyAvatarProps extends ComponentProps<'div'> {
  state?: CustomAgentState | 'idle';
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: 'w-20 h-20',
  md: 'w-32 h-32',
  lg: 'w-44 h-44',
};

const innerSizeMap = {
  sm: 'w-16 h-16',
  md: 'w-24 h-24',
  lg: 'w-36 h-36',
};

function getStateStyles(state: MoneyBuddyAvatarProps['state']) {
  switch (state) {
    case 'listening':
      return {
        ringClass: 'mb-animate-listening',
        glowColor: 'shadow-[0_0_30px_var(--mb-glow-listening)]',
        innerBg: 'bg-gradient-to-br from-emerald-400/20 to-teal-500/20',
        eyeAnimation: 'scale-y-110',
      };
    case 'speaking':
      return {
        ringClass: 'mb-animate-speaking',
        glowColor: 'shadow-[0_0_30px_var(--mb-glow-speaking)]',
        innerBg: 'bg-gradient-to-br from-sky-400/20 to-blue-500/20',
        eyeAnimation: 'scale-100',
      };
    case 'thinking':
      return {
        ringClass: 'mb-animate-pulse-ring',
        glowColor: 'shadow-[0_0_20px_var(--mb-glow)]',
        innerBg: 'bg-gradient-to-br from-amber-400/15 to-orange-500/15',
        eyeAnimation: 'scale-90',
      };
    case 'connecting':
    case 'initializing':
      return {
        ringClass: '',
        glowColor: 'shadow-[0_0_15px_var(--mb-glow)]',
        innerBg: 'bg-gradient-to-br from-amber-400/10 to-yellow-500/10',
        eyeAnimation: 'scale-95',
      };
    case 'ended':
      return {
        ringClass: '',
        glowColor: '',
        innerBg: 'bg-gradient-to-br from-gray-400/10 to-gray-500/10',
        eyeAnimation: 'scale-100',
      };
    default:
      return {
        ringClass: 'mb-animate-pulse-ring',
        glowColor: 'shadow-[0_0_20px_var(--mb-glow)]',
        innerBg: 'bg-gradient-to-br from-emerald-400/10 to-teal-500/10',
        eyeAnimation: 'scale-100',
      };
  }
}

export function MoneyBuddyAvatar({
  state = 'idle',
  size = 'lg',
  className,
  ...props
}: MoneyBuddyAvatarProps) {
  const styles = getStateStyles(state);
  const isConnecting = state === 'connecting' || state === 'initializing';
  const isSpeaking = state === 'speaking';
  const isListening = state === 'listening';
  const isEnded = state === 'ended';

  return (
    <div
      className={cn('relative flex items-center justify-center', sizeMap[size], className)}
      {...props}
    >
      {/* Outer animated ring */}
      <div
        className={cn(
          'absolute inset-0 rounded-full transition-all duration-700',
          styles.ringClass,
          styles.glowColor
        )}
      >
        {/* Gradient border ring */}
        <div
          className={cn(
            'absolute inset-0 rounded-full',
            'bg-gradient-to-tr from-emerald-500/40 via-teal-400/30 to-sky-500/40',
            'dark:from-emerald-400/30 dark:via-teal-300/20 dark:to-sky-400/30',
            isEnded && 'opacity-30',
          )}
          style={{ padding: '2px' }}
        >
          <div className="h-full w-full rounded-full bg-background" />
        </div>
      </div>

      {/* Connecting spinner ring */}
      <AnimatePresence>
        {isConnecting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 mb-animate-spin-slow"
          >
            <svg viewBox="0 0 100 100" className="h-full w-full">
              <defs>
                <linearGradient id="mb-spinner-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="var(--mb-emerald)" stopOpacity="0.8" />
                  <stop offset="50%" stopColor="var(--mb-gold)" stopOpacity="0.6" />
                  <stop offset="100%" stopColor="var(--mb-emerald)" stopOpacity="0" />
                </linearGradient>
              </defs>
              <circle
                cx="50"
                cy="50"
                r="47"
                fill="none"
                stroke="url(#mb-spinner-gradient)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeDasharray="100 200"
              />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Inner avatar face */}
      <motion.div
        className={cn(
          'relative z-10 flex items-center justify-center rounded-full',
          'border border-white/10 dark:border-white/5',
          'transition-colors duration-500',
          innerSizeMap[size],
          styles.innerBg,
          !isEnded && !isConnecting && 'mb-animate-float'
        )}
        animate={{
          scale: isSpeaking ? [1, 1.03, 1] : isListening ? [1, 1.02, 1] : 1,
        }}
        transition={{
          duration: isSpeaking ? 1.2 : 2,
          repeat: isSpeaking || isListening ? Infinity : 0,
          ease: 'easeInOut',
        }}
      >
        {/* Face SVG */}
        <svg
          viewBox="0 0 80 80"
          className={cn(
            'w-3/5 h-3/5',
            isEnded ? 'text-muted-foreground/40' : 'text-primary',
            'transition-colors duration-500'
          )}
          fill="none"
        >
          {/* Left eye */}
          <motion.ellipse
            cx="28"
            cy="32"
            rx="4"
            ry="5"
            fill="currentColor"
            opacity="1"
            animate={{
              ry: isListening ? [5, 6, 5] : isSpeaking ? [5, 4.5, 5] : 5,
              opacity: isEnded ? 0.4 : 1,
            }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          />
          {/* Right eye */}
          <motion.ellipse
            cx="52"
            cy="32"
            rx="4"
            ry="5"
            fill="currentColor"
            opacity="1"
            animate={{
              ry: isListening ? [5, 6, 5] : isSpeaking ? [5, 4.5, 5] : 5,
              opacity: isEnded ? 0.4 : 1,
            }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut', delay: 0.1 }}
          />
          {/* Eye highlights */}
          <circle cx="30" cy="30" r="1.5" fill="white" opacity={isEnded ? 0.1 : 0.6} />
          <circle cx="54" cy="30" r="1.5" fill="white" opacity={isEnded ? 0.1 : 0.6} />

          {/* Mouth — changes based on state */}
          {isSpeaking ? (
            <motion.ellipse
              cx="40"
              cy="50"
              rx="8"
              ry="3"
              fill="currentColor"
              opacity={0.7}
              animate={{ ry: [3, 6, 4, 7, 3] }}
              transition={{ duration: 0.8, repeat: Infinity, ease: 'easeInOut' }}
            />
          ) : isListening ? (
            <circle cx="40" cy="50" r="4" fill="currentColor" opacity={0.5} />
          ) : (
            <motion.path
              d="M30 48 Q40 56 50 48"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              fill="none"
              opacity="0.7"
              animate={{
                opacity: isEnded ? 0.3 : 0.7,
              }}
            />
          )}
        </svg>

        {/* Connecting dots overlay */}
        <AnimatePresence>
          {isConnecting && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute bottom-3 flex gap-1.5"
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-1.5 w-1.5 rounded-full bg-amber-400"
                  style={{
                    animation: `mb-dot-bounce 1.2s ease-in-out infinite`,
                    animationDelay: `${i * 0.15}s`,
                  }}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Listening indicator ears */}
        <AnimatePresence>
          {isListening && (
            <>
              <motion.div
                initial={{ opacity: 0, x: 5 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 5 }}
                className="absolute -left-2 top-1/2 -translate-y-1/2"
              >
                <div className="flex gap-0.5">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-0.5 rounded-full bg-primary/60"
                      style={{
                        animation: `mb-wave-bar 0.8s ease-in-out infinite`,
                        animationDelay: `${i * 0.1}s`,
                        height: `${8 + i * 4}px`,
                      }}
                    />
                  ))}
                </div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -5 }}
                className="absolute -right-2 top-1/2 -translate-y-1/2"
              >
                <div className="flex gap-0.5">
                  {[2, 1, 0].map((i) => (
                    <div
                      key={i}
                      className="w-0.5 rounded-full bg-primary/60"
                      style={{
                        animation: `mb-wave-bar 0.8s ease-in-out infinite`,
                        animationDelay: `${i * 0.1}s`,
                        height: `${8 + i * 4}px`,
                      }}
                    />
                  ))}
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
