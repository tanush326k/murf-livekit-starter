'use client';

import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X } from 'lucide-react';
import { cn } from '@/lib/shadcn/utils';

export interface TopicContent {
  id: string;
  title: string;
  icon: React.ElementType;
  description: string;
  points: {
    title?: string;
    text: string;
  }[];
  disclaimer?: string;
}

interface TopicModalProps {
  topic: TopicContent | null;
  isOpen: boolean;
  onClose: () => void;
}

export function TopicModal({ topic, isOpen, onClose }: TopicModalProps) {
  // Prevent scrolling on body when modal is open
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && topic && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
              'relative flex w-full max-w-2xl flex-col overflow-hidden rounded-3xl',
              'bg-card border border-border/50 shadow-2xl shadow-primary/10',
              'max-h-[90vh]'
            )}
            role="dialog"
            aria-modal="true"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border/50 px-6 py-5">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-primary/10 p-2.5">
                  <topic.icon className="h-6 w-6 text-primary" />
                </div>
                <h2 className="text-xl font-bold tracking-tight text-foreground">
                  {topic.title}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
              <p className="mb-6 text-base leading-relaxed text-muted-foreground">
                {topic.description}
              </p>

              <div className="space-y-5">
                {topic.points.map((point, index) => (
                  <div key={index} className="flex flex-col gap-1">
                    {point.title && (
                      <h3 className="font-semibold text-foreground">
                        {point.title}
                      </h3>
                    )}
                    <p className="text-sm leading-relaxed text-muted-foreground">
                      {point.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Disclaimer / Footer */}
            {topic.disclaimer && (
              <div className="bg-muted/50 px-6 py-4 text-xs leading-relaxed text-muted-foreground border-t border-border/50">
                <span className="font-semibold text-foreground mr-1">Note:</span>
                {' '}{topic.disclaimer}
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
