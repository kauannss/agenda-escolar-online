import { forwardBackendRequest } from "@/lib/auth-backend-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardBackendRequest(request, "/users/login");
}
