import { forwardAuthRequest } from "@/lib/auth-backend-proxy";

export const runtime = "nodejs";

export async function GET(request: Request) {
  return forwardAuthRequest(request, "/users/me");
}
