import { forwardBackendRequest } from "@/lib/auth-backend-proxy";

export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function forward(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return forwardBackendRequest(request, path.join("/"));
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const DELETE = forward;
