const LOCAL_API_URL = "http://127.0.0.1:8080";

export async function forwardAuthRequest(
  request: Request,
  backendPath: "/users/login" | "/users/me",
): Promise<Response> {
  const configuredApiUrl = process.env.API_URL;
  const apiUrl =
    configuredApiUrl ||
    (process.env.NODE_ENV === "development" ? LOCAL_API_URL : null);

  if (!apiUrl) {
    console.error("API_URL is not configured for the authentication proxy.");
    return Response.json(
      { detail: "A URL da API não está configurada no servidor web." },
      { status: 500 },
    );
  }

  let targetUrl: URL;
  try {
    targetUrl = new URL(backendPath, `${apiUrl.replace(/\/+$/, "")}/`);
  } catch {
    console.error("API_URL is not a valid URL.");
    return Response.json(
      { detail: "A URL da API está configurada incorretamente." },
      { status: 500 },
    );
  }

  if (process.env.NODE_ENV === "production" && targetUrl.protocol !== "https:") {
    console.error("API_URL must use HTTPS in production.");
    return Response.json(
      { detail: "A URL da API deve usar HTTPS em produção." },
      { status: 500 },
    );
  }

  const requestHeaders = new Headers();
  for (const headerName of ["accept", "content-type"]) {
    const headerValue = request.headers.get(headerName);
    if (headerValue) requestHeaders.set(headerName, headerValue);
  }
  const sessionCookie = request.headers
    .get("cookie")
    ?.split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith("agenda_session="));
  if (sessionCookie) requestHeaders.set("cookie", sessionCookie);

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(targetUrl, {
      method: request.method,
      headers: requestHeaders,
      ...(hasBody ? { body: await request.arrayBuffer() } : {}),
      cache: "no-store",
      redirect: "manual",
    });
  } catch (error: unknown) {
    console.error(
      "The authentication proxy could not reach the FastAPI service.",
      error,
    );
    return Response.json(
      { detail: "Não foi possível conectar ao serviço de autenticação." },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers();
  const contentType = upstreamResponse.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  responseHeaders.set("cache-control", "no-store");

  for (const cookie of upstreamResponse.headers.getSetCookie()) {
    responseHeaders.append("set-cookie", cookie);
  }

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: responseHeaders,
  });
}
