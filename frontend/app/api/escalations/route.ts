import { NextResponse } from 'next/server';
import { runDbQuery } from '@/lib/db-bridge';

export const revalidate = 0;

export async function GET() {
  try {
    const data = await runDbQuery('escalations');
    return NextResponse.json(data, {
      headers: { 'Cache-Control': 'no-store, max-age=0' },
    });
  } catch (error) {
    console.error('Error in /api/escalations:', error);
    return NextResponse.json([], { status: 500 });
  }
}
