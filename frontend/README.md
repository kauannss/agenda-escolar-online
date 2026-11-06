# Entrelaços — Agenda escolar

Projeto Integrador 2 da UNIVESP: desenvolvimento de uma agenda escolar online para facilitar a comunicação entre escola, professores e responsáveis, digitalizando o tradicional caderno de recados e centralizando avisos e informações da rotina escolar.

## O que está funcionando

- Consulta de comunicados e confirmação de leitura.
- Calendário com reuniões, eventos e feriados.
- Controle das atividades concluídas.
- Perfis de responsável, professor e gestão para testar a demonstração.
- Publicação de recados durante a sessão.

Os dados são fictícios. As alterações ficam apenas na sessão e são perdidas ao recarregar a página. A integração com banco de dados está prevista para uma próxima etapa.

## Login e conexão com a API

As chamadas do front-end à API passam por `/api/backend/*`, uma rota proxy do Next. O servidor Next encaminha essas chamadas ao FastAPI e repassa o cookie `agenda_session`. Assim, o navegador conversa apenas com o domínio do site e não depende de cookies de terceiros entre a Vercel e o Render.

Para testar localmente, inicie o FastAPI na porta `8080` e rode `npm run dev:next` no diretório `frontend`; abra `http://localhost:3000`. O proxy usa `http://127.0.0.1:8080` automaticamente no modo de desenvolvimento. Não use `npm run dev` para esse teste: esse comando mantém o fluxo Vinext/Cloudflare na porta `5173`, que não executa estas rotas do Next.

Na Vercel, configure a variável de ambiente `API_URL` com a URL base pública do FastAPI, sem barra final, por exemplo `https://agenda-escolar-online.onrender.com`. Selecione os ambientes em que o front será publicado e faça um novo deploy. Essa variável é usada somente no servidor Next; não use `NEXT_PUBLIC_API_URL` nem coloque chaves do Supabase no front-end.

## Como executar

É necessário ter Node.js 22.13.0 ou superior.

```sh
npm run install:ci
npm run dev
```

Abra o endereço informado no terminal. Por padrão, o servidor local usa a porta 5173.

## Conferir a versão final

```sh
npm run build
npm run start
```

O segundo comando abre uma prévia local da versão compilada. Ele não publica o projeto.

## Organização

- `app/Agenda.tsx`: telas, dados de demonstração e interações.
- `app/agenda.css`: estilos e ajustes para celular.
- `app/layout.tsx`: idioma e informações da página.
- `components/ui/`: componentes de interface.
- `public/`: arquivos disponíveis no site.
- `db/`: estrutura reservada para a futura integração com banco de dados.

A interface usa React e TypeScript. A aplicação roda com Vinext. As dependências e suas versões ficam registradas no arquivo de lock.
