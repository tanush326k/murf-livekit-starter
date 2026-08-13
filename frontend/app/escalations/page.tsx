'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'motion/react';
import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Clock,
  Filter,
  LifeBuoy,
  PhoneCall,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';
import { LanguageProvider, useLanguage } from '@/hooks/useLanguage';
import { LanguageSelector } from '@/components/moneybuddy/language-selector';

interface EscalationRecord {
  reference_id: string;
  caller_id?: string;
  caller_name: string;
  reason: string;
  summary: string;
  what_checked: string;
  urgency: string;
  language: string;
  preferred_followup: string;
  callback_time: string;
  status: string;
  created_at: string;
}

function EscalationsDashboardContent() {
  const { t, language } = useLanguage();

  const [records, setRecords] = useState<EscalationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState('');

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [urgencyFilter, setUrgencyFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const fetchEscalations = useCallback(async () => {
    try {
      const res = await fetch('/api/escalations');
      if (!res.ok) throw new Error('Failed to fetch escalations');
      const data = await res.json();
      setRecords(data);
      setError(null);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Escalations fetch error:', err);
      setError(
        language === 'hi'
          ? 'सहायता टिकट लोड करने में असमर्थ। पुनः प्रयास जारी है...'
          : 'Unable to load escalation tickets. Retrying in background...'
      );
    } finally {
      setLoading(false);
    }
  }, [language]);

  useEffect(() => {
    fetchEscalations();
    const interval = setInterval(fetchEscalations, 15000);
    return () => clearInterval(interval);
  }, [fetchEscalations]);

  const isHi = language === 'hi';
  const labels = {
    title: isHi ? 'मनीबडी मानव सहायता केंद्र' : 'MoneyBuddy Banking Support Center',
    subtitle: isHi ? 'वॉयस एजेंट से मानव विशेषज्ञ सहायता अनुरोध' : 'Human escalation requests generated from voice agent sessions',
    totalTickets: isHi ? 'कुल सहायता टिकट' : 'Total Tickets',
    openTickets: isHi ? 'खुले टिकट' : 'Open Requests',
    highUrgency: isHi ? 'उच्च / आपातकालीन' : 'High / Emergency',
    resolved: isHi ? 'समाधान किए गए' : 'Resolved',
    searchPlaceholder: isHi ? 'संदर्भ आईडी, नाम या कारण से खोजें...' : 'Search by Ref ID, caller name, or reason...',
    urgencyLabel: isHi ? 'आपातकाल स्तर' : 'Urgency',
    statusLabel: isHi ? 'स्थिति' : 'Status',
    allUrgency: isHi ? 'सभी स्तर' : 'All Urgency',
    allStatus: isHi ? 'सभी स्थितियां' : 'All Status',
    reset: isHi ? 'फ़िल्टर रीसेट करें' : 'Reset Filters',
    emptyText: isHi ? 'अभी तक कोई मानव सहायता टिकट नहीं है। सब कुछ स्पष्ट है!' : 'No escalation requests recorded yet. All clear!',
    thRefId: isHi ? 'संदर्भ आईडी' : 'Ref ID',
    thTime: isHi ? 'समय' : 'Date / Time',
    thCaller: isHi ? 'कॉलर का नाम' : 'Caller Name',
    thReason: isHi ? 'कारण' : 'Reason',
    thSummary: isHi ? 'सारांश (गोपनीयता संरक्षित)' : 'Summary (Sanitized)',
    thUrgency: isHi ? 'आपातकाल' : 'Urgency',
    thFollowup: isHi ? 'संपर्क समय' : 'Preferred Follow-up',
    thStatus: isHi ? 'स्थिति' : 'Status',
  };

  // Filtered records logic
  const filteredRecords = records.filter((r) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      (r.reference_id && r.reference_id.toLowerCase().includes(q)) ||
      (r.caller_name && r.caller_name.toLowerCase().includes(q)) ||
      (r.reason && r.reason.toLowerCase().includes(q)) ||
      (r.summary && r.summary.toLowerCase().includes(q));

    const matchesUrgency = !urgencyFilter || (r.urgency || '').toLowerCase() === urgencyFilter.toLowerCase();
    const matchesStatus = !statusFilter || (r.status || '').toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesUrgency && matchesStatus;
  });

  const totalCount = records.length;
  const openCount = records.filter((r) => (r.status || 'open').toLowerCase() === 'open').length;
  const highCount = records.filter((r) => ['high', 'emergency'].includes((r.urgency || '').toLowerCase())).length;
  const resolvedCount = records.filter((r) => (r.status || '').toLowerCase() === 'resolved').length;

  return (
    <div className="min-h-screen bg-background text-foreground px-4 py-6 md:px-8 md:py-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-border/40">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <LifeBuoy className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <span className="text-primary font-bold">MoneyBuddy</span> {labels.title.replace('MoneyBuddy ', '')}
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground mt-0.5">{labels.subtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-end sm:self-auto flex-wrap">
          <Link
            href="/analytics"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-foreground/80 hover:text-foreground bg-muted/60 hover:bg-muted border border-border/40 transition-all shadow-sm"
          >
            <BarChart3 className="h-3.5 w-3.5 text-primary" />
            <span>{t('nav.analytics')}</span>
          </Link>
          <Link
            href="/"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-foreground/80 hover:text-foreground bg-muted/60 hover:bg-muted border border-border/40 transition-all shadow-sm"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>{t('nav.backToAgent')}</span>
          </Link>
          <LanguageSelector />
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="mt-4 p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs font-medium flex items-center gap-2">
          <span>⚠️ {error}</span>
        </div>
      )}

      {/* Stats Cards */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Tickets */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-2xl mb-glass border border-border/40 flex flex-col gap-1"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {labels.totalTickets}
            </span>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <LifeBuoy className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono text-foreground mt-2">{totalCount}</span>
        </motion.div>

        {/* Open Requests */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="p-5 rounded-2xl mb-glass border border-emerald-500/20 bg-emerald-500/5 flex flex-col gap-1"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400/90 uppercase tracking-wider">
              {labels.openTickets}
            </span>
            <div className="p-2 rounded-lg bg-emerald-500/15 text-emerald-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono text-emerald-400 mt-2">{openCount}</span>
        </motion.div>

        {/* High / Emergency */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-5 rounded-2xl mb-glass border border-rose-500/20 bg-rose-500/5 flex flex-col gap-1"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400/90 uppercase tracking-wider">
              {labels.highUrgency}
            </span>
            <div className="p-2 rounded-lg bg-rose-500/15 text-rose-400">
              <ShieldAlert className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono text-rose-400 mt-2">{highCount}</span>
        </motion.div>

        {/* Resolved */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="p-5 rounded-2xl mb-glass border border-sky-500/20 bg-sky-500/5 flex flex-col gap-1"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-sky-400/90 uppercase tracking-wider">
              {labels.resolved}
            </span>
            <div className="p-2 rounded-lg bg-sky-500/15 text-sky-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono text-sky-400 mt-2">{resolvedCount}</span>
        </motion.div>
      </div>

      {/* Filter & Search Bar */}
      <div className="mt-6 p-4 rounded-2xl mb-glass border border-border/40 flex flex-wrap items-center gap-3 text-xs">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[220px]">
          <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder={labels.searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-card border border-border/40 rounded-lg text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary text-xs"
          />
        </div>

        {/* Urgency Filter */}
        <select
          value={urgencyFilter}
          onChange={(e) => setUrgencyFilter(e.target.value)}
          className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">{labels.allUrgency}</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="emergency">Emergency</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">{labels.allStatus}</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>

        {(searchQuery || urgencyFilter || statusFilter) && (
          <button
            onClick={() => {
              setSearchQuery('');
              setUrgencyFilter('');
              setStatusFilter('');
            }}
            className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2"
          >
            {labels.reset}
          </button>
        )}
      </div>

      {/* Escalation Tickets Table */}
      <div className="mt-6 rounded-2xl mb-glass border border-border/40 overflow-hidden">
        {filteredRecords.length === 0 ? (
          <div className="py-20 text-center flex flex-col items-center justify-center gap-2 text-muted-foreground">
            <CheckCircle2 className="h-10 w-10 text-emerald-400/50 mb-1" />
            <p className="text-xs font-medium">{labels.emptyText}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border/30 bg-muted/20 text-muted-foreground uppercase text-[10px] tracking-wider">
                  <th className="py-3.5 px-4">{labels.thRefId}</th>
                  <th className="py-3.5 px-4">{labels.thTime}</th>
                  <th className="py-3.5 px-4">{labels.thCaller}</th>
                  <th className="py-3.5 px-4">{labels.thReason}</th>
                  <th className="py-3.5 px-4">{labels.thSummary}</th>
                  <th className="py-3.5 px-4">{labels.thUrgency}</th>
                  <th className="py-3.5 px-4">{labels.thFollowup}</th>
                  <th className="py-3.5 px-4">{labels.thStatus}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {filteredRecords.map((r) => {
                  const urg = (r.urgency || 'low').toLowerCase();
                  const urgClass =
                    urg === 'emergency'
                      ? 'bg-purple-500/15 text-purple-400 border-purple-500/30'
                      : urg === 'high'
                      ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                      : urg === 'medium'
                      ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                      : 'bg-sky-500/15 text-sky-400 border-sky-500/30';

                  const st = (r.status || 'open').toLowerCase();
                  const statusClass =
                    st === 'resolved'
                      ? 'bg-slate-500/15 text-slate-400'
                      : st === 'in_progress'
                      ? 'bg-sky-500/15 text-sky-400'
                      : 'bg-emerald-500/15 text-emerald-400';

                  const dt = r.created_at ? new Date(r.created_at).toLocaleString() : '-';

                  return (
                    <tr key={r.reference_id} className="hover:bg-muted/10 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-primary text-[11px]">{r.reference_id}</td>
                      <td className="py-3.5 px-4 text-muted-foreground whitespace-nowrap">{dt}</td>
                      <td className="py-3.5 px-4 font-medium text-foreground">{r.caller_name || 'Anonymous'}</td>
                      <td className="py-3.5 px-4 text-foreground/90 font-medium">{r.reason || '-'}</td>
                      <td className="py-3.5 px-4 text-muted-foreground max-w-xs truncate" title={r.summary}>
                        {r.summary || '-'}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-1 rounded-md border font-semibold text-[10px] uppercase ${urgClass}`}>
                          {r.urgency || 'normal'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-muted-foreground">
                        {r.preferred_followup || r.callback_time ? `${r.preferred_followup || ''} ${r.callback_time || ''}`.trim() : '-'}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-1 rounded-md font-semibold text-[10px] uppercase ${statusClass}`}>
                          {r.status || 'open'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="mt-8 flex justify-between items-center text-[11px] text-muted-foreground/60">
        <span className="flex items-center gap-1.5">
          <RefreshCw className="h-3 w-3 animate-spin text-primary" />
          <span>Auto-polling active (15s)</span>
        </span>
        <span>{lastRefreshed ? `Last refreshed: ${lastRefreshed}` : ''}</span>
      </footer>
    </div>
  );
}

export default function EscalationsPage() {
  return (
    <LanguageProvider>
      <EscalationsDashboardContent />
    </LanguageProvider>
  );
}
