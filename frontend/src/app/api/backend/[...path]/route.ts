import { NextRequest, NextResponse } from "next/server";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

export const dynamic = "force-dynamic";

function getBackendBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.BACKEND_URL ??
    DEFAULT_BACKEND_URL
  ).replace(/\/$/, "");
}

function buildBackendUrl(path: string[], search: string): string {
  return `${getBackendBaseUrl()}/api/v1/${path.join("/")}${search}`;
}

function buildHeaders(request: NextRequest, hasBody: boolean): Headers {
  const headers = new Headers();

  if (request.headers.get("accept")) {
    headers.set("accept", request.headers.get("accept")!);
  }

  if (hasBody && request.headers.get("content-type")) {
    headers.set("content-type", request.headers.get("content-type")!);
  }

  if (request.headers.get("cookie")) {
    headers.set("cookie", request.headers.get("cookie")!);
  }

  return headers;
}

async function proxyRequest(
  request: NextRequest,
  context: { params: { path: string[] } },
): Promise<NextResponse> {
  const path = context.params.path ?? [];
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;
  const backendResponse = await fetch(
    buildBackendUrl(path, request.nextUrl.search),
    {
      method: request.method,
      headers: buildHeaders(request, hasBody),
      body,
      cache: "no-store",
    },
  );
  const responseBody = await backendResponse.text();
  const contentType =
    backendResponse.headers.get("content-type") ?? "application/json; charset=utf-8";
  const setCookie = backendResponse.headers.get("set-cookie");
  const responseHeaders = new Headers({ "content-type": contentType });

  if (setCookie) {
    responseHeaders.set("set-cookie", setCookie);
  }

  return new NextResponse(responseBody, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export async function GET(
  request: NextRequest,
  context: { params: { path: string[] } },
): Promise<NextResponse> {
  return proxyRequest(request, context);
}

export async function POST(
  request: NextRequest,
  context: { params: { path: string[] } },
): Promise<NextResponse> {
  return proxyRequest(request, context);
}

export async function PATCH(
  request: NextRequest,
  context: { params: { path: string[] } },
): Promise<NextResponse> {
  return proxyRequest(request, context);
}
