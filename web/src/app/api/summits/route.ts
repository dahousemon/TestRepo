import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';
import { addSummit, removeSummit, getUserSummits, hasSummited } from '@/lib/users';

export async function GET() {
  const session = await auth();

  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const summits = getUserSummits(session.user.id);
  return NextResponse.json({ summits });
}

export async function POST(request: NextRequest) {
  const session = await auth();

  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const { peakId, summitDate, notes } = body;

    if (!peakId) {
      return NextResponse.json({ error: 'Peak ID is required' }, { status: 400 });
    }

    if (hasSummited(session.user.id, peakId)) {
      return NextResponse.json({ error: 'Peak already summited' }, { status: 400 });
    }

    const summit = addSummit(session.user.id, peakId, summitDate, notes);
    return NextResponse.json({ summit });
  } catch (error) {
    console.error('Summit error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to add summit' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  const session = await auth();

  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await request.json();
    const { peakId } = body;

    if (!peakId) {
      return NextResponse.json({ error: 'Peak ID is required' }, { status: 400 });
    }

    const removed = removeSummit(session.user.id, peakId);

    if (!removed) {
      return NextResponse.json({ error: 'Summit not found' }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Summit delete error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to remove summit' },
      { status: 500 }
    );
  }
}
