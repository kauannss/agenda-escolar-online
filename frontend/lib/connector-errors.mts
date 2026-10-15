import { z } from "zod/v4";

/** Valida os resultados antes de devolver a resposta pública. */
export function connectorResponse(result: unknown): Response {
  try {
    // Carrega a leitura dos dados apenas no servidor para não incluí-la na interface.
    const requestId = z
      .string()
      .regex(/^[A-Za-z0-9._:-]{1,128}$/)
      .optional()
      .catch(undefined);
    const envelope = {
      error: z.never().optional(),
      content: z.never().optional(),
      structuredContent: z.never().optional(),
      isError: z.never().optional(),
      requestId,
    };
    const content = z.object({
      content: z.array(z.object({ type: z.string() }).catchall(z.json())),
      structuredContent: z.json().optional(),
      isError: z.never().optional(),
      error: z.never().optional(),
    });
    const failure = z.object({
      ...envelope,
      status: z
        .string()
        .min(1)
        .refine((value) => value !== "success"),
      message: z.string().min(1),
      retryAfterMs: z.number().int().nonnegative().safe().optional(),
      result: content.optional(),
    });
    const success = z.object({
      ...envelope,
      status: z.literal("success"),
      result: content,
      message: z.never().optional(),
      retryAfterMs: z.never().optional(),
    });
    const schema =
      result !== null &&
      typeof result === "object" &&
      "status" in result &&
      result.status === "success"
        ? success
        : failure;
    const parsed = schema.safeParse(result);
    if (parsed.success) {
      // O estado informado no JSON determina o resultado.
      return Response.json(parsed.data, {
        headers: { "Cache-Control": "private, no-store" },
      });
    }
  } catch {
    // Valores cíclicos ou que não podem ser serializados também ficam sem confirmação.
  }
  return Response.json(
    {
      status: "upstream_error",
      message:
        "The app did not return a confirmed result. The action may have completed; check before trying again.",
    },
    { status: 502, headers: { "Cache-Control": "private, no-store" } },
  );
}

/** Somente apresentação. O endereço de autenticação é fornecido pelo servidor. */
export function connectorErrorRecovery(
  error: { status: string; message: string },
  connectorName: string,
  reconnectHref: string,
): { message: string; action?: { label: string; href: string } } {
  if (error.status === "reauthentication_required") {
    return {
      message: error.message,
      action: { label: `Connect ${connectorName}`, href: reconnectHref },
    };
  }
  // Outros resultados não confirmam a falta de permissão nem permitem repetir a chamada com segurança.
  return { message: error.message };
}
