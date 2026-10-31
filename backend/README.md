# agenda-escolar-online
Projeto Integrador 2 da UNIVESP: desenvolvimento de uma agenda escolar online para facilitar a comunicação entre escola, professores e responsáveis, digitalizando o tradicional caderno de recados e centralizando avisos e informações da rotina escolar.

## CORS

Em desenvolvimento, a API permite chamadas dos front-ends locais em `localhost` e `127.0.0.1`, nas portas `3000` e `5173`. O domínio de produção atual `https://agenda-escolar-online-sz6h.vercel.app` também está permitido por padrão.

Em produção, configure a variável de ambiente `CORS_ORIGINS` no serviço que hospeda a API com a origem exata do front-end. Para mais de uma origem, separe os endereços por vírgula, sem barra no final:

```text
CORS_ORIGINS=https://seu-projeto.vercel.app,https://www.seu-dominio.com
```

Não use `*` para liberar qualquer origem. Depois de alterar a variável no serviço de hospedagem, reinicie ou publique novamente a API.

O front-end chama a API diretamente pelo navegador, usando a URL definida em `frontend/app/services/api.js`. Para testes com o front-end na Vercel e o backend local, o navegador precisa conseguir acessar `http://127.0.0.1:8080`; em produção, esse endereço deve ser substituído pela URL HTTPS pública do backend.

## Sessões de login

`POST /users/login` valida o identificador e a senha temporária (data de nascimento no formato `DDMMYYYY`), cria um token aleatório e grava na tabela `sessions` somente o hash SHA-256 do token junto com `id_usuarios` e `created_at`. O token original é entregue ao navegador em um cookie `HttpOnly`, não no JSON da resposta.

`GET /users/me` lê o cookie, valida a sessão no Supabase e retorna `id`, `nome`, `tipo`, `turma` e `pai`. Para aluno, `nome` vem de `usuarios`, e `turma` vem do relacionamento em `usuarios_dados_alunos` com `turmas`. `pai` fica vazio enquanto não houver um campo ou relacionamento de responsável disponível no banco. Sessões duram 12 horas por padrão; `SESSION_TTL_SECONDS` altera esse prazo. Sessões expiradas ou desconhecidas recebem `401`.

`POST /users/logout` remove do Supabase o hash da sessão apresentada no cookie e expira o cookie no navegador. A rota retorna sucesso mesmo que o navegador não envie um cookie.

O cookie é `HttpOnly`; o navegador o armazena e o envia nas chamadas seguintes. Como o front-end e a API podem estar em sites diferentes, o backend deve usar `SESSION_COOKIE_SAMESITE=none` e `SESSION_COOKIE_SECURE=true` para esse cenário. Em produção, a API deve usar HTTPS; para desenvolvimento, o loopback local (`localhost`/`127.0.0.1`) pode ser usado. Navegadores podem bloquear cookies de terceiros conforme as configurações de privacidade.

A tela `/home` consulta `/users/me` ao abrir, mostra o perfil retornado e redireciona para `/login` quando a API responde `401`. A senha baseada na data de nascimento é temporária e fraca para uso real.
