"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import Agenda from "../Agenda";
import api from "../services/api";

type UserProfile = {
  id: string;
  nome: string;
  tipo: string;
  turma: string;
  pai: string;
};

export default function HomePage() {
  const router = useRouter();
  const [status, setStatus] = useState<"checking" | "authenticated" | "error">(
    "checking",
  );
  const [user, setUser] = useState<UserProfile | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const checkSession = useCallback(async () => {
    try {
      const response = await api.get<UserProfile>("/users/me");
      setUser(response.data);
      setStatus("authenticated");
    } catch (error: unknown) {
      if (isAxiosError(error) && error.response?.status === 401) {
        router.replace("/login");
        return;
      }
      setErrorMessage(
        "Não foi possível verificar sua sessão. Confira a conexão com a API e tente novamente.",
      );
      setStatus("error");
    }
  }, [router]);

  const logout = useCallback(async () => {
    try {
      await api.post("/users/logout");
      router.replace("/login");
    } catch (error: unknown) {
      const detail = isAxiosError<{ detail?: unknown }>(error)
        ? error.response?.data?.detail
        : undefined;
      setErrorMessage(
        typeof detail === "string"
          ? detail
          : "Não foi possível encerrar sua sessão. Tente novamente.",
      );
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
          {errorMessage}
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

  if (!user) return null;

  return <Agenda user={user} onLogout={logout} />;
}
