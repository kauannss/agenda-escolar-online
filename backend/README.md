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

## Criação de sessão no login

Após validar o identificador e a senha temporária (data de nascimento no formato `DDMMYYYY`), `POST /users/login` cria um token aleatório. O backend grava na tabela `sessions` somente o hash SHA-256 do token, junto com `id_usuarios` e `created_at`, e retorna o token original como `access_token`.

Para permitir esse insert sem usar a chave publicável, configure `SUPABASE_SECRET_KEY` somente no ambiente do backend (localmente no `.env` do backend e, em produção, nas variáveis do serviço que hospeda o FastAPI). Nunca use essa chave no front-end nem em uma variável `NEXT_PUBLIC_*`. A tabela `sessions` deve ter RLS habilitado; o backend usa a chave secreta no servidor para o insert.

Esta etapa apenas cria e retorna a sessão. O cookie seguro, a validação do token em rotas protegidas, a expiração e o logout ainda não estão implementados. Até isso ser feito, o `access_token` não autentica outras requisições. A senha baseada na data de nascimento também é temporária e fraca para uso real.
