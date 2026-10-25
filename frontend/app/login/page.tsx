import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <section className="w-full max-w-md space-y-4 rounded-lg border bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Entrelaços · Agenda Escolar
        </p>
        <h1 className="text-2xl font-semibold">Acesso à agenda</h1>
        <p className="text-sm leading-6 text-muted-foreground">
          A tela de login e a autenticação serão implementadas em uma próxima
          etapa. Por enquanto, esta página apenas marca a rota de entrada.
        </p>
        <Link
          className="inline-flex min-h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          href="/home"
        >
          Abrir demonstração
        </Link>
      </section>
    </main>
  );
}
