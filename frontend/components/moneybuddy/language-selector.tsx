'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Globe, Check, ChevronDown } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { LANGUAGES, type Language } from '@/lib/i18n';
import { cn } from '@/lib/shadcn/utils';

interface LanguageSelectorProps {
  className?: string;
}

export function LanguageSelector({ className }: LanguageSelectorProps) {
  const { language, setLanguage } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLang = LANGUAGES.find((l) => l.code === language) ?? LANGUAGES[0];

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Escape
  useEffect(() => {
    function handleEsc(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false);
    }
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, []);

  const handleSelect = (code: Language) => {
    setLanguage(code);
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className={cn('relative', className)}>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 rounded-full px-3.5 py-2',
          'text-sm font-medium transition-all duration-200',
          'mb-glass hover:bg-white/10 dark:hover:bg-white/8',
          'text-foreground/80 hover:text-foreground',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50'
        )}
        aria-label="Select language"
        aria-expanded={isOpen}
      >
        <Globe className="h-4 w-4 text-primary" />
        <span className="hidden sm:inline">{currentLang.nativeLabel}</span>
        <span className="sm:hidden">{currentLang.flag}</span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className={cn(
              'absolute right-0 top-full mt-2 z-50',
              'min-w-[200px] rounded-xl overflow-hidden',
              'bg-card border border-border/50',
              'shadow-xl shadow-black/10 dark:shadow-black/30',
              'backdrop-blur-xl'
            )}
          >
            <div className="p-1.5">
              {LANGUAGES.map((lang) => {
                const isSelected = lang.code === language;
                return (
                  <button
                    key={lang.code}
                    onClick={() => handleSelect(lang.code)}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2.5',
                      'text-sm transition-colors duration-150',
                      'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/30',
                      isSelected
                        ? 'bg-primary/10 text-primary dark:bg-primary/15'
                        : 'text-foreground/70 hover:bg-accent hover:text-foreground'
                    )}
                  >
                    <span className="text-lg leading-none">{lang.flag}</span>
                    <div className="flex flex-col items-start">
                      <span className="font-medium">{lang.nativeLabel}</span>
                      {lang.nativeLabel !== lang.label && (
                        <span className="text-xs text-muted-foreground">{lang.label}</span>
                      )}
                    </div>
                    {isSelected && (
                      <Check className="ml-auto h-4 w-4 text-primary" />
                    )}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
