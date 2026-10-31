"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import Agenda from "../Agenda";
import api from "../services/api";

export default function HomePage() {
  const router = useRouter();
  const [status, setStatus] = useState<"checking" | "authenticated" | "error">(
    "checking",
  );

  const checkSession = useCallback(async () => {
    try {
      await api.get("/me");
      setStatus("authenticated");
    } catch (error: unknown) {
      if (isAxiosError(error) && error.response?.status === 401) {
        router.replace("/login");
        return;
      }
      setStatus("error");
    }
  }, [router]);

  useEffect(() => {
    void Promise.resolve().then(checkSession);
  }, [checkSession]);

  if (status === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f7f7f4] p-6 text-sm text-[#626b64]">
        Verificando sua sessão…
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#f7f7f4] p-6 text-center">
        <p role="alert" className="text-sm text-[#626b64]">
          Não foi possível verificar sua sessão. Confira a conexão com a API e
          tente novamente.
        </p>
        <button
          className="rounded-md bg-[#2d6349] px-4 py-2 text-sm font-medium text-white"
          onClick={() => {
            setStatus("checking");
            void checkSession();
          }}
        >
          Tentar novamente
        </button>
      </main>
    );
  }

  return <Agenda />;
}
