'use client';

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { User, Bot } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { cn } from '@/lib/shadcn/utils';

interface TranscriptPanelProps {
  messages: ReceivedMessage[];
  agentState?: AgentState;
  className?: string;
}

export function TranscriptPanel({ messages, agentState, className }: TranscriptPanelProps) {
  const { t } = useLanguage();
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div
      className={cn(
        'flex flex-col h-full rounded-2xl overflow-hidden',
        'bg-card/50 dark:bg-card/30',
        'border border-border/30',
        'backdrop-blur-sm',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3.5 border-b border-border/20">
        <div className="h-2 w-2 rounded-full bg-primary/60" />
        <h3 className="text-sm font-semibold text-foreground/80">
          Live Transcript
        </h3>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4 mb-scrollbar"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="w-12 h-12 rounded-full bg-muted/50 flex items-center justify-center mb-3">
              <Bot className="h-5 w-5 text-muted-foreground/50" />
            </div>
            <p className="text-sm text-muted-foreground/60">{t('transcript.empty')}</p>
          </div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {messages.map((receivedMessage) => {
                const { id, timestamp, from, message } = receivedMessage;
                const isUser = from?.isLocal === true;
                const time = new Date(timestamp);
                const timeStr = time.toLocaleTimeString(undefined, {
                  hour: '2-digit',
                  minute: '2-digit',
                });

                return (
                  <motion.div
                    key={id}
                    initial={{ opacity: 0, y: 12, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                    className={cn(
                      'flex gap-2.5',
                      isUser ? 'flex-row-reverse' : 'flex-row'
                    )}
                  >
                    {/* Avatar icon */}
                    <div
                      className={cn(
                        'shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-1',
                        isUser
                          ? 'bg-primary/15 dark:bg-primary/10'
                          : 'bg-sky-500/15 dark:bg-sky-400/10'
                      )}
                    >
                      {isUser ? (
                        <User className="h-3.5 w-3.5 text-primary" />
                      ) : (
                        <Bot className="h-3.5 w-3.5 text-sky-500 dark:text-sky-400" />
                      )}
                    </div>

                    {/* Message bubble */}
                    <div
                      className={cn(
                        'max-w-[80%] flex flex-col gap-1',
                        isUser ? 'items-end' : 'items-start'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-semibold text-muted-foreground/70 uppercase tracking-wide">
                          {isUser ? t('transcript.you') : t('transcript.moneybuddy')}
                        </span>
                        <span className="text-[10px] text-muted-foreground/40">{timeStr}</span>
                      </div>
                      <div
                        className={cn(
                          'rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                          isUser
                            ? 'bg-primary/10 dark:bg-primary/15 text-foreground rounded-tr-sm'
                            : 'bg-muted/60 dark:bg-muted/40 text-foreground/90 rounded-tl-sm'
                        )}
                      >
                        {message}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {/* Thinking indicator */}
            <AnimatePresence>
              {agentState === 'thinking' && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="flex gap-2.5"
                >
                  <div className="w-7 h-7 rounded-full bg-sky-500/15 dark:bg-sky-400/10 flex items-center justify-center mt-1">
                    <Bot className="h-3.5 w-3.5 text-sky-500 dark:text-sky-400" />
                  </div>
                  <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-muted/60 dark:bg-muted/40 px-4 py-3">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50"
                        style={{
                          animation: `mb-dot-bounce 1.2s ease-in-out infinite`,
                          animationDelay: `${i * 0.2}s`,
                        }}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
