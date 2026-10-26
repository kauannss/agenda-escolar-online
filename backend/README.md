# agenda-escolar-online
Projeto Integrador 2 da UNIVESP: desenvolvimento de uma agenda escolar online para facilitar a comunicação entre escola, professores e responsáveis, digitalizando o tradicional caderno de recados e centralizando avisos e informações da rotina escolar.

## CORS

Em desenvolvimento, a API permite chamadas dos front-ends locais em `localhost` e `127.0.0.1`, nas portas `3000` e `5173`.

Em produção, configure a variável de ambiente `CORS_ORIGINS` no serviço que hospeda a API com a origem exata do front-end. Para mais de uma origem, separe os endereços por vírgula, sem barra no final:

```text
CORS_ORIGINS=https://seu-projeto.vercel.app,https://www.seu-dominio.com
```

Não use `*` para liberar qualquer origem. Depois de alterar a variável no serviço de hospedagem, reinicie ou publique novamente a API.
