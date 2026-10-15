from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

doc=Document()
s=doc.sections[0]
s.top_margin=s.left_margin=Cm(3)
s.bottom_margin=s.right_margin=Cm(2)
normal=doc.styles['Normal']; normal.font.name='Arial'; normal.font.size=Pt(12)
normal.paragraph_format.line_spacing=1.5
normal.paragraph_format.space_after=Pt(6)
for name in ['Heading 1','Heading 2']:
 doc.styles[name].font.name='Arial'; doc.styles[name].font.color.rgb=__import__('docx').shared.RGBColor(0,0,0)
 doc.styles[name].font.size=Pt(12)
authors=['Beatriz Cerqueira Santos, RA: 24215022','Bernardo Goisman, RA: 2224138','Italo Machado de Oliveira, RA: 24208911','Kauan dos Santos Silva, RA: 24200757','Leila Margareti Pessoa Silva, RA: 24201723','Leonardo Davi Silva Klai Vasques, RA: 24214673','Marcelo Trindade Santos, RA: 24200341','Silvia Alcantara Dias de Souza, RA: 2217944']
title='Agenda Escolar Inteligente: aplicação web para a comunicação entre escola e família do 1º ao 5º ano do Ensino Fundamental'
def p(t,center=False):
 a=doc.add_paragraph(t); a.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY; return a
