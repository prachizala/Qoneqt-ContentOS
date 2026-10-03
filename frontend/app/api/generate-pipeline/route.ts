import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const userId = body.user_id || 'usr_local_creator_123';

    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

    const backendRes = await fetch(`${backendUrl}/api/generate-pipeline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': userId,
      },
      body: JSON.stringify({
        ...body,
        user_id: userId
      })
    });

    const data = await backendRes.json();

    if (!backendRes.ok) {
      return NextResponse.json(data, { status: backendRes.status });
    }

    return NextResponse.json(data, { status: 201 });
  } catch (error: any) {
    return NextResponse.json(
      {
        error: 'INTERNAL_ERROR',
        message: error.message || 'An error occurred during video pipeline generation.'
      },
      { status: 500 }
    );
  }
}
