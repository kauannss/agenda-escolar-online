# agenda-escolar-online
Projeto Integrador 2 da UNIVESP: desenvolvimento de uma agenda escolar online para facilitar a comunicação entre escola, professores e responsáveis, digitalizando o tradicional caderno de recados e centralizando avisos e informações da rotina escolar.

## CORS

Em desenvolvimento, a API permite chamadas dos front-ends locais em `localhost` e `127.0.0.1`, nas portas `3000` e `5173`. O domínio de produção atual `https://agenda-escolar-online-sz6h.vercel.app` também está permitido por padrão.

Em produção, configure a variável de ambiente `CORS_ORIGINS` no serviço que hospeda a API com a origem exata do front-end. Para mais de uma origem, separe os endereços por vírgula, sem barra no final:

```text
CORS_ORIGINS=https://seu-projeto.vercel.app,https://www.seu-dominio.com
```

Não use `*` para liberar qualquer origem. Depois de alterar a variável no serviço de hospedagem, reinicie ou publique novamente a API.

A API permite os métodos `GET`, `POST`, `PUT`, `DELETE` e `OPTIONS`. O front-end publicado na Vercel encaminha as chamadas pelo proxy do Next, então a comunicação entre navegador e front-end é same-origin e não depende de CORS do browser. `CORS_ORIGINS` continua necessário para clientes que chamem a API diretamente.

No projeto Vercel, configure `API_URL` com a URL HTTPS pública do backend (por exemplo, `https://agenda-escolar-online.onrender.com`) e publique novamente. A variável é lida pelo servidor Next e não deve ter o prefixo `NEXT_PUBLIC_`.

## Sessões de login

`POST /users/login` valida o identificador e a senha temporária (data de nascimento no formato `DDMMYYYY`), cria um token aleatório e grava na tabela `sessions` somente o hash SHA-256 do token junto com `id_usuarios` e `created_at`. O token original é entregue ao navegador em um cookie `HttpOnly`, não no JSON da resposta.

`GET /users/me` lê o cookie, valida a sessão no Supabase e retorna `id`, `nome`, `tipo`, `turma` e `pai`. Para aluno, nome e turma vêm de `usuarios` e de seus relacionamentos; `pai` contém `usuarios_dados_alunos.nome_responsavel`. Se esse campo estiver vazio, a interface solicita o nome do responsável. `PUT /users/me/responsavel` permite que o próprio aluno autenticado salve esse nome. Sessões duram 12 horas por padrão; `SESSION_TTL_SECONDS` altera esse prazo. Sessões expiradas ou desconhecidas recebem `401`.

`POST /users/logout` remove do Supabase o hash da sessão apresentada no cookie e expira o cookie no navegador. A rota retorna sucesso mesmo que o navegador não envie um cookie.

O cookie é `HttpOnly`; o navegador o armazena no domínio da Vercel e o envia nas chamadas ao proxy do Next, que o encaminha ao backend. Em produção, a API deve usar HTTPS e `SESSION_COOKIE_SECURE=true`. O proxy usa `API_URL`; em desenvolvimento, usa `http://127.0.0.1:8080` por padrão.

A tela `/home` consulta `/users/me` ao abrir, mostra o perfil retornado e redireciona para `/login` quando a API responde `401`. A senha baseada na data de nascimento é temporária e fraca para uso real.

## Cadastro de usuários

`GET /users/` lista identificador, nome, tipo e turmas dos usuários e exige sessão de gestão. Não retorna data de nascimento. `POST /users/register` também exige sessão de gestão. O corpo recebe `id`, `type` (`aluno`, `professor` ou `gestor`), `name`, `date_of_birth` no formato `YYYY-MM-DD` e `id_turma` para aluno/professor. Para cadastrar um gestor, não envie `id_turma`. `GET /users/classes` lista turmas apenas para gestão. O usuário é criado em `usuarios`; alunos também recebem vínculo em `usuarios_dados_alunos`, professores em `turmas_professores`, e gestores não recebem vínculo de turma. Se o identificador já existir com dados diferentes, a API retorna `409`. Se uma tentativa anterior deixou um aluno ou professor sem vínculo, repetir exatamente os mesmos dados completa esse vínculo; falhas novas na criação do vínculo levam o backend a tentar remover o registro principal.

Se o vínculo falhar, a resposta inclui o SQLSTATE do Supabase e os logs do backend registram a mensagem e a dica retornadas pelo banco, sem registrar o identificador do usuário. Use esses dados para diagnosticar falhas de chave estrangeira, permissões ou outras restrições.

