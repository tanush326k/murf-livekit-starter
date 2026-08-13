'use client';

import { useMemo, useState } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import Link from 'next/link';
import { ShieldCheck, Wallet, Landmark, Smartphone, BookOpen, BarChart3, LifeBuoy } from 'lucide-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { LanguageSelector } from '@/components/moneybuddy/language-selector';
import { TopicModal, type TopicContent } from '@/components/moneybuddy/topic-modal';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { LanguageProvider, useLanguage } from '@/hooks/useLanguage';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function HeaderNavLinks() {
  const { t } = useLanguage();
  return (
    <div className="flex items-center gap-2">
      <Link
        href="/analytics"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-foreground/80 hover:text-foreground bg-muted/50 hover:bg-muted/80 border border-border/40 transition-colors"
      >
        <BarChart3 className="h-3.5 w-3.5 text-primary" />
        <span>{t('nav.analytics')}</span>
      </Link>
      <Link
        href="/escalations"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-foreground/80 hover:text-foreground bg-muted/50 hover:bg-muted/80 border border-border/40 transition-colors"
      >
        <LifeBuoy className="h-3.5 w-3.5 text-emerald-400" />
        <span>{t('nav.humanSupport')}</span>
      </Link>
    </div>
  );
}

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

const FINANCIAL_TOPICS: TopicContent[] = [
  {
    id: 'savings',
    title: 'Savings & Accounts',
    icon: Wallet,
    description: 'A savings account is a basic type of bank account that allows you to deposit money, keep it safe, and earn a small amount of interest.',
    points: [
      { title: 'Basic account types', text: 'Common accounts include Savings Accounts (for daily use and earning interest), Current Accounts (for businesses), and Fixed Deposits (locking money for a set period for higher interest).' },
      { title: 'How savings accounts work', text: 'When you deposit money into a savings account, the bank pays you interest on your balance over time. You can withdraw your money when needed using ATMs, bank branches, or digital banking.' },
      { title: 'Before opening an account', text: 'Consider factors like minimum balance requirements, interest rates, ATM availability, and hidden fees or service charges.' }
    ]
  },
  {
    id: 'schemes',
    title: 'Government Schemes',
    icon: Landmark,
    description: 'Government schemes are financial programs created by the government to support citizens with banking access, savings, insurance, and pensions.',
    points: [
      { title: 'Pradhan Mantri Jan Dhan Yojana (PMJDY)', text: 'A scheme ensuring access to financial services like banking, savings, remittance, credit, insurance, and pension in an affordable manner, often with zero minimum balance.' },
      { title: 'Sukanya Samriddhi Yojana (SSY)', text: 'A savings scheme designed for the betterment of the girl child, offering a high interest rate and tax benefits for parents or guardians.' },
      { title: 'General explanation', text: 'These schemes are designed to promote financial inclusion, providing safety nets and secure savings avenues for various demographics.' }
    ],
    disclaimer: 'This information is a general summary of government schemes. MoneyBuddy is an informational tool and is NOT an official government or banking service. Please consult official government portals for current eligibility and application details.'
  },
  {
    id: 'digital',
    title: 'Digital Banking',
    icon: Smartphone,
    description: 'Digital banking allows you to perform financial transactions over the internet without visiting a physical bank branch.',
    points: [
      { title: 'UPI Basics', text: 'Unified Payments Interface (UPI) lets you transfer money instantly between bank accounts using a smartphone. It operates 24/7 and only requires a Virtual Payment Address (UPI ID) or phone number.' },
      { title: 'Mobile Banking', text: 'Bank-provided smartphone apps let you check balances, transfer funds, pay bills, and manage accounts securely from your phone.' },
      { title: 'Online Bank Transfers', text: 'Systems like NEFT, RTGS, and IMPS allow you to electronically transfer funds to other accounts for different needs based on speed and amount limits.' },
      { title: 'Safe Digital Practices', text: 'Always use secure networks, verify the recipient before sending money, log out of banking apps when done, and regularly monitor your transaction history.' }
    ]
  },
  {
    id: 'safety',
    title: 'Financial Safety',
    icon: ShieldCheck,
    description: 'Protecting your financial information is critical in the digital age. Scammers often use deception to steal credentials.',
    points: [
      { title: 'Never share credentials', text: 'Do not share your OTPs (One Time Passwords), PINs, passwords, CVV numbers, or full banking details with anyone, even if they claim to be from the bank.' },
      { title: 'Recognizing phishing', text: 'Be cautious of urgent messages, unverified links in SMS or emails, and calls asking you to download screen-sharing apps or update KYC immediately.' },
      { title: 'If suspicious activity occurs', text: 'Immediately block your card or freeze your account via your banking app, and contact your bank’s official customer care number. Report the fraud to the national cybercrime portal.' }
    ]
  },
  {
    id: 'basics',
    title: 'Money Basics',
    icon: BookOpen,
    description: 'Mastering the fundamentals of money management helps build a secure financial future and reduces financial stress.',
    points: [
      { title: 'Budgeting', text: 'Creating a budget means tracking your income and expenses. It helps you understand where your money goes and ensures you do not spend more than you earn.' },
      { title: 'Saving', text: 'Pay yourself first. Aim to set aside a portion of your income as savings before spending on non-essentials. Building an emergency fund is a critical first step.' },
      { title: 'Managing daily expenses', text: 'Distinguish between "needs" (rent, groceries) and "wants" (dining out, entertainment). Small, daily expenses can add up quickly over a month.' },
      { title: 'Loans and interest', text: 'A loan is borrowed money that must be paid back with interest. Understanding interest rates helps you calculate the true cost of borrowing and avoid debt traps.' }
    ]
  }
];

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const [selectedTopic, setSelectedTopic] = useState<TopicContent | null>(null);

  const tokenSource = useMemo(() => {
    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSource(appConfig);
    }
    return TokenSource.custom(async () => {
      let userId = localStorage.getItem('moneybuddy_user_id');
      if (!userId) {
        userId = `voice_assistant_user_${Math.floor(Math.random() * 100000)}`;
        localStorage.setItem('moneybuddy_user_id', userId);
      }

      const res = await fetch('/api/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId }),
      });

      if (!res.ok) {
        throw new Error('Failed to fetch token');
      }

      return await res.json();
    });
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <LanguageProvider>
      <AgentSessionProvider session={session}>
        <AppSetup />

        {/* MoneyBuddy Header */}
        <header className="fixed top-0 left-0 z-50 flex w-full items-center justify-between px-4 py-3 md:px-6 md:py-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <span className="text-sm font-bold tracking-wide text-foreground">
              MoneyBuddy
            </span>
          </div>
          <div className="flex items-center gap-3">
            <HeaderNavLinks />
            <LanguageSelector />
          </div>
        </header>

        <main className="flex flex-col min-h-screen pt-16 mb-glow-bg">
          {/* Hero Section containing Voice Agent */}
          <section className="relative w-full flex-1 flex flex-col justify-center min-h-[85vh]">
            <ViewController appConfig={appConfig} />
          </section>

          {/* Financial Information Cards Section */}
          <section className="w-full max-w-6xl mx-auto px-6 py-20">
            <div className="text-center mb-12">
              <h2 className="text-2xl font-bold text-foreground">Explore Financial Topics</h2>
              <p className="text-muted-foreground mt-3 text-sm max-w-xl mx-auto">
                MoneyBuddy is here to help you learn about banking, government schemes, and digital safety.
              </p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {FINANCIAL_TOPICS.map((card) => (
                <button 
                  key={card.id} 
                  onClick={() => setSelectedTopic(card)}
                  className="mb-glass rounded-2xl p-6 flex flex-col items-start gap-4 hover:bg-white/5 transition-all border border-border/40 text-left hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-primary/50"
                  aria-label={`Learn more about ${card.title}`}
                >
                  <div className="p-3 rounded-xl bg-primary/10">
                    <card.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground tracking-tight">{card.title}</h3>
                    <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{card.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Footer with Disclaimer */}
          <footer className="w-full border-t border-border/50 bg-card/30 mt-auto">
            <div className="max-w-5xl mx-auto px-6 py-8 text-center text-xs text-muted-foreground leading-relaxed">
              <p>
                MoneyBuddy provides general financial information. For applications, transactions, 
                eligibility, or account-specific assistance, use the relevant official bank or government website.
              </p>
              <p className="mt-3 opacity-60">© {new Date().getFullYear()} MoneyBuddy. All rights reserved.</p>
            </div>
          </footer>
        </main>
        <StartAudioButton label="Start Audio" />
        <Toaster
          icons={{
            warning: <WarningIcon weight="bold" />,
          }}
          position="top-center"
          className="toaster group"
          style={
            {
              '--normal-bg': 'var(--popover)',
              '--normal-text': 'var(--popover-foreground)',
              '--normal-border': 'var(--border)',
            } as React.CSSProperties
          }
        />
        
        <TopicModal 
          isOpen={selectedTopic !== null} 
          topic={selectedTopic} 
          onClose={() => setSelectedTopic(null)} 
        />
      </AgentSessionProvider>
    </LanguageProvider>
  );
}
