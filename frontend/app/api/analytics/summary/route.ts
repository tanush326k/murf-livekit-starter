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

    const data = await runDbQuery('summary', {
      date_from,
      date_to,
      language,
      channel,
    });

    return NextResponse.json(data, {
      headers: { 'Cache-Control': 'no-store, max-age=0' },
    });
  } catch (error) {
    console.error('Error in /api/analytics/summary:', error);
    return NextResponse.json(
      { total_calls: 0, successful_calls: 0, failed_calls: 0, success_rate: 0, avg_latency_ms: null },
      { status: 500 }
    );
  }
}
