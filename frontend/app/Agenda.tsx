"use client";
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { BookOpen, CalendarDays, Check, ArrowUpRight, Plus, ChevronLeft, ChevronRight, GraduationCap, Clock3, FileText, Download, ArrowRight, MessageSquare, CircleCheck, LogOut, UserPlus, UsersRound } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Toaster, toast } from 'sonner';
import api from './services/api';
import './agenda.css';
type Notice = {
    id: string;
    title: string;
    description: string;
    created_at: string;
    id_turmas: string[];
};
type ClassOption = { id: string; nome: string };
type UserRecord = { id: string; nome: string; tipo: string; turmas: string[] };
type RegistrationType = 'aluno' | 'professor' | 'gestor';
const isRegistrationType = (value: string): value is RegistrationType =>
    value === 'aluno' || value === 'professor' || value === 'gestor';
const tasksInitial = [{ id: 1, title: 'Leitura em família', subject: 'Língua Portuguesa', desc: 'Ler uma história e registrar a parte favorita no caderno.', due: '2026-10-09', done: false }, { id: 2, title: 'Formas geométricas em casa', subject: 'Matemática', desc: 'Encontrar e desenhar três formas geométricas em casa.', due: '2026-10-13', done: false }, { id: 3, title: 'Observação de uma planta', subject: 'Ciências', desc: 'Observar uma planta e desenhar suas partes.', due: '2026-10-07', done: true }];
const events = [{ date: '2026-10-09', title: 'Roda de leitura', time: '10h', kind: 'Na sala de aula' }, { date: '2026-10-12', title: 'Feriado · sem aula', time: 'Dia todo', kind: 'Calendário escolar' }, { date: '2026-10-13', title: 'Oficina de arte', time: '09h', kind: 'Semana da infância' }, { date: '2026-10-15', title: 'Reunião de famílias', time: '18h30', kind: 'Sala do 3º ano A' }, { date: '2026-10-23', title: 'Mostra de descobertas', time: '14h', kind: 'Pátio da escola' }];
const referenceDay = '2026-10-08';
const formatDate = (date: string) => new Date(date + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
const formatAnnouncementDate = (date: string) => new Date(date).toLocaleString('pt-BR', { dateStyle: 'medium', timeStyle: 'short' });
const navigation = [{ id: 'inicio', label: 'Visão geral', Icon: BookOpen }, { id: 'comunicados', label: 'Comunicados', Icon: MessageSquare }, { id: 'usuarios', label: 'Usuários', Icon: UsersRound }, { id: 'calendario', label: 'Calendário', Icon: CalendarDays }, { id: 'atividades', label: 'Atividades', Icon: FileText }, { id: 'projeto', label: 'Sobre o projeto', Icon: GraduationCap }];
type AgendaUser = { id: string; nome: string; tipo: string; turma: string; pai: string };
function Calendar({ month, setMonth, day, setDay, compact = false }: {
    month: Date;
    setMonth: (month: Date) => void;
    day: string;
    setDay: (day: string) => void;
    compact?: boolean;
}) {
    const year = month.getFullYear(), m = month.getMonth(), count = new Date(year, m + 1, 0).getDate(), offset = new Date(year, m, 1).getDay();
    return <div className={compact ? 'calendar compact' : 'calendar'}><div className="calendar-head"><h3>{month.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</h3><div><button aria-label="Mês anterior" onClick={() => setMonth(new Date(year, m - 1, 1))}><ChevronLeft size={18}/></button><button aria-label="Próximo mês" onClick={() => setMonth(new Date(year, m + 1, 1))}><ChevronRight size={18}/></button></div></div><div className="calendar-grid">{['D', 'S', 'T', 'Q', 'Q', 'S', 'S'].map((d, i) => <span className="weekday" key={'w' + i}>{d}</span>)}{Array.from({ length: offset }, (_, i) => <span key={'b' + i}/>)}{Array.from({ length: count }, (_, i) => { const key = `${year}-${String(m + 1).padStart(2, '0')}-${String(i + 1).padStart(2, '0')}`, has = events.some(e => e.date === key); return <button key={key} className={(day === key ? 'chosen ' : '') + (key === referenceDay ? 'today ' : '')} onClick={() => setDay(key)} aria-pressed={day === key} aria-label={`${i + 1} de ${month.toLocaleDateString('pt-BR', { month: 'long' })}${has ? ', com evento' : ''}`}>{i + 1}{has && <i />}</button>; })}</div><div className="calendar-legend"><span><i /> Evento escolar</span><span>Referência: 08/10/2026</span></div></div>;
}
export default function Agenda({ user, onLogout }: { user: AgendaUser; onLogout: () => void }) {
    const [tab, setTab] = useState('inicio'), [notices, setNotices] = useState<Notice[]>([]), [tasks, setTasks] = useState(tasksInitial), [selected, setSelected] = useState<string | null>(null), [compose, setCompose] = useState(false), [registerOpen, setRegisterOpen] = useState(false), [registrationType, setRegistrationType] = useState<'aluno' | 'professor' | 'gestor'>('aluno'), [registering, setRegistering] = useState(false), [month, setMonth] = useState(new Date(2026, 9, 1)), [day, setDay] = useState('2026-10-15');
    const [noticeStatus, setNoticeStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
    const [noticeError, setNoticeError] = useState('');
    const [classes, setClasses] = useState<ClassOption[]>([]);
    const [classError, setClassError] = useState('');
    const [publishing, setPublishing] = useState(false);
    const [users, setUsers] = useState<UserRecord[]>([]);
    const [usersStatus, setUsersStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
    const [usersError, setUsersError] = useState('');
    const isStudent = user.tipo === 'aluno';
    const canPublish = ['professor', 'gestao', 'gestor'].includes(user.tipo.trim().toLowerCase());
    const canManageUsers = ['gestao', 'gestor', 'gestão'].includes(user.tipo.trim().toLowerCase());
    const userInitials = user.nome.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
    const remaining = tasks.filter(t => !t.done).length, current = notices.find(n => n.id === selected);
    const loadNotices = useCallback(async () => {
        setNoticeStatus('loading');
        setNoticeError('');
        try {
            const response = await api.get<Notice[]>('/comunicados');
            setNotices(response.data);
            setNoticeStatus('loaded');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            setNoticeError(typeof detail === 'string' ? detail : 'Não foi possível carregar os comunicados.');
            setNoticeStatus('error');
        }
    }, []);

    const loadUsers = useCallback(async () => {
        setUsersStatus('loading');
        setUsersError('');
        try {
            const response = await api.get<UserRecord[]>('/users/');
            setUsers(response.data);
            setUsersStatus('loaded');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            setUsersError(typeof detail === 'string' ? detail : 'Não foi possível carregar os usuários.');
            setUsersStatus('error');
        }
    }, []);

    useEffect(() => {
        void Promise.resolve().then(loadNotices);
    }, [loadNotices]);

    useEffect(() => {
        if (!canPublish) return;
        let active = true;
        api.get<ClassOption[]>('/comunicados/turmas')
            .then(response => {
                if (active) setClasses(response.data);
            })
            .catch((error: unknown) => {
                if (!active) return;
                const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
                setClassError(typeof detail === 'string' ? detail : 'Não foi possível carregar suas turmas.');
            });
        return () => { active = false; };
    }, [canPublish]);

    useEffect(() => {
        if (canManageUsers) {
            void Promise.resolve().then(loadUsers);
        }
    }, [canManageUsers, loadUsers]);

    async function publishCommunication(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const title = String(formData.get('title') || '').trim();
        const description = String(formData.get('description') || '').trim();
        const id_turmas = formData.getAll('id_turmas').map(String);
        if (!title || !description || id_turmas.length === 0) {
            toast.error('Informe o título, a mensagem e selecione ao menos uma turma.');
            return;
        }

        setPublishing(true);
        try {
            await api.post('/comunicados', { title, description, id_turmas });
            await loadNotices();
            setCompose(false);
            setTab('comunicados');
            toast.success('Comunicado publicado.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível publicar o comunicado.');
        } finally {
            setPublishing(false);
        }
    }

    async function registerUser(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const body: {
            id: string;
            type: RegistrationType;
            name: string;
            date_of_birth: string;
            id_turma?: string;
        } = {
            id: String(formData.get('id') || '').trim(),
            type: registrationType,
            name: String(formData.get('name') || '').trim(),
            date_of_birth: String(formData.get('date_of_birth') || ''),
        };
        if (registrationType !== 'gestor') {
            body.id_turma = String(formData.get('id_turma') || '');
        }
        if (!body.id || !body.name || !body.date_of_birth ||
            (registrationType !== 'gestor' && !body.id_turma)) {
            toast.error('Preencha os dados obrigatórios do cadastro.');
            return;
        }

        setRegistering(true);
        try {
            await api.post('/users/register', body);
            await loadUsers();
            setRegisterOpen(false);
            setRegistrationType('aluno');
            toast.success('Usuário cadastrado com sucesso.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível cadastrar o usuário. Confira os dados e tente novamente.');
        } finally {
            setRegistering(false);
        }
    }

    const cards = (list: Notice[]) => list.length ? list.map(n => <article className="notice" key={n.id}><div className="notice-icon comunicado"><MessageSquare size={20}/></div><div className="notice-main"><div className="notice-meta"><span>{formatAnnouncementDate(n.created_at)}</span></div><button className="notice-title" onClick={() => setSelected(n.id)}>{n.title}</button><p>{n.description}</p></div></article>) : <div className="empty"><CircleCheck /><h3>Nenhum comunicado por enquanto</h3><p>Quando houver um recado para suas turmas, ele aparecerá aqui.</p></div>;
    const selectedEvents = events.filter(e => e.date === day);
    return <><Toaster position="bottom-right" richColors/><div className="demo-bar"><span><i /> Demonstração acadêmica · UNIVESP</span><span>Agenda em desenvolvimento</span></div><div className="app-shell"><header className="app-header"><button className="brand" onClick={() => setTab('inicio')} aria-label="Entrelaços, início"><span className="brand-mark"><BookOpen size={26}/><i /></span><span>entrelaços<small>AGENDA ESCOLAR</small></span></button><div className="header-right"><div className="school"><GraduationCap size={19}/><span>Escola Horizonte<small>Unidade de demonstração</small></span></div><span className="avatar" aria-label={user.nome || "Usuário"}>{userInitials}</span><button type="button" className="logout-button" onClick={onLogout}><LogOut size={16}/> Sair</button></div></header>
 <Tabs value={tab} onValueChange={setTab} className="app-tabs"><TabsList className="main-nav">{navigation.filter(({ id }) => id !== 'usuarios' || canManageUsers).map(({ id, label, Icon }) => <TabsTrigger key={id} value={id}><Icon size={17}/><span>{label}</span>{id === 'comunicados' && notices.length > 0 && <b>{notices.length}</b>}</TabsTrigger>)}</TabsList><main><div className="page-heading"><div><div className="eyebrow">{user.turma ? `${user.turma} · ` : ""}Outubro de 2026</div><h1>{tab === 'inicio' ? (isStudent ? `Olá, ${user.nome || "estudante"}.` : 'Agenda da turma') : tab === 'comunicados' ? 'Comunicados' : tab === 'usuarios' ? 'Usuários' : tab === 'calendario' ? 'Calendário escolar' : tab === 'atividades' ? 'Atividades' : 'Sobre o projeto'}</h1><p>{tab === 'inicio' ? 'Confira os comunicados enviados para suas turmas.' : tab === 'comunicados' ? 'Comunicados publicados para suas turmas.' : tab === 'usuarios' ? 'Consulte e cadastre usuários da escola.' : tab === 'calendario' ? 'Consulte as reuniões, os eventos e os feriados.' : tab === 'atividades' ? 'Veja os prazos e marque as atividades concluídas.' : 'Agenda Escolar · Projeto Integrador II · UNIVESP, 2026.'}</p></div>{isStudent ? <div className="student"><span className="student-avatar">{userInitials}</span><span><strong>{user.nome}</strong><small>{user.turma || "Turma não informada"}{user.pai ? ` · Pai: ${user.pai}` : ""}</small></span></div> : <div className="page-actions">{canManageUsers && <button className="secondary" onClick={() => setRegisterOpen(true)}><UserPlus size={16}/> Cadastrar usuário</button>}{canPublish && <button className="primary" onClick={() => setCompose(true)}><Plus size={17}/> Novo comunicado</button>}</div>}</div>
 <TabsContent value="inicio"><section className="stats"><div><span className="stat-icon sage"><MessageSquare /></span><div><span>Comunicados para suas turmas</span><strong>{notices.length}<small> publicados</small></strong></div><button aria-label="Ver comunicados" onClick={() => setTab('comunicados')}><ArrowUpRight /></button></div><div><span className="stat-icon peach"><BookOpen /></span><div><span>Atividades em andamento</span><strong>{remaining}<small> para acompanhar</small></strong></div><button aria-label="Ver atividades" onClick={() => setTab('atividades')}><ArrowUpRight /></button></div><div><span className="stat-icon lavender"><CalendarDays /></span><div><span>Próximo encontro</span><strong>15 out<small> reunião de famílias</small></strong></div><button aria-label="Ver reunião no calendário" onClick={() => { setDay('2026-10-15'); setTab('calendario'); }}><ArrowUpRight /></button></div></section><div className="dashboard"><div><section className="panel"><div className="section-heading"><h2>Últimos comunicados <span>{notices.length}</span></h2><button onClick={() => setTab('comunicados')}>Ver todos <ArrowRight size={15}/></button></div>{noticeStatus === 'loading' ? <p className="quiet notice-state">Carregando comunicados…</p> : noticeStatus === 'error' ? <div className="notice-state"><p role="alert">{noticeError}</p><button className="secondary" onClick={() => void loadNotices()}>Tentar novamente</button></div> : cards(notices.slice(0, 3))}</section></div><aside><section className="panel calendar-panel"><div className="section-heading"><h2>Calendário</h2><CalendarDays size={18}/></div><Calendar month={month} setMonth={setMonth} day={day} setDay={setDay} compact/><div className="day-agenda"><span className="eyebrow">{formatDate(day)} · AGENDA DO DIA</span>{selectedEvents.length ? selectedEvents.map(e => <div className="event-line" key={e.title}><span className="event-bar"/><div><strong>{e.title}</strong><small><Clock3 size={12}/>{e.time} · {e.kind}</small></div></div>) : <p className="quiet">Nenhum evento previsto para este dia.</p>}</div></section></aside></div></TabsContent>
 <TabsContent value="comunicados"><section className="panel"><div className="section-heading"><h2>Mural de comunicados <span>{notices.length}</span></h2>{canPublish && <button type="button" onClick={() => setCompose(true)}><Plus size={16}/> Novo comunicado</button>}</div>{noticeStatus === 'loading' ? <p className="quiet notice-state">Carregando comunicados…</p> : noticeStatus === 'error' ? <div className="notice-state"><p role="alert">{noticeError}</p><button className="secondary" onClick={() => void loadNotices()}>Tentar novamente</button></div> : cards(notices)}</section></TabsContent>
 <TabsContent value="usuarios"><section className="panel"><div className="section-heading"><h2>Usuários cadastrados <span>{users.length}</span></h2><div className="page-actions"><button type="button" className="secondary" onClick={() => void loadUsers()} disabled={usersStatus === 'loading'}>Atualizar</button><button type="button" className="primary" onClick={() => setRegisterOpen(true)}><UserPlus size={16}/> Cadastrar usuário</button></div></div>{usersStatus === 'loading' ? <p className="quiet notice-state">Carregando usuários…</p> : usersStatus === 'error' ? <div className="notice-state"><p role="alert">{usersError}</p><button className="secondary" onClick={() => void loadUsers()}>Tentar novamente</button></div> : users.length === 0 ? <div className="empty"><UsersRound/><h3>Nenhum usuário cadastrado</h3><p>Os usuários adicionados aparecerão nesta lista.</p></div> : <div className="users-table-wrap"><table className="users-table"><thead><tr><th>Identificador</th><th>Nome</th><th>Tipo</th><th>Turma(s)</th></tr></thead><tbody>{users.map(record => <tr key={record.id}><td>{record.id}</td><td>{record.nome}</td><td>{record.tipo === 'gestao' ? 'Gestor' : record.tipo === 'professor' ? 'Professor' : record.tipo === 'aluno' ? 'Aluno' : record.tipo}</td><td>{record.turmas.length ? record.turmas.join(', ') : '—'}</td></tr>)}</tbody></table></div>}</section></TabsContent>
 <TabsContent value="calendario"><div className="calendar-layout"><section className="panel"><Calendar month={month} setMonth={setMonth} day={day} setDay={setDay}/></section><section className="panel"><div className="section-heading"><h2>{formatDate(day)}</h2><CalendarDays size={19}/></div>{selectedEvents.length ? selectedEvents.map(e => <div className="large-event" key={e.title}><span className="tag evento">Evento escolar</span><h3>{e.title}</h3><p><Clock3 size={16}/>{e.time}</p><p>{e.kind}</p></div>) : <div className="empty"><CalendarDays /><h3>Um espaço livre na agenda</h3><p>Não há eventos previstos para este dia.</p></div>}<div className="upcoming"><h3>Próximos no calendário</h3>{events.map(e => <button key={e.date} onClick={() => { setDay(e.date); setMonth(new Date(2026, 9, 1)); }}><span>{formatDate(e.date)}</span>{e.title}<ChevronRight size={16}/></button>)}</div></section></div></TabsContent>
 <TabsContent value="atividades"><div className="tasks-grid">{[...tasks].sort((a, b) => Number(a.done) - Number(b.done) || a.due.localeCompare(b.due)).map(t => <article className={'panel task ' + (t.done ? 'completed' : '')} key={t.id}><div className="task-top"><span className="stat-icon sage"><BookOpen /></span><span className={'tag ' + (t.done ? 'evento' : 'importante')}>{t.done ? 'Concluída' : 'Em andamento'}</span></div><span className="eyebrow">{t.subject}</span><h2>{t.title}</h2><p>{t.desc}</p><div className="task-due"><CalendarDays size={16}/> Entrega: {formatDate(t.due)}</div><button className={t.done ? 'secondary' : 'primary'} onClick={() => { setTasks(v => v.map(x => x.id === t.id ? { ...x, done: !x.done } : x)); toast.success(t.done ? 'Atividade reaberta.' : 'Atividade marcada como concluída.'); }}><Check size={16}/>{t.done ? 'Reabrir atividade' : 'Marcar como concluída'}</button></article>)}</div><p className="helper">A marcação é apenas para organização da família. Não substitui a avaliação do professor.</p></TabsContent>
 <TabsContent value="projeto"><section className="project-intro panel"><div><span className="eyebrow">PROJETO INTEGRADOR II · 2026</span><h2>Agenda escolar<br />para o dia a dia.</h2><p>Uma proposta para organizar a comunicação com responsáveis por estudantes do 1º ao 5º ano do Ensino Fundamental.</p><a className="primary" href="/Agenda_Escolar_UNIVESP_Atualizado.docx" download><Download size={17}/> Baixar relatório atualizado</a></div><div className="project-seal"><GraduationCap size={52}/><strong>UNIVESP</strong><span>Universidade Virtual<br />do Estado de São Paulo</span></div></section><div className="project-grid"><section className="panel text-panel"><h2>Da proposta à aplicação</h2><p>React organiza a interface em componentes reutilizáveis. A demonstração utiliza Vinext, com convenções de aplicação Next.js.</p><p>Os comunicados são consultados e publicados pela API FastAPI, com persistência no Supabase. Calendário e atividades ainda usam dados de demonstração no navegador.</p><p>A agenda reúne comunicados para as turmas autorizadas. Esta demonstração não envia notificações.</p><div className="tech-chips"><span>React</span><span>TypeScript</span><span>FastAPI</span><span>Supabase</span></div></section><section className="panel text-panel"><h2>Fundamentação e referências</h2><a target="_blank" rel="noreferrer" href="https://ceur-ws.org/Vol-2185/CtrlE_2018_paper_21.pdf">Neves, Silva e Terra · ClassMatch (2018)<ArrowUpRight size={17}/></a><a target="_blank" rel="noreferrer" href="https://periodicos.ufms.br/index.php/EIGEDIN/article/view/7048">Larrosa et al. · Comunicação escolar (2019)<ArrowUpRight size={17}/></a><a target="_blank" rel="noreferrer" href="https://www.nngroup.com/articles/ten-usability-heuristics/">Jakob Nielsen · Usabilidade<ArrowUpRight size={17}/></a><p>Elmasri e Navathe fundamentam a modelagem relacional. As documentações de React e Supabase orientam as escolhas técnicas. Referências completas no relatório.</p></section></div><section className="panel text-panel"><h2>Equipe do projeto</h2><p>Beatriz Cerqueira Santos · Bernardo Goisman · Italo Machado de Oliveira · Kauan dos Santos Silva · Leila Margareti Pessoa Silva · Leonardo Davi Silva Klai Vasques · Marcelo Trindade Santos · Silvia Alcantara Dias de Souza</p><small>Tutora: Roberta Cristina Gobi · Polos: Diadema, Jandira e Santo André</small></section></TabsContent>
 </main></Tabs><footer className="app-footer"><span>entrelaços · Agenda escolar</span><span>Protótipo acadêmico · UNIVESP 2026</span></footer></div>
 <Dialog open={selected !== null} onOpenChange={open => { if (!open) setSelected(null); }}><DialogContent className="agenda-dialog"><DialogTitle>{current?.title}</DialogTitle><DialogDescription>{current ? formatAnnouncementDate(current.created_at) : ''}</DialogDescription><p className="full-message">{current?.description}</p></DialogContent></Dialog>
 <Dialog open={compose} onOpenChange={setCompose}><DialogContent className="agenda-dialog"><DialogTitle>Novo comunicado</DialogTitle><DialogDescription>Escolha uma ou mais turmas para receber o comunicado.</DialogDescription><form onSubmit={publishCommunication}><label htmlFor="notice-title">Título</label><input id="notice-title" name="title" placeholder="Assunto do comunicado" required maxLength={200}/><label htmlFor="notice-description">Mensagem</label><textarea id="notice-description" name="description" placeholder="Escreva o recado para as famílias…" required maxLength={10000} rows={5}/><span className="form-label">Turmas destinatárias</span>{classError ? <p role="alert">{classError}</p> : classes.length ? <div className="class-options">{classes.map(classOption => <label className="class-option" key={classOption.id}><input type="checkbox" name="id_turmas" value={classOption.id}/><span>{classOption.nome}</span></label>)}</div> : <p className="helper">Nenhuma turma disponível para publicação.</p>}<button className="primary" type="submit" disabled={publishing || classes.length === 0}><Plus size={17}/>{publishing ? 'Publicando…' : 'Publicar comunicado'}</button></form></DialogContent></Dialog>
 <Dialog open={registerOpen} onOpenChange={setRegisterOpen}><DialogContent className="agenda-dialog"><DialogTitle>Cadastrar usuário</DialogTitle><DialogDescription>Cadastro disponível somente para a gestão.</DialogDescription><form onSubmit={registerUser}><label htmlFor="user-type">Tipo de usuário</label><select id="user-type" name="type" value={registrationType} onChange={event => { if (isRegistrationType(event.target.value)) setRegistrationType(event.target.value); }}><option value="aluno">Aluno</option><option value="professor">Professor</option><option value="gestor">Gestor</option></select><label htmlFor="user-id">Identificador</label><input id="user-id" name="id" placeholder="Digite o identificador" required maxLength={100}/><label htmlFor="user-name">Nome completo</label><input id="user-name" name="name" placeholder="Digite o nome completo" required maxLength={200}/><label htmlFor="user-date-of-birth">Data de nascimento</label><input id="user-date-of-birth" name="date_of_birth" type="date" required/>{registrationType !== 'gestor' && <><label htmlFor="user-class">Turma</label><select id="user-class" name="id_turma" required defaultValue=""><option value="" disabled>Selecione uma turma</option>{classes.map(classOption => <option key={classOption.id} value={classOption.id}>{classOption.nome}</option>)}</select></>}{classError && registrationType !== 'gestor' && <p role="alert">{classError}</p>}<button className="primary" type="submit" disabled={registering || (registrationType !== 'gestor' && classes.length === 0)}><UserPlus size={17}/>{registering ? 'Cadastrando…' : 'Cadastrar usuário'}</button></form></DialogContent></Dialog></>;
}