def h(t):doc.add_heading(t,level=1)
p('UNIVERSIDADE VIRTUAL DO ESTADO DE SÃO PAULO',True)
p('')
for a in authors:p(a,True)
p('');p(title,True);p('');p('São Paulo – SP\n2026',True)
doc.add_page_break();p('UNIVERSIDADE VIRTUAL DO ESTADO DE SÃO PAULO',True);p('');p(title,True);p('')
p('Relatório Técnico-Científico apresentado à disciplina de Projeto Integrador II dos cursos de Engenharia de Computação, Bacharelado em Tecnologia da Informação e Bacharelado em Ciência de Dados da Universidade Virtual do Estado de São Paulo (UNIVESP).')
p('Tutora: Roberta Cristina Gobi.\nPolos: Diadema, Jandira e Santo André.');p('');p('São Paulo – SP\n2026',True)
doc.add_page_break();h('RESUMO')
p('Este trabalho apresenta a proposta de uma Agenda Escolar Inteligente destinada à comunicação entre escolas públicas e responsáveis por estudantes do 1º ao 5º ano do Ensino Fundamental. O objetivo é centralizar comunicados, atividades e eventos, com confirmação de leitura e acompanhamento de pendências. A investigação inicial compreendeu revisão bibliográfica, discussões entre integrantes, conversas informais e elaboração de questionários para profissionais da educação e responsáveis. Até a etapa relatada no texto original, os instrumentos não haviam recebido respostas; portanto, as necessidades identificadas permanecem preliminares. A arquitetura proposta utiliza React para a interface e Supabase com PostgreSQL para persistência, autenticação e controle de acesso. A inteligência da agenda corresponde a regras de organização por prazo, prioridade e confirmação de leitura. Os resultados consolidados nesta etapa são a delimitação do escopo, os requisitos preliminares e o planejamento técnico. A demonstração do front-end utiliza dados fictícios e não comprova implantação institucional nem integração com banco de dados. A avaliação com a comunidade e a implementação dos serviços de dados constituem etapas posteriores.')
p('Palavras-chave: Comunicação escolar. Agenda digital. React. Supabase. Banco de dados.')
h('ESTRUTURA DO RELATÓRIO')
for t in ['1 Introdução','2 Desenvolvimento','2.1 Objetivos','2.2 Justificativa e delimitação do problema','2.3 Fundamentação teórica','2.4 Metodologia','2.5 Solução proposta e arquitetura','2.6 Requisitos e critérios de validação','2.7 Resultados preliminares e limitações','3 Considerações finais','Referências','Apêndice A – Roteiro de demonstração']:p(t)
doc.add_page_break();h('1 INTRODUÇÃO')
p('A comunicação entre escola e família contribui para o acompanhamento da rotina dos estudantes. Nos anos iniciais do Ensino Fundamental, os responsáveis precisam consultar orientações, atividades, reuniões e solicitações de materiais. As experiências profissionais e conversas informais relatadas pelo grupo indicam dificuldades na circulação de recados e no acompanhamento de seu recebimento. Essas observações orientam a investigação, mas não representam uma pesquisa concluída com a comunidade.')
p('A proposta parte de práticas já existentes. Neves, Silva e Terra (2018) descrevem o ClassMatch, desenvolvido para organização de compromissos e avaliado por usuários na época do estudo. Larrosa et al. (2019) apresentam uma experiência de substituição da agenda física por aplicativo em uma escola privada. Esses trabalhos sustentam a viabilidade de investigar a comunicação digital, sem demonstrar automaticamente sua adequação à escola pública participante deste projeto.')
p('O projeto propõe uma aplicação web para consulta de comunicados, calendário e atividades. A contribuição pretendida consiste em adaptar esses recursos ao acompanhamento realizado por responsáveis de estudantes do 1º ao 5º ano, com navegação simples e informações organizadas. Não se afirma ineditismo das agendas digitais nem funcionamento institucional do sistema do grupo antes de sua implantação e avaliação.')
h('2 DESENVOLVIMENTO');h('2.1 OBJETIVOS')
p('Objetivo geral: desenvolver e avaliar um protótipo de Agenda Escolar Inteligente que centralize a comunicação entre profissionais da escola e responsáveis por estudantes dos anos iniciais do Ensino Fundamental.')
for t in ['Investigar dificuldades de comunicação e condições de acesso digital dos participantes.','Desenvolver interface responsiva e interativa em React.','Planejar e implementar persistência em PostgreSQL por meio do Supabase.','Definir os perfis de gestão escolar, professor e responsável e seus vínculos de acesso.','Organizar comunicados e atividades por prazo e situação de leitura.','Avaliar os principais fluxos por testes funcionais, de acessibilidade e de uso.']:doc.add_paragraph(t,style='List Bullet')
h('2.2 JUSTIFICATIVA E DELIMITAÇÃO DO PROBLEMA')
p('A questão orientadora é: como uma aplicação web pode apoiar a comunicação entre escola e responsáveis, tornando as informações mais organizadas, acessíveis e acompanháveis? A hipótese de trabalho é que a centralização dos registros poderá facilitar sua consulta e reduzir a dispersão de recados. Essa hipótese deverá ser verificada com participantes, sem antecipar resultados positivos.')
p('O escopo inicial compreende comunicados, atividades, calendário, confirmação de leitura e visão de pendências. Lançamento de notas, documentação de guarda, informações de saúde, integração com a SED e envio automático por WhatsApp ficam fora da primeira versão. O acesso será realizado pelo navegador, sem exigir instalação. A escola deverá identificar alternativas para famílias sem acesso regular à internet.')
h('2.3 FUNDAMENTAÇÃO TEÓRICA')
p('Comunicação escolar: Larrosa et al. (2019) discutem o uso de aplicativo na comunicação entre escola e família em um contexto específico. Neste projeto, essa experiência orienta a investigação do recebimento e do retorno dos comunicados, sem generalizar seus resultados para a rede pública. Neves, Silva e Terra (2018) contribuem como referência de calendário e organização de eventos; o público e o contexto daquele estudo diferem dos responsáveis pelos anos iniciais aqui considerados.')
p('Usabilidade: as heurísticas de Jakob Nielsen orientam a visibilidade do estado da aplicação, a consistência e a prevenção de erros. Na agenda, sua aplicação corresponde a feedback após publicação, indicação de confirmação de leitura, campos identificados e navegação previsível. As diretrizes WCAG orientam aspectos de acessibilidade, como uso por teclado e informação que não dependa exclusivamente de cor. A conformidade deverá ser avaliada, e não presumida.')
p('Front-end: React permite compor interfaces com elementos reutilizáveis e gerenciar interações e estado. Será utilizado para calendário, comunicados e formulários. A escolha favorece a organização do código e a evolução da interface. Não se presume maior desempenho apenas pela adoção da biblioteca; carregamento e resposta às ações precisam ser medidos. React é uma biblioteca; a camada de framework deverá ser explicitada na implementação para atender ao requisito acadêmico. A demonstração usa React em uma estrutura compatível com as convenções Next.js, executada pelo Vinext.')
p('Banco de dados: Elmasri e Navathe são referências para a modelagem de entidades, relacionamentos e integridade dos dados. Sua aplicação ao projeto orienta a separação entre alunos, turmas, responsáveis e comunicados. O Supabase disponibiliza PostgreSQL e serviços de autenticação e API, reduzindo a infraestrutura a implementar pela equipe. A autorização deverá utilizar políticas de segurança por linha (RLS), com verificações de vínculo entre usuário, escola e estudante. As tecnologias não eliminam a necessidade de configurar e testar as regras.')
h('2.4 METODOLOGIA')
p('A pesquisa é aplicada e exploratória, associada ao desenvolvimento incremental de um protótipo. Foram realizadas discussões entre integrantes, pesquisa bibliográfica e conversas informais. Foram elaborados dois questionários; conforme o relato original, ainda não havia respostas no período descrito. Por esse motivo, não se apresentam estatísticas de aceitação ou conclusões sobre a eficácia da solução.')
p('As etapas seguintes serão: aplicação dos instrumentos; análise das necessidades; priorização dos requisitos; construção das telas; implementação dos serviços de dados; testes e avaliação com participantes. O código deverá ser mantido em controle de versão com Git. Os registros de teste deverão informar cenário, resultado esperado, resultado observado e correção necessária.')
p('Questionário para a comunidade escolar: https://docs.google.com/forms/d/e/1FAIpQLScXKV7qyj5seRkl4piosnsnlVdRkVfN8UCuW5tt54RXYiv_Zg/viewform')
p('Questionário para responsáveis: https://docs.google.com/forms/d/e/1FAIpQLScZYzL8DYgNG19xQRDKoEG3-2tkcIx22IFVz3KZq3xr98rxjg/viewform')
h('2.5 SOLUÇÃO PROPOSTA E ARQUITETURA')
p('Fluxo previsto: navegador → interface React → API e autenticação do Supabase → banco PostgreSQL com políticas de acesso. Nesta etapa, a demonstração visual funciona com dados fictícios em memória. A troca de perfil é uma simulação de navegação, sem autenticação real. A conexão com Supabase permanece planejada e não deve ser apresentada como implementada.')
p('A gestão escolar administrará turmas e vínculos. Professores publicarão informações para as turmas atribuídas. Responsáveis consultarão os estudantes autorizados e confirmarão a leitura. O vínculo entre responsável e estudante deverá ser validado pela escola; conhecer o nome ou identificador do aluno não poderá conceder acesso.')
p('O modelo proposto contém perfis, escolas, turmas, alunos, matrículas, vínculos de responsáveis, atribuições de professores, comunicados, destinatários, confirmações e eventos. A tabela de vínculos permite vários responsáveis por estudante e vários estudantes por responsável. As confirmações serão individuais por destinatário, sem presumir ciência de todos os responsáveis por uma única leitura.')
p('A agenda inteligente utiliza regras explícitas: destacar mensagens pendentes, ordenar atividades por prazo, mostrar eventos próximos e consolidar confirmações em aberto. Não se afirma uso de aprendizado de máquina. A confirmação de leitura representa ciência declarada do comunicado, não comprovação de execução de uma atividade. Alertas de frequência dependem de um futuro módulo e de critérios definidos pela escola.')
h('2.6 REQUISITOS E CRITÉRIOS DE VALIDAÇÃO')
rows=[('RF01','Publicação de comunicado','Ao publicar um título e uma mensagem válidos, o comunicado aparece na lista.'),('RF02','Confirmação de leitura','Confirmar uma vez altera o estado e reduz a quantidade de pendências, sem duplicar confirmações.'),('RF03','Consulta ao calendário','Selecionar uma data exibe apenas os eventos daquele dia; meses podem ser navegados.'),('RF04','Atividades','Alterar a situação de uma atividade atualiza a lista e o indicador correspondente.'),('RNF01','Interface responsiva','Conteúdo permanece utilizável em celular e computador.'),('RNF02','Acessibilidade','Fluxos principais utilizáveis por teclado, com foco visível e campos rotulados.'),('RNF03','Autorização futura','Usuário autenticado não obtém registros de outra escola ou de aluno sem vínculo.'),('RNF04','Desempenho','Medir carregamento e resposta em ambiente e dispositivo registrados, sem declarar ganho sem comparação.')]
table=doc.add_table(rows=1,cols=3);table.style='Table Grid'
for c,t in zip(table.rows[0].cells,['Identificador','Requisito','Critério de avaliação']):c.text=t
for row in rows:
 for c,t in zip(table.add_row().cells,row):c.text=t
