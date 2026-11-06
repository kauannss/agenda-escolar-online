"use client";
import { FormEvent, useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { BookOpen, CalendarDays, Check, ArrowUpRight, Plus, ChevronLeft, ChevronRight, GraduationCap, FileText, Download, ArrowRight, MessageSquare, CircleCheck, LogOut, UserPlus, UsersRound, Pencil, Trash2 } from 'lucide-react';
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
type SchoolEvent = { id: string | number; nome: string; data: string; id_turmas: string[]; turmas?: string[] };
type SchoolActivity = {
    id: string | number;
    created_at: string;
    nome: string;
    professor_id: string;
    professor_nome: string;
    descricao: string;
    data_limite: string;
    materia: string;
    id_turmas: string[];
    turmas: string[];
};
type UserRecord = { id: string; nome: string; tipo: string; turmas: string[] };
type UserEditor = { id: string; nome: string; tipo: RegistrationType; date_of_birth: string; id_turmas: string[] };
type UserEditorResponse = Omit<UserEditor, 'tipo'> & { tipo: string };
type RegistrationType = 'aluno' | 'professor' | 'gestor';
const isRegistrationType = (value: string): value is RegistrationType =>
    value === 'aluno' || value === 'professor' || value === 'gestor';
const localDateKey = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
const formatDate = (date: string) => new Date(date + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
const formatAnnouncementDate = (date: string) => new Date(date).toLocaleString('pt-BR', { dateStyle: 'medium', timeStyle: 'short' });
const navigation = [{ id: 'inicio', label: 'Visão geral', Icon: BookOpen }, { id: 'comunicados', label: 'Comunicados', Icon: MessageSquare }, { id: 'usuarios', label: 'Usuários', Icon: UsersRound }, { id: 'calendario', label: 'Calendário', Icon: CalendarDays }, { id: 'atividades', label: 'Atividades', Icon: FileText }, { id: 'projeto', label: 'Sobre o projeto', Icon: GraduationCap }];
type AgendaUser = { id: string; nome: string; tipo: string; turma: string; pai: string };
function Calendar({ month, setMonth, day, setDay, events, compact = false }: {
    month: Date;
    setMonth: (month: Date) => void;
    day: string;
    setDay: (day: string) => void;
    events: SchoolEvent[];
    compact?: boolean;
}) {
    const year = month.getFullYear(), m = month.getMonth(), count = new Date(year, m + 1, 0).getDate(), offset = new Date(year, m, 1).getDay();
    const today = localDateKey(new Date());
    return <div className={compact ? 'calendar compact' : 'calendar'}><div className="calendar-head"><h3>{month.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</h3><div><button aria-label="Mês anterior" onClick={() => setMonth(new Date(year, m - 1, 1))}><ChevronLeft size={18}/></button><button aria-label="Próximo mês" onClick={() => setMonth(new Date(year, m + 1, 1))}><ChevronRight size={18}/></button></div></div><div className="calendar-grid">{['D', 'S', 'T', 'Q', 'Q', 'S', 'S'].map((d, i) => <span className="weekday" key={'w' + i}>{d}</span>)}{Array.from({ length: offset }, (_, i) => <span key={'b' + i}/>)}{Array.from({ length: count }, (_, i) => { const key = `${year}-${String(m + 1).padStart(2, '0')}-${String(i + 1).padStart(2, '0')}`, has = events.some(e => e.data === key); return <button key={key} className={(day === key ? 'chosen ' : '') + (key === today ? 'today ' : '')} onClick={() => setDay(key)} aria-pressed={day === key} aria-label={`${i + 1} de ${month.toLocaleDateString('pt-BR', { month: 'long' })}${has ? ', com evento' : ''}`}>{i + 1}{has && <i />}</button>; })}</div><div className="calendar-legend"><span><i /> Evento escolar</span><span>Hoje: {formatDate(today)}</span></div></div>;
}
export default function Agenda({ user, onLogout }: { user: AgendaUser; onLogout: () => void }) {
    const [tab, setTab] = useState('inicio'), [notices, setNotices] = useState<Notice[]>([]), [tasks, setTasks] = useState<SchoolActivity[]>([]), [completedTaskIds, setCompletedTaskIds] = useState<string[]>([]), [selected, setSelected] = useState<string | null>(null), [compose, setCompose] = useState(false), [registerOpen, setRegisterOpen] = useState(false), [eventOpen, setEventOpen] = useState(false), [activityDialogOpen, setActivityDialogOpen] = useState(false), [editingActivity, setEditingActivity] = useState<SchoolActivity | null>(null), [selectedActivityTeacher, setSelectedActivityTeacher] = useState(''), [registrationType, setRegistrationType] = useState<'aluno' | 'professor' | 'gestor'>('aluno'), [registering, setRegistering] = useState(false), [month, setMonth] = useState(() => { const today = new Date(); return new Date(today.getFullYear(), today.getMonth(), 1); }), [day, setDay] = useState(() => localDateKey(new Date()));
    const [noticeStatus, setNoticeStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
    const [noticeError, setNoticeError] = useState('');
    const [events, setEvents] = useState<SchoolEvent[]>([]);
    const [eventsStatus, setEventsStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
    const [eventsError, setEventsError] = useState('');
    const [classes, setClasses] = useState<ClassOption[]>([]);
    const [classError, setClassError] = useState('');
    const [publishing, setPublishing] = useState(false);
    const [publishingEvent, setPublishingEvent] = useState(false);
    const [users, setUsers] = useState<UserRecord[]>([]);
    const [usersStatus, setUsersStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
    const [usersError, setUsersError] = useState('');
    const [activitiesStatus, setActivitiesStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
    const [activitiesError, setActivitiesError] = useState('');
    const [savingActivity, setSavingActivity] = useState(false);
    const [deletingActivityId, setDeletingActivityId] = useState<string | null>(null);
    const [editingUser, setEditingUser] = useState<UserEditor | null>(null);
    const [editUserType, setEditUserType] = useState<RegistrationType>('aluno');
    const [loadingUserId, setLoadingUserId] = useState<string | null>(null);
    const [savingUser, setSavingUser] = useState(false);
    const [deletingUserId, setDeletingUserId] = useState<string | null>(null);
    const [deletingEventId, setDeletingEventId] = useState<string | null>(null);
    const isStudent = user.tipo === 'aluno';
    const canPublish = ['professor', 'gestao', 'gestor'].includes(user.tipo.trim().toLowerCase());
    const canManageUsers = ['gestao', 'gestor', 'gestão'].includes(user.tipo.trim().toLowerCase());
    const canManageActivities = canPublish;
    const userInitials = user.nome.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
    const remaining = tasks.filter(task => !completedTaskIds.includes(String(task.id))).length, current = notices.find(n => n.id === selected);
    const today = localDateKey(new Date());
    const nextEvent = events.filter(event => event.data >= today).sort((a, b) => a.data.localeCompare(b.data))[0];
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

    const loadEvents = useCallback(async () => {
        setEventsStatus('loading');
        setEventsError('');
        try {
            const response = await api.get<SchoolEvent[]>('/eventos');
            setEvents(response.data);
            setEventsStatus('loaded');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            setEventsError(typeof detail === 'string' ? detail : 'Não foi possível carregar os eventos.');
            setEventsStatus('error');
        }
    }, []);

    const loadActivities = useCallback(async () => {
        setActivitiesStatus('loading');
        setActivitiesError('');
        try {
            const response = await api.get<SchoolActivity[]>('/atividades');
            setTasks(response.data);
            setActivitiesStatus('loaded');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            setActivitiesError(typeof detail === 'string' ? detail : 'Não foi possível carregar as atividades.');
            setActivitiesStatus('error');
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
        void Promise.resolve().then(loadEvents);
    }, [loadEvents]);

    useEffect(() => {
        void Promise.resolve().then(loadActivities);
    }, [loadActivities]);

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

    async function publishSchoolEvent(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const nome = String(formData.get('nome') || '').trim();
        const data = String(formData.get('data') || '');
        const id_turmas = formData.getAll('id_turmas').map(String);
        if (!nome || !data || id_turmas.length === 0) {
            toast.error('Informe o nome, a data e selecione ao menos uma turma.');
            return;
        }

        setPublishingEvent(true);
        try {
            await api.post('/eventos', { nome, data, id_turmas });
            await loadEvents();
            setEventOpen(false);
            toast.success('Evento criado.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível criar o evento.');
        } finally {
            setPublishingEvent(false);
        }
    }

    function openActivityEditor(activity?: SchoolActivity) {
        setEditingActivity(activity || null);
        setSelectedActivityTeacher(activity?.professor_id || '');
        setActivityDialogOpen(true);
    }

    async function saveActivity(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const nome = String(formData.get('nome') || '').trim();
        const materia = String(formData.get('materia') || '').trim();
        const descricao = String(formData.get('descricao') || '').trim();
        const data_limite = String(formData.get('data_limite') || '');
        const id_turmas = formData.getAll('id_turmas').map(String);
        const professor_id = canManageUsers
            ? String(formData.get('professor_id') || '')
            : undefined;
        if (!nome || !materia || !descricao || !data_limite || id_turmas.length === 0 ||
            (canManageUsers && !professor_id)) {
            toast.error('Preencha os dados e selecione ao menos uma turma e um professor responsável.');
            return;
        }

        setSavingActivity(true);
        try {
            const body = { nome, materia, descricao, data_limite, id_turmas, professor_id };
            if (editingActivity) {
                await api.put(`/atividades/${encodeURIComponent(String(editingActivity.id))}`, body);
            } else {
                await api.post('/atividades', body);
            }
            await loadActivities();
            setActivityDialogOpen(false);
            setEditingActivity(null);
            toast.success(editingActivity ? 'Atividade atualizada.' : 'Atividade criada.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível salvar a atividade.');
        } finally {
            setSavingActivity(false);
        }
    }

    async function removeActivity(activity: SchoolActivity) {
        if (!window.confirm(`Excluir permanentemente a atividade "${activity.nome}"?`)) return;
        const activityId = String(activity.id);
        setDeletingActivityId(activityId);
        try {
            await api.delete(`/atividades/${encodeURIComponent(activityId)}`);
            setTasks(current => current.filter(item => String(item.id) !== activityId));
            setCompletedTaskIds(current => current.filter(id => id !== activityId));
            toast.success('Atividade removida.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível remover a atividade.');
        } finally {
            setDeletingActivityId(null);
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

    async function openUserEditor(userId: string) {
        setLoadingUserId(userId);
        try {
            const response = await api.get<UserEditorResponse>(`/users/${encodeURIComponent(userId)}`);
            const data = response.data;
            const type = data.tipo === 'gestao' || data.tipo === 'gestor'
                ? 'gestor'
                : isRegistrationType(data.tipo) ? data.tipo : null;
            if (!type) {
                toast.error('O tipo de usuário retornado pela API é inválido.');
                return;
            }
            const editor: UserEditor = {
                ...data,
                tipo: type,
                date_of_birth: data.date_of_birth.slice(0, 10),
            };
            setEditingUser(editor);
            setEditUserType(type);
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível carregar os dados do usuário.');
        } finally {
            setLoadingUserId(null);
        }
    }

    async function saveUser(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!editingUser) return;
        const formData = new FormData(event.currentTarget);
        const name = String(formData.get('name') || '').trim();
        const date_of_birth = String(formData.get('date_of_birth') || '');
        const id_turmas = formData.getAll('id_turmas').map(String);
        if (!name || !date_of_birth ||
            (editUserType === 'aluno' && id_turmas.length !== 1) ||
            (editUserType === 'professor' && id_turmas.length === 0)) {
            toast.error('Confira o nome, a data de nascimento e os vínculos com as turmas.');
            return;
        }

        setSavingUser(true);
        try {
            await api.put(`/users/${encodeURIComponent(editingUser.id)}`, {
                name,
                type: editUserType,
                date_of_birth,
                id_turmas,
            });
            await loadUsers();
            setEditingUser(null);
            toast.success('Usuário atualizado.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível atualizar o usuário.');
        } finally {
            setSavingUser(false);
        }
    }

    async function removeUser(record: UserRecord) {
        if (!window.confirm(`Excluir permanentemente o usuário "${record.nome}" (${record.id})? Os vínculos de turma e sessões ativas também serão removidos.`)) return;
        setDeletingUserId(record.id);
        try {
            await api.delete(`/users/${encodeURIComponent(record.id)}`);
            await loadUsers();
            toast.success('Usuário removido.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível remover o usuário.');
        } finally {
            setDeletingUserId(null);
        }
    }

    async function removeEvent(event: SchoolEvent) {
        if (!window.confirm(`Excluir o evento "${event.nome}" de todas as turmas vinculadas?`)) return;
        const eventId = String(event.id);
        setDeletingEventId(eventId);
        try {
            await api.delete(`/eventos/${encodeURIComponent(eventId)}`);
            setEvents(currentEvents => currentEvents.filter(item => String(item.id) !== eventId));
            toast.success('Evento removido.');
        } catch (error: unknown) {
            const detail = isAxiosError<{ detail?: unknown }>(error) ? error.response?.data?.detail : undefined;
            toast.error(typeof detail === 'string' ? detail : 'Não foi possível remover o evento.');
        } finally {
            setDeletingEventId(null);
        }
    }

    const cards = (list: Notice[]) => list.length ? list.map(n => <article className="notice" key={n.id}><div className="notice-icon comunicado"><MessageSquare size={20}/></div><div className="notice-main"><div className="notice-meta"><span>{formatAnnouncementDate(n.created_at)}</span></div><button className="notice-title" onClick={() => setSelected(n.id)}>{n.title}</button><p>{n.description}</p></div></article>) : <div className="empty"><CircleCheck /><h3>Nenhum comunicado por enquanto</h3><p>Quando houver um recado para suas turmas, ele aparecerá aqui.</p></div>;
    const selectedEvents = events.filter(event => event.data === day);
    const activityClassOptions = editingActivity
        ? [
            ...classes,
            ...editingActivity.id_turmas
                .map((id, index) => ({
                    id,
                    nome: editingActivity.turmas[index] || `Turma ${id}`,
                }))
                .filter(classOption => !classes.some(item => item.id === classOption.id)),
        ]
        : classes;
    return <><Toaster position="bottom-right" richColors/><div className="demo-bar"><span><i /> Demonstração acadêmica · UNIVESP</span><span>Agenda em desenvolvimento</span></div><div className="app-shell"><header className="app-header"><button className="brand" onClick={() => setTab('inicio')} aria-label="Entrelaços, início"><span className="brand-mark"><BookOpen size={26}/><i /></span><span>entrelaços<small>AGENDA ESCOLAR</small></span></button><div className="header-right"><div className="school"><GraduationCap size={19}/><span>Escola Horizonte<small>Unidade de demonstração</small></span></div><span className="avatar" aria-label={user.nome || "Usuário"}>{userInitials}</span><button type="button" className="logout-button" onClick={onLogout}><LogOut size={16}/> Sair</button></div></header>
 <Tabs value={tab} onValueChange={setTab} className="app-tabs"><TabsList className="main-nav">{navigation.filter(({ id }) => id !== 'usuarios' || canManageUsers).map(({ id, label, Icon }) => <TabsTrigger key={id} value={id}><Icon size={17}/><span>{label}</span>{id === 'comunicados' && notices.length > 0 && <b>{notices.length}</b>}</TabsTrigger>)}</TabsList><main><div className="page-heading"><div><div className="eyebrow">{user.turma ? `${user.turma} · ` : ""}{month.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</div><h1>{tab === 'inicio' ? (isStudent ? `Olá, ${user.nome || "estudante"}.` : 'Agenda da turma') : tab === 'comunicados' ? 'Comunicados' : tab === 'usuarios' ? 'Usuários' : tab === 'calendario' ? 'Calendário escolar' : tab === 'atividades' ? 'Atividades' : 'Sobre o projeto'}</h1><p>{tab === 'inicio' ? 'Confira os comunicados enviados para suas turmas.' : tab === 'comunicados' ? 'Comunicados publicados para suas turmas.' : tab === 'usuarios' ? 'Consulte e cadastre usuários da escola.' : tab === 'calendario' ? 'Consulte as reuniões, os eventos e os feriados.' : tab === 'atividades' ? 'Veja os prazos e marque as atividades concluídas.' : 'Agenda Escolar · Projeto Integrador II · UNIVESP, 2026.'}</p></div>{isStudent && <div className="student"><span className="student-avatar">{userInitials}</span><span><strong>{user.nome}</strong><small>{user.turma || "Turma não informada"}{user.pai ? ` · Pai: ${user.pai}` : ""}</small></span></div>}</div>
 <TabsContent value="inicio"><section className="stats"><div><span className="stat-icon sage"><MessageSquare /></span><div><span>Comunicados para suas turmas</span><strong>{notices.length}<small> publicados</small></strong></div><button aria-label="Ver comunicados" onClick={() => setTab('comunicados')}><ArrowUpRight /></button></div><div><span className="stat-icon peach"><BookOpen /></span><div><span>Atividades em andamento</span><strong>{remaining}<small> para acompanhar</small></strong></div><button aria-label="Ver atividades" onClick={() => setTab('atividades')}><ArrowUpRight /></button></div><div><span className="stat-icon lavender"><CalendarDays /></span><div><span>Próximo evento</span><strong>{nextEvent ? formatDate(nextEvent.data) : '—'}<small>{nextEvent?.nome || 'Nenhum evento previsto'}</small></strong></div><button aria-label="Ver próximo evento no calendário" onClick={() => { if (nextEvent) { setDay(nextEvent.data); setMonth(new Date(`${nextEvent.data}T12:00:00`)); } setTab('calendario'); }}><ArrowUpRight /></button></div></section><div className="dashboard"><div><section className="panel"><div className="section-heading"><h2>Últimos comunicados <span>{notices.length}</span></h2><button onClick={() => setTab('comunicados')}>Ver todos <ArrowRight size={15}/></button></div>{noticeStatus === 'loading' ? <p className="quiet notice-state">Carregando comunicados…</p> : noticeStatus === 'error' ? <div className="notice-state"><p role="alert">{noticeError}</p><button className="secondary" onClick={() => void loadNotices()}>Tentar novamente</button></div> : cards(notices.slice(0, 3))}</section></div><aside><section className="panel calendar-panel"><div className="section-heading"><h2>Calendário</h2><CalendarDays size={18}/></div><Calendar month={month} setMonth={setMonth} day={day} setDay={setDay} events={events} compact/><div className="day-agenda"><span className="eyebrow">{formatDate(day)} · AGENDA DO DIA</span>{eventsStatus === 'loading' ? <p className="quiet">Carregando eventos…</p> : eventsStatus === 'error' ? <div><p role="alert">{eventsError}</p><button className="secondary" onClick={() => void loadEvents()}>Tentar novamente</button></div> : selectedEvents.length ? selectedEvents.map(event => <div className="event-line" key={event.id}><span className="event-bar"/><div><strong>{event.nome}</strong><small>{event.turmas?.join(', ') || 'Evento escolar'}</small></div></div>) : <p className="quiet">Nenhum evento previsto para este dia.</p>}</div></section></aside></div></TabsContent>
 <TabsContent value="comunicados"><section className="panel"><div className="section-heading"><h2>Mural de comunicados <span>{notices.length}</span></h2>{canPublish && <button type="button" onClick={() => setCompose(true)}><Plus size={16}/> Novo comunicado</button>}</div>{noticeStatus === 'loading' ? <p className="quiet notice-state">Carregando comunicados…</p> : noticeStatus === 'error' ? <div className="notice-state"><p role="alert">{noticeError}</p><button className="secondary" onClick={() => void loadNotices()}>Tentar novamente</button></div> : cards(notices)}</section></TabsContent>
 <TabsContent value="usuarios"><section className="panel"><div className="section-heading"><h2>Usuários cadastrados <span>{users.length}</span></h2><div className="page-actions"><button type="button" className="secondary" onClick={() => void loadUsers()} disabled={usersStatus === 'loading'}>Atualizar</button><button type="button" className="primary" onClick={() => setRegisterOpen(true)}><UserPlus size={16}/> Cadastrar usuário</button></div></div>{usersStatus === 'loading' ? <p className="quiet notice-state">Carregando usuários…</p> : usersStatus === 'error' ? <div className="notice-state"><p role="alert">{usersError}</p><button className="secondary" onClick={() => void loadUsers()}>Tentar novamente</button></div> : users.length === 0 ? <div className="empty"><UsersRound/><h3>Nenhum usuário cadastrado</h3><p>Os usuários adicionados aparecerão nesta lista.</p></div> : <div className="users-table-wrap"><table className="users-table"><thead><tr><th>Identificador</th><th>Nome</th><th>Tipo</th><th>Turma(s)</th><th>Ações</th></tr></thead><tbody>{users.map(record => <tr key={record.id}><td>{record.id}</td><td>{record.nome}</td><td>{record.tipo === 'gestao' ? 'Gestor' : record.tipo === 'professor' ? 'Professor' : record.tipo === 'aluno' ? 'Aluno' : record.tipo}</td><td>{record.turmas.length ? record.turmas.join(', ') : '—'}</td><td><div className="table-actions"><button type="button" className="icon-action" aria-label={`Editar ${record.nome}`} title="Editar usuário" disabled={loadingUserId === record.id || deletingUserId === record.id} onClick={() => void openUserEditor(record.id)}><Pencil size={16}/></button>{record.id !== user.id && <button type="button" className="icon-action danger" aria-label={`Remover ${record.nome}`} title="Remover usuário" disabled={deletingUserId === record.id || loadingUserId === record.id} onClick={() => void removeUser(record)}><Trash2 size={16}/></button>}</div></td></tr>)}</tbody></table></div>}</section></TabsContent>
 <TabsContent value="calendario"><div className="calendar-layout"><section className="panel"><div className="section-heading"><h2>Calendário escolar</h2>{canPublish && <button type="button" onClick={() => setEventOpen(true)}><Plus size={16}/> Novo evento</button>}</div>{eventsStatus === 'loading' ? <p className="quiet notice-state">Carregando eventos…</p> : eventsStatus === 'error' ? <div className="notice-state"><p role="alert">{eventsError}</p><button className="secondary" onClick={() => void loadEvents()}>Tentar novamente</button></div> : <Calendar month={month} setMonth={setMonth} day={day} setDay={setDay} events={events}/>}</section><section className="panel"><div className="section-heading"><h2>{formatDate(day)}</h2><CalendarDays size={19}/></div>{selectedEvents.length ? selectedEvents.map(event => <div className="large-event" key={event.id}><span className="tag evento">Evento escolar</span><h3>{event.nome}</h3><p><CalendarDays size={16}/>{formatDate(event.data)}</p><p>{event.turmas?.length ? `Turmas: ${event.turmas.join(', ')}` : 'Evento escolar'}</p>{canManageUsers && <button type="button" className="secondary event-delete" disabled={deletingEventId === String(event.id)} onClick={() => void removeEvent(event)}><Trash2 size={16}/>{deletingEventId === String(event.id) ? 'Excluindo…' : 'Excluir evento'}</button>}</div>) : <div className="empty"><CalendarDays /><h3>Um espaço livre na agenda</h3><p>Não há eventos previstos para este dia.</p></div>}{events.length > 0 && <div className="upcoming"><h3>Próximos no calendário</h3>{events.filter(event => event.data >= today).sort((a, b) => a.data.localeCompare(b.data)).map(event => <button key={event.id} onClick={() => { setDay(event.data); setMonth(new Date(`${event.data}T12:00:00`)); }}><span>{formatDate(event.data)}</span>{event.nome}<ChevronRight size={16}/></button>)}</div>}</section></div></TabsContent>
 <TabsContent value="atividades">
    {canManageActivities ? <section className="panel">
        <div className="section-heading">
            <h2>Atividades cadastradas <span>{tasks.length}</span></h2>
            <div className="page-actions">
                <button type="button" className="secondary" onClick={() => void loadActivities()} disabled={activitiesStatus === 'loading'}>Atualizar</button>
                <button type="button" className="primary" onClick={() => openActivityEditor()}><Plus size={16}/> Nova atividade</button>
            </div>
        </div>
        {activitiesStatus === 'loading' ? <p className="quiet notice-state">Carregando atividades…</p> :
            activitiesStatus === 'error' ? <div className="notice-state"><p role="alert">{activitiesError}</p><button className="secondary" onClick={() => void loadActivities()}>Tentar novamente</button></div> :
            tasks.length === 0 ? <div className="empty"><FileText/><h3>Nenhuma atividade cadastrada</h3><p>As atividades criadas para suas turmas aparecerão aqui.</p></div> :
                <div className="users-table-wrap"><table className="users-table"><thead><tr><th>Atividade</th><th>Matéria</th><th>Prazo</th><th>Turma(s)</th><th>Professor</th><th>Ações</th></tr></thead><tbody>
                    {tasks.map(activity => <tr key={activity.id}><td>{activity.nome}</td><td>{activity.materia}</td><td>{formatDate(activity.data_limite)}</td><td>{activity.turmas.length ? activity.turmas.join(', ') : '—'}</td><td>{activity.professor_nome || activity.professor_id}</td><td><div className="table-actions"><button type="button" className="icon-action" aria-label={`Editar ${activity.nome}`} title="Editar atividade" onClick={() => openActivityEditor(activity)}><Pencil size={16}/></button><button type="button" className="icon-action danger" aria-label={`Remover ${activity.nome}`} title="Remover atividade" disabled={deletingActivityId === String(activity.id)} onClick={() => void removeActivity(activity)}><Trash2 size={16}/></button></div></td></tr>)}
                </tbody></table></div>}
    </section> : activitiesStatus === 'loading' ? <p className="quiet notice-state">Carregando atividades…</p> :
        activitiesStatus === 'error' ? <div className="panel notice-state"><p role="alert">{activitiesError}</p><button className="secondary" onClick={() => void loadActivities()}>Tentar novamente</button></div> :
            tasks.length === 0 ? <div className="panel empty"><FileText/><h3>Nenhuma atividade por enquanto</h3><p>Quando o professor publicar atividades para sua turma, elas aparecerão aqui.</p></div> :
                <div className="tasks-grid">{[...tasks].sort((a, b) => Number(completedTaskIds.includes(String(a.id))) - Number(completedTaskIds.includes(String(b.id))) || a.data_limite.localeCompare(b.data_limite)).map(activity => {
                    const isCompleted = completedTaskIds.includes(String(activity.id));
                    return <article className={'panel task ' + (isCompleted ? 'completed' : '')} key={activity.id}>
                        <div className="task-top"><span className="stat-icon sage"><BookOpen /></span><span className={'tag ' + (isCompleted ? 'evento' : 'importante')}>{isCompleted ? 'Concluída' : 'Em andamento'}</span></div>
                        <span className="eyebrow">{activity.materia}</span><h2>{activity.nome}</h2><p>{activity.descricao}</p>
                        <div className="task-due"><CalendarDays size={16}/> Entrega: {formatDate(activity.data_limite)}</div>
                        <button className={isCompleted ? 'secondary' : 'primary'} onClick={() => { setCompletedTaskIds(current => isCompleted ? current.filter(id => id !== String(activity.id)) : [...current, String(activity.id)]); toast.success(isCompleted ? 'Atividade reaberta.' : 'Atividade marcada como concluída.'); }}><Check size={16}/>{isCompleted ? 'Reabrir atividade' : 'Marcar como concluída'}</button>
                    </article>;
                })}</div>}
    {!canManageActivities && <p className="helper">A marcação é apenas para organização da família. Não substitui a avaliação do professor.</p>}
 </TabsContent>
 <TabsContent value="projeto"><section className="project-intro panel"><div><span className="eyebrow">PROJETO INTEGRADOR II · 2026</span><h2>Agenda escolar<br />para o dia a dia.</h2><p>Uma proposta para organizar a comunicação com responsáveis por estudantes do 1º ao 5º ano do Ensino Fundamental.</p><a className="primary" href="/Agenda_Escolar_UNIVESP_Atualizado.docx" download><Download size={17}/> Baixar relatório atualizado</a></div><div className="project-seal"><GraduationCap size={52}/><strong>UNIVESP</strong><span>Universidade Virtual<br />do Estado de São Paulo</span></div></section><div className="project-grid"><section className="panel text-panel"><h2>Da proposta à aplicação</h2><p>React organiza a interface em componentes reutilizáveis. A demonstração utiliza Vinext, com convenções de aplicação Next.js.</p><p>Comunicados, eventos do calendário e atividades são consultados e gerenciados pela API FastAPI, com persistência no Supabase.</p><p>A agenda reúne informações das turmas autorizadas. A marcação de conclusão das atividades ainda é local e não envia notificações.</p><div className="tech-chips"><span>React</span><span>TypeScript</span><span>FastAPI</span><span>Supabase</span></div></section><section className="panel text-panel"><h2>Fundamentação e referências</h2><a target="_blank" rel="noreferrer" href="https://ceur-ws.org/Vol-2185/CtrlE_2018_paper_21.pdf">Neves, Silva e Terra · ClassMatch (2018)<ArrowUpRight size={17}/></a><a target="_blank" rel="noreferrer" href="https://periodicos.ufms.br/index.php/EIGEDIN/article/view/7048">Larrosa et al. · Comunicação escolar (2019)<ArrowUpRight size={17}/></a><a target="_blank" rel="noreferrer" href="https://www.nngroup.com/articles/ten-usability-heuristics/">Jakob Nielsen · Usabilidade<ArrowUpRight size={17}/></a><p>Elmasri e Navathe fundamentam a modelagem relacional. As documentações de React e Supabase orientam as escolhas técnicas. Referências completas no relatório.</p></section></div><section className="panel text-panel"><h2>Equipe do projeto</h2><p>Beatriz Cerqueira Santos · Bernardo Goisman · Italo Machado de Oliveira · Kauan dos Santos Silva · Leila Margareti Pessoa Silva · Leonardo Davi Silva Klai Vasques · Marcelo Trindade Santos · Silvia Alcantara Dias de Souza</p><small>Tutora: Roberta Cristina Gobi · Polos: Diadema, Jandira e Santo André</small></section></TabsContent>
 </main></Tabs><footer className="app-footer"><span>entrelaços · Agenda escolar</span><span>Protótipo acadêmico · UNIVESP 2026</span></footer></div>
 <Dialog open={selected !== null} onOpenChange={open => { if (!open) setSelected(null); }}><DialogContent className="agenda-dialog"><DialogTitle>{current?.title}</DialogTitle><DialogDescription>{current ? formatAnnouncementDate(current.created_at) : ''}</DialogDescription><p className="full-message">{current?.description}</p></DialogContent></Dialog>
 <Dialog open={compose} onOpenChange={setCompose}><DialogContent className="agenda-dialog"><DialogTitle>Novo comunicado</DialogTitle><DialogDescription>Escolha uma ou mais turmas para receber o comunicado.</DialogDescription><form onSubmit={publishCommunication}><label htmlFor="notice-title">Título</label><input id="notice-title" name="title" placeholder="Assunto do comunicado" required maxLength={200}/><label htmlFor="notice-description">Mensagem</label><textarea id="notice-description" name="description" placeholder="Escreva o recado para as famílias…" required maxLength={10000} rows={5}/><span className="form-label">Turmas destinatárias</span>{classError ? <p role="alert">{classError}</p> : classes.length ? <div className="class-options">{classes.map(classOption => <label className="class-option" key={classOption.id}><input type="checkbox" name="id_turmas" value={classOption.id}/><span>{classOption.nome}</span></label>)}</div> : <p className="helper">Nenhuma turma disponível para publicação.</p>}<button className="primary" type="submit" disabled={publishing || classes.length === 0}><Plus size={17}/>{publishing ? 'Publicando…' : 'Publicar comunicado'}</button></form></DialogContent></Dialog>
 <Dialog open={eventOpen} onOpenChange={setEventOpen}><DialogContent className="agenda-dialog"><DialogTitle>Novo evento</DialogTitle><DialogDescription>Informe o evento e escolha uma ou mais turmas.</DialogDescription><form onSubmit={publishSchoolEvent}><label htmlFor="event-name">Nome do evento</label><input id="event-name" name="nome" placeholder="Ex.: Reunião de famílias" required maxLength={200}/><label htmlFor="event-date">Data</label><input id="event-date" name="data" type="date" required/><span className="form-label">Turmas</span>{classError ? <p role="alert">{classError}</p> : classes.length ? <div className="class-options">{classes.map(classOption => <label className="class-option" key={classOption.id}><input type="checkbox" name="id_turmas" value={classOption.id}/><span>{classOption.nome}</span></label>)}</div> : <p className="helper">Nenhuma turma disponível para eventos.</p>}<button className="primary" type="submit" disabled={publishingEvent || classes.length === 0}><Plus size={17}/>{publishingEvent ? 'Criando…' : 'Criar evento'}</button></form></DialogContent></Dialog>
 <Dialog open={registerOpen} onOpenChange={setRegisterOpen}><DialogContent className="agenda-dialog"><DialogTitle>Cadastrar usuário</DialogTitle><DialogDescription>Cadastro disponível somente para a gestão.</DialogDescription><form onSubmit={registerUser}><label htmlFor="user-type">Tipo de usuário</label><select id="user-type" name="type" value={registrationType} onChange={event => { if (isRegistrationType(event.target.value)) setRegistrationType(event.target.value); }}><option value="aluno">Aluno</option><option value="professor">Professor</option><option value="gestor">Gestor</option></select><label htmlFor="user-id">Identificador</label><input id="user-id" name="id" placeholder="Digite o identificador" required maxLength={100}/><label htmlFor="user-name">Nome completo</label><input id="user-name" name="name" placeholder="Digite o nome completo" required maxLength={200}/><label htmlFor="user-date-of-birth">Data de nascimento</label><input id="user-date-of-birth" name="date_of_birth" type="date" required/>{registrationType !== 'gestor' && <><label htmlFor="user-class">Turma</label><select id="user-class" name="id_turma" required defaultValue=""><option value="" disabled>Selecione uma turma</option>{classes.map(classOption => <option key={classOption.id} value={classOption.id}>{classOption.nome}</option>)}</select></>}{classError && registrationType !== 'gestor' && <p role="alert">{classError}</p>}<button className="primary" type="submit" disabled={registering || (registrationType !== 'gestor' && classes.length === 0)}><UserPlus size={17}/>{registering ? 'Cadastrando…' : 'Cadastrar usuário'}</button></form></DialogContent></Dialog>
 <Dialog open={editingUser !== null} onOpenChange={open => { if (!open && !savingUser) setEditingUser(null); }}><DialogContent className="agenda-dialog"><DialogTitle>Editar usuário</DialogTitle><DialogDescription>O identificador do usuário não pode ser alterado.</DialogDescription>{editingUser && <form key={editingUser.id} onSubmit={saveUser}><label htmlFor="edit-user-id">Identificador</label><input id="edit-user-id" value={editingUser.id} readOnly/><label htmlFor="edit-user-name">Nome completo</label><input id="edit-user-name" name="name" defaultValue={editingUser.nome} required maxLength={200}/><label htmlFor="edit-user-type">Tipo de usuário</label><select id="edit-user-type" name="type" value={editUserType} onChange={event => { if (isRegistrationType(event.target.value)) setEditUserType(event.target.value); }}><option value="aluno">Aluno</option><option value="professor">Professor</option><option value="gestor">Gestor</option></select><label htmlFor="edit-user-birth">Data de nascimento</label><input id="edit-user-birth" name="date_of_birth" type="date" defaultValue={editingUser.date_of_birth} required/>{editUserType !== 'gestor' && <><span className="form-label">{editUserType === 'aluno' ? 'Turma do aluno' : 'Turmas do professor'}</span>{classError ? <p role="alert">{classError}</p> : classes.length ? <div className="class-options">{classes.map(classOption => <label className="class-option" key={classOption.id}><input type={editUserType === 'aluno' ? 'radio' : 'checkbox'} name="id_turmas" value={classOption.id} defaultChecked={editingUser.id_turmas.includes(classOption.id)}/><span>{classOption.nome}</span></label>)}</div> : <p className="helper">Nenhuma turma disponível.</p>}</>}<button className="primary" type="submit" disabled={savingUser || (editUserType !== 'gestor' && classes.length === 0)}><Pencil size={16}/>{savingUser ? 'Salvando…' : 'Salvar alterações'}</button></form>}</DialogContent></Dialog>
 <Dialog open={activityDialogOpen} onOpenChange={open => { if (!open && !savingActivity) { setActivityDialogOpen(false); setEditingActivity(null); } }}><DialogContent className="agenda-dialog"><DialogTitle>{editingActivity ? 'Editar atividade' : 'Nova atividade'}</DialogTitle><DialogDescription>Preencha os dados e escolha as turmas que receberão a atividade.</DialogDescription><form key={editingActivity ? String(editingActivity.id) : 'new-activity'} onSubmit={saveActivity}><label htmlFor="activity-name">Nome</label><input id="activity-name" name="nome" defaultValue={editingActivity?.nome || ''} required maxLength={200}/><label htmlFor="activity-subject">Matéria</label><input id="activity-subject" name="materia" defaultValue={editingActivity?.materia || ''} required maxLength={200}/><label htmlFor="activity-description">Descrição</label><textarea id="activity-description" name="descricao" defaultValue={editingActivity?.descricao || ''} required maxLength={10000} rows={4}/><label htmlFor="activity-due-date">Data limite</label><input id="activity-due-date" name="data_limite" type="date" defaultValue={editingActivity?.data_limite.slice(0, 10) || ''} required/>{canManageUsers && <><label htmlFor="activity-teacher">Professor responsável</label><select id="activity-teacher" name="professor_id" value={selectedActivityTeacher} onChange={event => setSelectedActivityTeacher(event.target.value)} required><option value="" disabled>Selecione um professor</option>{users.filter(record => record.tipo === 'professor').map(record => <option key={record.id} value={record.id}>{record.nome}</option>)}</select></>}<span className="form-label">Turmas</span>{classError ? <p role="alert">{classError}</p> : classes.length ? <div className="class-options">{classes.map(classOption => <label className="class-option" key={classOption.id}><input type="checkbox" name="id_turmas" value={classOption.id} defaultChecked={editingActivity?.id_turmas.includes(classOption.id) || false}/><span>{classOption.nome}</span></label>)}</div> : <p className="helper">Nenhuma turma disponível para atividades.</p>}<button className="primary" type="submit" disabled={savingActivity || classes.length === 0 || (canManageUsers && users.every(record => record.tipo !== 'professor'))}><Pencil size={16}/>{savingActivity ? 'Salvando…' : editingActivity ? 'Salvar alterações' : 'Criar atividade'}</button></form></DialogContent></Dialog></>;
}
