# Entrelaços — Agenda escolar

Projeto Integrador 2 da UNIVESP: desenvolvimento de uma agenda escolar online para facilitar a comunicação entre escola, professores e responsáveis, digitalizando o tradicional caderno de recados e centralizando avisos e informações da rotina escolar.

## O que está funcionando

- Consulta de comunicados e confirmação de leitura.
- Calendário com reuniões, eventos e feriados.
- Controle das atividades concluídas.
- Perfis de responsável, professor e gestão para testar a demonstração.
- Publicação de recados durante a sessão.

Os dados são fictícios. As alterações ficam apenas na sessão e são perdidas ao recarregar a página. A integração com banco de dados está prevista para uma próxima etapa.

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