p('A demonstração utilizará exclusivamente dados fictícios. Credenciais privilegiadas não deverão ser incluídas no código do navegador. A implantação com dados reais requer análise institucional dos dados necessários, das permissões e das responsabilidades. Este relatório não afirma conformidade jurídica ou implantação de controles ainda não testados.')
h('2.7 RESULTADOS PRELIMINARES E LIMITAÇÕES')
p('Os resultados documentados são a delimitação do público, a elaboração dos questionários, os requisitos preliminares e a arquitetura proposta. A demonstração visual é um instrumento para discutir os fluxos com a comunidade. Não substitui a implementação do banco, autenticação, autorização ou avaliação em campo. As ações da demonstração são temporárias e reiniciadas ao recarregar a página.')
p('As principais limitações são a ausência de respostas aos instrumentos no período relatado, o caráter informal das observações e a falta de evidências de implantação na escola. Futuras versões deverão registrar os resultados reais dos testes e as alterações decorrentes do retorno dos participantes. Não são apresentados ganhos de desempenho, redução de faltas ou melhoria de aprendizagem sem evidência.')
h('3 CONSIDERAÇÕES FINAIS')
p('A Agenda Escolar Inteligente constitui uma proposta de aplicação dos conhecimentos de desenvolvimento web e banco de dados a uma necessidade de comunicação escolar. O projeto se apoia em experiências publicadas e delimita uma primeira versão centrada em comunicados, calendário e atividades. A escolha de React e Supabase é vinculada à organização da interface e à modelagem dos registros. A continuidade depende da escuta da comunidade, da implementação dos serviços planejados e da validação dos fluxos em condições reais de uso.')
h('REFERÊNCIAS')
refs=[
'ELMASRI, Ramez; NAVATHE, Shamkant B. Fundamentals of Database Systems. 7. ed. Pearson, 2022. Registro eletrônico da edição consultada. Disponível em: https://www.pearson.com/en-us/subject-catalog/p/redirected-product/P200000003546/9780133970777. Acesso em: 8 out. 2026.',
'LARROSA, Sandra Aparecida Ortiz; PERIOTTO, Tania Regina Corredato; SANTOS, Ana Paula Francisca dos; BORTOLOZZI, Flavio. A gestão do conhecimento por meio de um aplicativo de comunicação no contexto escolar: o caso de uma escola da rede privada na região noroeste do Paraná-Brasil. Encontro Internacional de Gestão, Desenvolvimento e Inovação, v. 2, n. 1, 2019. Disponível em: https://periodicos.ufms.br/index.php/EIGEDIN/article/view/7048. Acesso em: 8 out. 2026.',
'NEVES, Vinícius Assis; SILVA, Carlos Eduardo Paulino; TERRA, Daniela Costa. ClassMatch: agenda escolar online. In: Congresso sobre Tecnologias na Educação, 2018. Anais [...]. CEUR Workshop Proceedings, v. 2185, p. 562–568, 2018. Disponível em: https://ceur-ws.org/Vol-2185/CtrlE_2018_paper_21.pdf. Acesso em: 8 out. 2026.',
'NIELSEN, Jakob. 10 Usability Heuristics for User Interface Design. Nielsen Norman Group. Disponível em: https://www.nngroup.com/articles/ten-usability-heuristics/. Acesso em: 8 out. 2026.',
'REACT. Quick Start. Disponível em: https://react.dev/learn. Acesso em: 8 out. 2026.',
'REACT. memo. Disponível em: https://react.dev/reference/react/memo. Acesso em: 8 out. 2026.',
'NEXT.JS. Next.js Docs. Disponível em: https://nextjs.org/docs. Acesso em: 8 out. 2026.',
'SUPABASE. Database. Disponível em: https://supabase.com/docs/guides/database/overview. Acesso em: 8 out. 2026.',
'SUPABASE. Row Level Security. Disponível em: https://supabase.com/docs/guides/database/postgres/row-level-security. Acesso em: 8 out. 2026.',
'WORLD WIDE WEB CONSORTIUM. WCAG 2 Overview. Disponível em: https://www.w3.org/WAI/standards-guidelines/wcag/. Acesso em: 8 out. 2026.'
]
for t in refs:p(t)
h('APÊNDICE A – ROTEIRO DE DEMONSTRAÇÃO')
for t in ['Abrir a agenda e identificar o aviso de dados fictícios.','Consultar os comunicados e confirmar a leitura de um item.','Observar a atualização do total de mensagens pendentes.','Consultar o calendário e selecionar o dia de um evento.','Acessar as atividades e alterar a situação de uma tarefa.','Alternar para a visão de professor e publicar um comunicado de demonstração.','Acessar a apresentação do projeto e consultar tecnologias e referências.','Explicar que a persistência em Supabase e a autenticação real são etapas futuras.']:doc.add_paragraph(t,style='List Number')
footer=s.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
out=Path(__file__).parent/'public'/'Agenda_Escolar_UNIVESP_Atualizado.docx';out.parent.mkdir(exist_ok=True);doc.save(out)
Document(out)
print(str(out))
