"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import { BookOpen, Eye, EyeOff, LockKeyhole } from "lucide-react";
import "./login.css";
import api from '../services/api';

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");

  // Permitem ler os valores atuais dos campos sem manter cada tecla em estado React.
  const inputlogin = useRef<HTMLInputElement>(null);
  const inputPassword = useRef<HTMLInputElement>(null);

  // Envia as credenciais para a rota de login do FastAPI.
  function login(identifier: string, password: string) {
    return api.post("/users/login", {
      id: identifier,
      password: password,
    });
  }

  // Valida os campos, chama a API e traduz o resultado em uma mensagem para a tela.
  async function handleSubmit() {
    const loginInput = inputlogin.current;
    const passwordInput = inputPassword.current;

    // Se os elementos ainda não estiverem montados, não há dados para enviar.
    if (!loginInput || !passwordInput) return;

    // Apresenta a validação nativa dos inputs obrigatórios antes da requisição.
    if (!loginInput.reportValidity() || !passwordInput.reportValidity()) return;

    try {
      await login(loginInput.value, passwordInput.value);
      await api.get<{ id: string }>("/users/me");
      router.replace("/home");
    } catch (error: unknown) {
      // A API pode devolver um detalhe legível, como credenciais inválidas.
      if (isAxiosError<{ detail?: unknown }>(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string") {
          setMessage(detail);
        // Uma resposta HTTP indica que a API respondeu, mas rejeitou a operação.
        } else if (error.response) {
          setMessage("Não foi possível entrar. Verifique os dados e tente novamente.");
        // Sem resposta HTTP, provavelmente a API está indisponível ou inacessível.
        } else {
          setMessage("Não foi possível conectar à API. Tente novamente.");
        }
        return;
      }

      setMessage("Ocorreu um erro inesperado ao tentar entrar.");
    }
  }

  return (
    <main className="login-page">
      <section className="login-layout" aria-labelledby="login-heading">
        <div className="login-intro">
          <Link className="login-brand" href="/" aria-label="Entrelaços, início">
            <span className="login-brand-mark" aria-hidden="true">
              <BookOpen size={27} strokeWidth={1.8} />
              <i />
            </span>
            <span>
              entrelaços
              <small>AGENDA ESCOLAR</small>
            </span>
          </Link>

          <div className="login-welcome">
            <span className="login-eyebrow">ESCOLA HORIZONTE · 3º ANO A</span>
            <h1>Uma escola mais perto, todos os dias.</h1>
            <p>
              Comunicados, atividades e momentos importantes da turma em um só
              lugar.
            </p>
          </div>

          <div className="login-note">
            <span className="login-note-icon" aria-hidden="true">
              <LockKeyhole size={17} />
            </span>
            <p>
              Acesso destinado à comunidade escolar.
              <br />
              As contas são disponibilizadas pela gestão.
            </p>
          </div>
        </div>

        <div className="login-card">
          <div className="login-card-heading">
            <span className="login-eyebrow">BEM-VINDO(A) DE VOLTA</span>
            <h2 id="login-heading">Acesse sua conta</h2>
            <p>Entre com seus dados para acompanhar a agenda escolar.</p>
          </div>

          <form
            className="login-form"
            onSubmit={(event) => event.preventDefault()}
          >
            <div className="login-field">
              <label htmlFor="login-identifier">E-mail ou identificação</label>
              <input
                id="login-identifier"
                name="identifier"
                type="text"
                ref={inputlogin}
                autoComplete="username"
                placeholder="Digite seu e-mail ou identificação"
                required
              />
            </div>

            <div className="login-field">
              <label htmlFor="login-password">Senha</label>
              <div className="login-password-wrap">
                <input
                  id="login-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Digite sua senha"
                  ref={inputPassword}
                  required
                />
                <button
                  className="login-password-toggle"
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  aria-pressed={showPassword}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <p className="login-help">
              Precisa de acesso? Entre em contato com a gestão da escola.
            </p>

            <button
              className="login-submit"
              type="button"
              onClick={handleSubmit}
            >
              Entrar
              <span aria-hidden="true">→</span>
            </button>

            <p className="login-feedback" role="status" aria-live="polite">
              {message}
            </p>
          </form>

          <p className="login-card-footer">
            <span aria-hidden="true" />
            Um espaço de cuidado, diálogo e parceria.
          </p>
        </div>
      </section>
      <footer className="login-footer">
        <span>entrelaços · Agenda escolar</span>
        <span>Uma parceria entre escola e família</span>
      </footer>
    </main>
  );
}
