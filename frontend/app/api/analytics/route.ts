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
    const outcome = searchParams.get('outcome') || undefined;

    const data = await runDbQuery('list', {
      date_from,
      date_to,
      language,
      channel,
      outcome,
    });

    return NextResponse.json(data, {
      headers: { 'Cache-Control': 'no-store, max-age=0' },
    });
  } catch (error) {
    console.error('Error in /api/analytics:', error);
    return NextResponse.json([], { status: 500 });
  }
}
