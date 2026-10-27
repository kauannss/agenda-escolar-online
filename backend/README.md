# agenda-escolar-online
Projeto Integrador 2 da UNIVESP: desenvolvimento de uma agenda escolar online para facilitar a comunicação entre escola, professores e responsáveis, digitalizando o tradicional caderno de recados e centralizando avisos e informações da rotina escolar.

## CORS

Em desenvolvimento, a API permite chamadas dos front-ends locais em `localhost` e `127.0.0.1`, nas portas `3000` e `5173`. O domínio de produção atual `https://agenda-escolar-online-sz6h.vercel.app` também está permitido por padrão.

Em produção, configure a variável de ambiente `CORS_ORIGINS` no serviço que hospeda a API com a origem exata do front-end. Para mais de uma origem, separe os endereços por vírgula, sem barra no final:

```text
CORS_ORIGINS=https://seu-projeto.vercel.app,https://www.seu-dominio.com
```

Não use `*` para liberar qualquer origem. Depois de alterar a variável no serviço de hospedagem, reinicie ou publique novamente a API.

No projeto do front-end hospedado na Vercel, configure `NEXT_PUBLIC_API_URL` com a URL pública do serviço FastAPI, por exemplo `https://sua-api.exemplo.com`. Em desenvolvimento local, essa variável pode ficar sem definição e o cliente Axios usa `http://127.0.0.1:8080`.

## Sessões de login

`POST /users/login` valida o identificador e a senha temporária (data de nascimento no formato `DDMMYYYY`), cria um token aleatório e grava na tabela `sessions` somente o hash SHA-256 do token junto com `id_usuarios` e `created_at`. O token original é entregue ao navegador em um cookie `HttpOnly`, não no JSON da resposta.

`GET /users/me` lê o cookie, calcula o hash, procura a sessão no Supabase e retorna o identificador do usuário se a sessão ainda for válida. Sessões duram 12 horas por padrão; `SESSION_TTL_SECONDS` altera esse prazo. Sessões expiradas ou desconhecidas recebem `401`, e o cookie inválido é removido.

Configure `SUPABASE_SECRET_KEY` somente no backend. Ela é necessária porque o backend acessa a tabela `sessions` com uma chave de servidor. Nunca coloque essa chave no front-end ou em uma variável `NEXT_PUBLIC_*`. Ative RLS na tabela `sessions` e não crie políticas para acesso público; o backend usa a chave secreta no servidor.

Para produção com front-end e API em sites diferentes, configure no backend `SESSION_COOKIE_SECURE=true` e `SESSION_COOKIE_SAMESITE=none`, além de `CORS_ORIGINS` com a origem exata do front-end. Em desenvolvimento local, os padrões são `SESSION_COOKIE_SECURE=false` e `SESSION_COOKIE_SAMESITE=lax`. CORS permite credenciais e o cliente Axios deve usar `withCredentials: true`.

O cookie é criado e validado por `/users/me`, mas a proteção das demais rotas, o logout e a renovação da sessão ainda não estão implementados. A senha baseada na data de nascimento é temporária e fraca para uso real.