`GET /users/{id}` retorna os dados de um usuário para edição, incluindo a data de nascimento e os IDs das turmas; `PUT /users/{id}` atualiza nome, tipo, nascimento e vínculos sem permitir mudar o identificador. Aluno deve ter exatamente uma turma, professor ao menos uma e gestor nenhuma. `DELETE /users/{id}` remove permanentemente o usuário, seus vínculos de turma e sessões. Somente a gestão pode executar essas operações; não é permitido remover a própria conta nem excluir/rebaixar o último gestor.

## Turmas

`GET /turmas` lista o identificador, nome e turno das turmas; `POST /turmas` cadastra uma turma com `nome` e `turno`; `PUT /turmas/{id}` altera nome e turno; `DELETE /turmas/{id}` remove uma turma sem vínculos. Todas as rotas exigem sessão de gestão. A exclusão responde `409` quando houver alunos, professores, comunicados, eventos ou atividades vinculados à turma. A interface de gestão exibe a lista e permite cadastrar, editar e excluir turmas na aba **Turmas**.

## Comunicados

`GET /comunicados` lista os comunicados das turmas associadas ao usuário autenticado. `GET /comunicados/turmas` lista as turmas que um professor ou usuário de gestão pode selecionar. `POST /comunicados` recebe:

```json
{
  "title": "Reunião de famílias",
  "description": "A reunião será na próxima quinta-feira.",
  "id_turmas": ["id-da-turma-a", "id-da-turma-b"]
}
```

O registro é gravado uma única vez em `comunicated` com `title` e `description`; o banco gera `id` e `created_at`. O vínculo com várias turmas usa `comunicated_turmas`, com `id_comunicado` e `id_turma` como chaves estrangeiras. Alunos consultam somente as turmas em que estão matriculados; professores só podem publicar nas turmas atribuídas a eles; gestão pode selecionar todas as turmas.

`PUT /comunicados/{id}` atualiza título, mensagem e turmas destinatárias; `DELETE /comunicados/{id}` exclui o comunicado e seus vínculos. As duas operações são exclusivas da gestão. A interface disponibiliza essas ações na aba **Comunicados** para gestores.

O estado de leitura ainda não é persistido: a tabela descrita não tem dados de confirmação. RLS e permissões das tabelas devem ser configuradas para permitir as operações necessárias pelo backend sem conceder escrita pública.

## Eventos do calendário

`GET /eventos` lista os eventos associados às turmas do usuário autenticado. `GET /eventos/turmas` lista as turmas que professores e usuários de gestão podem selecionar. `POST /eventos` é permitido somente a professores e à gestão e recebe:

```json
{
  "nome": "Reunião de famílias",
  "data": "2026-10-15",
  "id_turmas": ["id-da-turma-a", "id-da-turma-b"]
}
```

O evento é criado uma vez em `eventos` com `nome` e `data`; o banco gera o identificador. Para cada turma selecionada, o backend cria um vínculo em `eventos_turmas` usando `id_eventos` e `id_turmas`. Alunos consultam somente eventos de suas turmas, professores somente eventos de turmas atribuídas a eles e a gestão pode consultar e criar eventos para todas as turmas. O backend também valida os vínculos enviados antes de gravar. `DELETE /eventos/{id}` é exclusivo da gestão e remove o evento e todos os vínculos com turmas.

## Atividades

As rotas `/atividades` consultam, criam, editam e removem atividades usando as tabelas `atividades` e `atividades_turmas`. Cada atividade armazena `nome`, `descricao`, `materia`, `data_limite` e `professor_id`; os vínculos de turma usam `atividade_id` e `turma_id`. O professor conectado é identificado pela sessão e usado automaticamente como responsável. A gestão também pode cadastrar/editar atividades, mas deve selecionar um professor responsável.

Alunos veem somente atividades vinculadas às suas turmas. Professores veem e podem alterar/remover atividades cujo `professor_id` corresponde ao ID da sessão; essa atribuição explícita permite que vejam atividades atribuídas pela gestão mesmo quando a turma ainda não está no vínculo professor-turma. Ao criar atividades, professores só podem escolher suas turmas; ao editar, podem manter os vínculos atuais ou adicionar turmas próprias. A gestão pode consultar e gerenciar todas as atividades. A marcação de conclusão na interface do aluno é apenas local; a tabela informada não possui coluna para persistir esse status.
