import { forwardAuthRequest } from "@/lib/auth-backend-proxy";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return forwardAuthRequest(request, "/users/login");
}
