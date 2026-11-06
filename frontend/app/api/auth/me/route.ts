import { forwardBackendRequest } from "@/lib/auth-backend-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  return forwardBackendRequest(request, "/users/me");
}
