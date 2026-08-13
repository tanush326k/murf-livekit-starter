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
  Globe,
  LifeBuoy,
  Phone,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  UserCheck,
  XCircle,
} from 'lucide-react';
import { LanguageProvider, useLanguage } from '@/hooks/useLanguage';
import { LanguageSelector } from '@/components/moneybuddy/language-selector';

interface SummaryData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  avg_latency_ms: number | null;
}

interface ChartsData {
  calls_over_time: Array<{ date: string; successful: number; failed: number }>;
  failure_distribution: Array<{ type: string; count: number }>;
  language_distribution: Array<{ language: string; count: number }>;
  financial_outcomes: Array<{ outcome: string; count: number }>;
}

interface CallAnalyticsRecord {
  call_id: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  channel: string;
  language: string;
  outcome: string;
  failure_type: string | null;
  success_reason: string | null;
  financial_outcome: string | null;
  escalation_created: number;
  avg_latency_ms: number | null;
  created_at: string;
}

interface EscalationRecord {
  reference_id: string;
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

function AnalyticsDashboardContent() {
  const { t, language } = useLanguage();

  // Filters state
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [channel, setChannel] = useState('');
  const [langFilter, setLangFilter] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('');

  // Active tab
  const [activeTab, setActiveTab] = useState<'history' | 'escalations'>('history');

  // Data states
  const [summary, setSummary] = useState<SummaryData>({
    total_calls: 0,
    successful_calls: 0,
    failed_calls: 0,
    success_rate: 0,
    avg_latency_ms: null,
  });
  const [charts, setCharts] = useState<ChartsData>({
    calls_over_time: [],
    failure_distribution: [],
    language_distribution: [],
    financial_outcomes: [],
  });
  const [records, setRecords] = useState<CallAnalyticsRecord[]>([]);
  const [escalations, setEscalations] = useState<EscalationRecord[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const buildQueryString = useCallback(() => {
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (channel) params.append('channel', channel);
    if (langFilter) params.append('language', langFilter);
    if (outcomeFilter) params.append('outcome', outcomeFilter);
    return params.toString();
  }, [dateFrom, dateTo, channel, langFilter, outcomeFilter]);

  const fetchData = useCallback(async () => {
    try {
      const qs = buildQueryString();
      const [sumRes, chartRes, listRes, escRes] = await Promise.all([
        fetch(`/api/analytics/summary?${qs}`),
        fetch(`/api/analytics/charts?${qs}`),
        fetch(`/api/analytics?${qs}`),
        fetch('/api/escalations'),
      ]);

      if (!sumRes.ok || !chartRes.ok || !listRes.ok) {
        throw new Error('Failed to fetch analytics from backend');
      }

      const sumData = await sumRes.json();
      const chartData = await chartRes.json();
      const listData = await listRes.json();
      const escData = await escRes.json().catch(() => []);

      setSummary(sumData);
      setCharts(chartData);
      setRecords(listData);
      setEscalations(escData);
      setError(null);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Analytics fetch error:', err);
      setError(
        language === 'hi'
          ? 'कॉल इतिहास लोड करने में असमर्थ। पुनः प्रयास जारी है...'
          : 'Unable to load call metrics. Retrying in background...'
      );
    } finally {
      setLoading(false);
    }
  }, [buildQueryString, language]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const resetFilters = () => {
    setDateFrom('');
    setDateTo('');
    setChannel('');
    setLangFilter('');
    setOutcomeFilter('');
  };

  // Multilingual text labels
  const isHi = language === 'hi';
  const labels = {
    title: isHi ? 'मनीबडी कॉल विश्लेषिकी' : 'MoneyBuddy Call Analytics',
    subtitle: isHi ? 'वास्तविक समय वॉयस एजेंट प्रदर्शन एवं मेट्रिक्स' : 'Real-time voice agent metrics & performance insights',
    totalCalls: isHi ? 'कुल कॉल' : 'Total Calls',
    successfulCalls: isHi ? 'सफल कॉल' : 'Successful Calls',
    failedCalls: isHi ? 'असफल कॉल' : 'Failed Calls',
    successRate: isHi ? 'सफलता दर' : 'Success Rate',
    avgLatency: isHi ? 'औसत वॉयस रिस्पॉन्स टाइम' : 'Avg Voice Latency',
    callHistory: isHi ? 'कॉल इतिहास' : 'Call History',
    escalations: isHi ? 'मानव सहायता टिकट' : 'Human Escalations',
    filterFrom: isHi ? 'से' : 'From',
    filterTo: isHi ? 'तक' : 'To',
    filterChannel: isHi ? 'चैनल' : 'Channel',
    filterLang: isHi ? 'भाषा' : 'Language',
    filterOutcome: isHi ? 'परिणाम' : 'Outcome',
    reset: isHi ? 'फ़िल्टर रीसेट करें' : 'Reset Filters',
    allChannels: isHi ? 'सभी चैनल' : 'All Channels',
    allLangs: isHi ? 'सभी भाषाएं' : 'All Languages',
    allOutcomes: isHi ? 'सभी परिणाम' : 'All Outcomes',
    timeline: isHi ? 'समय के साथ कॉल' : 'Calls Over Time',
    failureDist: isHi ? 'विफलता प्रकार वितरण' : 'Failure Type Breakdown',
    emptyHistory: isHi ? 'चुने गए फ़िल्टर के लिए कोई कॉल रिकॉर्ड नहीं मिला।' : 'No call records found for selected filters.',
    emptyEscalations: isHi ? 'अभी तक कोई मानव सहायता टिकट नहीं है।' : 'No escalation requests recorded yet.',
  };

  return (
    <div className="min-h-screen bg-background text-foreground px-4 py-6 md:px-8 md:py-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-border/40">
        <div className="flex items-center gap-3">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
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
            href="/escalations"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-foreground/80 hover:text-foreground bg-muted/60 hover:bg-muted border border-border/40 transition-all shadow-sm"
          >
            <LifeBuoy className="h-3.5 w-3.5 text-emerald-400" />
            <span>{t('nav.humanSupport')}</span>
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

      {/* Filter Bar */}
      <div className="mt-6 p-4 rounded-2xl mb-glass border border-border/40 flex flex-wrap items-center gap-3 text-xs">
        <div className="flex items-center gap-1.5 text-muted-foreground font-semibold uppercase tracking-wider text-[11px] mr-1">
          <Filter className="h-3.5 w-3.5 text-primary" />
          <span>Filters</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground">{labels.filterFrom}:</span>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground">{labels.filterTo}:</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        <select
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">{labels.allChannels}</option>
          <option value="browser">Browser</option>
          <option value="sip">SIP / Outbound</option>
        </select>

        <select
          value={langFilter}
          onChange={(e) => setLangFilter(e.target.value)}
          className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">{labels.allLangs}</option>
          <option value="English">English</option>
          <option value="Hindi">Hindi</option>
        </select>

        <select
          value={outcomeFilter}
          onChange={(e) => setOutcomeFilter(e.target.value)}
          className="bg-card border border-border/40 rounded-lg px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">{labels.allOutcomes}</option>
          <option value="successful">Successful</option>
          <option value="failed">Failed</option>
        </select>

        <button
          onClick={resetFilters}
          className="ml-auto text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
        >
          {labels.reset}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Calls */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-2xl mb-glass border border-border/40 flex flex-col gap-1 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {labels.totalCalls}
            </span>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Phone className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono tracking-tight text-foreground mt-2">
            {summary.total_calls}
          </span>
          <span className="text-[11px] text-muted-foreground/70">All recorded call sessions</span>
        </motion.div>

        {/* Successful Calls */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="p-5 rounded-2xl mb-glass border border-emerald-500/20 bg-emerald-500/5 flex flex-col gap-1 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400/90 uppercase tracking-wider">
              {labels.successfulCalls}
            </span>
            <div className="p-2 rounded-lg bg-emerald-500/15 text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono tracking-tight text-emerald-400 mt-2">
            {summary.successful_calls}
          </span>
          <span className="text-[11px] text-muted-foreground/70">Completed financial intent</span>
        </motion.div>

        {/* Failed Calls */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-5 rounded-2xl mb-glass border border-rose-500/20 bg-rose-500/5 flex flex-col gap-1 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400/90 uppercase tracking-wider">
              {labels.failedCalls}
            </span>
            <div className="p-2 rounded-lg bg-rose-500/15 text-rose-400">
              <XCircle className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono tracking-tight text-rose-400 mt-2">
            {summary.failed_calls}
          </span>
          <span className="text-[11px] text-muted-foreground/70">User decline / incomplete</span>
        </motion.div>

        {/* Success Rate */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="p-5 rounded-2xl mb-glass border border-amber-500/20 bg-amber-500/5 flex flex-col gap-1 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400/90 uppercase tracking-wider">
              {labels.successRate}
            </span>
            <div className="p-2 rounded-lg bg-amber-500/15 text-amber-400">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono tracking-tight text-amber-400 mt-2">
            {summary.success_rate}%
          </span>
          <span className="text-[11px] text-muted-foreground/70">Real database percentage</span>
        </motion.div>

        {/* Avg Latency */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-5 rounded-2xl mb-glass border border-sky-500/20 bg-sky-500/5 flex flex-col gap-1 relative overflow-hidden"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-sky-400/90 uppercase tracking-wider">
              {labels.avgLatency}
            </span>
            <div className="p-2 rounded-lg bg-sky-500/15 text-sky-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <span className="text-2xl font-bold font-mono tracking-tight text-sky-400 mt-2">
            {summary.avg_latency_ms !== null ? `${Math.round(summary.avg_latency_ms)} ms` : 'N/A'}
          </span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-[11px] text-muted-foreground/70">Turn-taking response</span>
            {summary.avg_latency_ms !== null && (
              <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                summary.avg_latency_ms < 500
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : summary.avg_latency_ms <= 900
                  ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                  : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              }`}>
                {summary.avg_latency_ms < 500 ? '<500ms (Excellent)' : summary.avg_latency_ms <= 900 ? '500-900ms (Acceptable)' : '>900ms'}
              </span>
            )}
          </div>
        </motion.div>
      </div>

      {/* Charts Section */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <div className="p-5 rounded-2xl mb-glass border border-border/40 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              <span>{labels.timeline}</span>
            </h3>
            <span className="text-xs text-muted-foreground">Daily breakdown</span>
          </div>

          <div className="h-44 w-full flex items-end justify-between gap-2 pt-4 px-2">
            {charts.calls_over_time.length === 0 ? (
              <div className="m-auto text-xs text-muted-foreground/60">No timeline data available</div>
            ) : (
              charts.calls_over_time.slice(-7).map((d, i) => {
                const total = d.successful + d.failed || 1;
                const succPct = (d.successful / total) * 100;
                const failPct = (d.failed / total) * 100;

                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                    <div className="w-full max-w-[32px] h-full flex flex-col justify-end bg-muted/20 rounded-md overflow-hidden">
                      <div style={{ height: `${failPct}%` }} className="bg-rose-500/80 transition-all duration-500" title={`${d.failed} failed`} />
                      <div style={{ height: `${succPct}%` }} className="bg-emerald-500/80 transition-all duration-500" title={`${d.successful} successful`} />
                    </div>
                    <span className="text-[10px] text-muted-foreground/70 font-mono">{d.date.slice(5)}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Failure Breakdown */}
        <div className="p-5 rounded-2xl mb-glass border border-border/40 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <XCircle className="h-4 w-4 text-rose-400" />
              <span>{labels.failureDist}</span>
            </h3>
            <span className="text-xs text-muted-foreground">Reason category</span>
          </div>

          <div className="flex-1 flex flex-col justify-center gap-3">
            {charts.failure_distribution.length === 0 ? (
              <div className="m-auto text-xs text-muted-foreground/60">No failure categories recorded</div>
            ) : (
              charts.failure_distribution.slice(0, 4).map((f, i) => {
                const totalFails = charts.failure_distribution.reduce((acc, c) => acc + c.count, 0) || 1;
                const pct = Math.round((f.count / totalFails) * 100);

                return (
                  <div key={i} className="flex flex-col gap-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-foreground/90 capitalize">{f.type.replace('_', ' ')}</span>
                      <span className="font-mono text-muted-foreground">{f.count} ({pct}%)</span>
                    </div>
                    <div className="h-1.5 w-full bg-muted/40 rounded-full overflow-hidden">
                      <div className="h-full bg-rose-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Tabs & Table */}
      <div className="mt-8 flex flex-col gap-4">
        <div className="flex items-center gap-2 border-b border-border/30 pb-2">
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'history'
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {labels.callHistory} ({records.length})
          </button>
          <button
            onClick={() => setActiveTab('escalations')}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'escalations'
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {labels.escalations} ({escalations.length})
          </button>
        </div>

        <div className="rounded-2xl mb-glass border border-border/40 overflow-hidden">
          {activeTab === 'history' ? (
            records.length === 0 ? (
              <div className="py-16 text-center text-xs text-muted-foreground">{labels.emptyHistory}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-border/30 bg-muted/20 text-muted-foreground uppercase text-[10px] tracking-wider">
                      <th className="py-3 px-4">Call ID</th>
                      <th className="py-3 px-4">Time</th>
                      <th className="py-3 px-4">Channel</th>
                      <th className="py-3 px-4">Language</th>
                      <th className="py-3 px-4">Duration</th>
                      <th className="py-3 px-4">Latency</th>
                      <th className="py-3 px-4">Outcome</th>
                      <th className="py-3 px-4">Financial Result / Failure Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/20">
                    {records.map((r) => {
                      const isSuccess = r.outcome === 'successful';
                      const dt = r.start_time ? new Date(r.start_time).toLocaleTimeString() : '-';

                      return (
                        <tr key={r.call_id} className="hover:bg-muted/10 transition-colors">
                          <td className="py-3 px-4 font-mono text-primary text-[11px]">{r.call_id}</td>
                          <td className="py-3 px-4 text-muted-foreground">{dt}</td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-400 font-medium text-[10px] uppercase">
                              {r.channel || 'browser'}
                            </span>
                          </td>
                          <td className="py-3 px-4">{r.language || 'English'}</td>
                          <td className="py-3 px-4 text-muted-foreground">{r.duration_seconds ? `${r.duration_seconds}s` : '-'}</td>
                          <td className="py-3 px-4 text-muted-foreground">{r.avg_latency_ms ? `${Math.round(r.avg_latency_ms)}ms` : '-'}</td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-1.5">
                              {isSuccess ? (
                                <span className="px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 font-semibold text-[10px] uppercase">
                                  Successful
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-400 font-semibold text-[10px] uppercase">
                                  Failed
                                </span>
                              )}
                              {r.escalation_created === 1 && (
                                <span className="px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-400 font-semibold text-[10px] uppercase">
                                  Escalated
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-muted-foreground/90">
                            {isSuccess
                              ? r.financial_outcome || r.success_reason || 'Task completed'
                              : r.failure_type
                              ? `Reason: ${r.failure_type}`
                              : 'Incomplete'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )
          ) : (
            escalations.length === 0 ? (
              <div className="py-16 text-center text-xs text-muted-foreground">{labels.emptyEscalations}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-border/30 bg-muted/20 text-muted-foreground uppercase text-[10px] tracking-wider">
                      <th className="py-3 px-4">Ref ID</th>
                      <th className="py-3 px-4">Time</th>
                      <th className="py-3 px-4">Caller</th>
                      <th className="py-3 px-4">Reason</th>
                      <th className="py-3 px-4">Summary</th>
                      <th className="py-3 px-4">Urgency</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/20">
                    {escalations.map((e) => (
                      <tr key={e.reference_id} className="hover:bg-muted/10 transition-colors">
                        <td className="py-3 px-4 font-mono text-primary text-[11px]">{e.reference_id}</td>
                        <td className="py-3 px-4 text-muted-foreground">{e.created_at ? new Date(e.created_at).toLocaleString() : '-'}</td>
                        <td className="py-3 px-4 font-medium">{e.caller_name || '-'}</td>
                        <td className="py-3 px-4 text-muted-foreground">{e.reason || '-'}</td>
                        <td className="py-3 px-4 text-muted-foreground max-w-xs truncate">{e.summary || '-'}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-md bg-amber-500/15 text-amber-400 font-semibold text-[10px] uppercase">
                            {e.urgency || 'normal'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 font-semibold text-[10px] uppercase">
                            {e.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          )}
        </div>
      </div>

      {/* Footer status */}
      <footer className="mt-8 flex justify-between items-center text-[11px] text-muted-foreground/60">
        <span className="flex items-center gap-1.5">
          <RefreshCw className="h-3 w-3 animate-spin text-primary" />
          <span>Auto-refresh active (15s polling)</span>
        </span>
        <span>{lastRefreshed ? `Last updated: ${lastRefreshed}` : ''}</span>
      </footer>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <LanguageProvider>
      <AnalyticsDashboardContent />
    </LanguageProvider>
  );
}
