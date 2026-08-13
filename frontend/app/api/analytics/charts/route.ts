import { NextResponse } from 'next/server';
import { runDbQuery } from '@/lib/db-bridge';

export const revalidate = 0;

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const date_from = searchParams.get('date_from') || undefined;
    const date_to = searchParams.get('date_to') || undefined;
    const language = searchParams.get('language') || undefined;
    const channel = searchParams.get('channel') || undefined;

    const data = await runDbQuery('charts', {
      date_from,
      date_to,
      language,
      channel,
    });

    return NextResponse.json(data, {
      headers: { 'Cache-Control': 'no-store, max-age=0' },
    });
  } catch (error) {
    console.error('Error in /api/analytics/charts:', error);
    return NextResponse.json(
      { calls_over_time: [], failure_distribution: [], language_distribution: [], financial_outcomes: [], latency_trend: [] },
      { status: 500 }
    );
  }
}
