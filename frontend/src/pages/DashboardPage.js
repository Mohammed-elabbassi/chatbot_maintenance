// src/pages/DashboardPage.js
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sendQuestion, exportExcel } from '../services/api';
import ReactMarkdown from 'react-markdown';
import './DashboardPage.css';

const RESPONSE_MODES = [
  {
    id: 'data',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
      </svg>
    ),
    label: 'LES DONNÉES',
    desc: 'Résultats uniquement',
  },
  {
    id: 'data_sql',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        <path d="M9 17l-2 2 2 2M15 17l2 2-2 2M11 21l2-8" strokeWidth="1.5"/>
      </svg>
    ),
    label: 'DONNÉES AVEC REQUÊTES',
    desc: 'Données + SQL',
  },
  {
    id: 'data_sql_excel',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14,2 14,8 20,8"/>
        <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10,9 9,9 8,9"/>
      </svg>
    ),
    label: 'DONNÉES/REQUÊTES/TÉLÉCHARGER',
    desc: 'Données + SQL + Excel',
  },
];

function TypingIndicator() {
  return (
    <div className="msg bot fade-in">
      <div className="msg-avatar bot-avatar">
        <BotIcon />
      </div>
      <div className="msg-bubble typing-bubble">
        <span className="dot d1" /><span className="dot d2" /><span className="dot d3" />
      </div>
    </div>
  );
}

function BotIcon() {
  return (
    <svg viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="16" fill="url(#botGrad)"/>
      <defs>
        <linearGradient id="botGrad" x1="0" y1="0" x2="32" y2="32">
          <stop offset="0%" stopColor="#00c9b1"/>
          <stop offset="100%" stopColor="#2196f3"/>
        </linearGradient>
      </defs>
      <circle cx="12" cy="14" r="2" fill="white"/>
      <circle cx="20" cy="14" r="2" fill="white"/>
      <path d="M10 20 Q16 24 22 20" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round"/>
      <rect x="14" y="7" width="4" height="3" rx="1" fill="white" opacity="0.8"/>
    </svg>
  );
}

function DataTable({ rows, columns }) {
  if (!rows || rows.length === 0) return null;
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>{columns.map(c => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((row, i) => (
            <tr key={i}>
              {columns.map(c => (
                <td key={c}>{row[c] === null || row[c] === undefined ? '—' : String(row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 20 && (
        <p className="table-more">… et {rows.length - 20} autres résultats</p>
      )}
    </div>
  );
}

function SqlBlock({ sql }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="sql-block">
      <div className="sql-header">
        <span>SQL</span>
        <button onClick={copy} className="copy-btn">{copied ? '✓ Copié' : '⎘ Copier'}</button>
      </div>
      <pre className="sql-code">{sql}</pre>
    </div>
  );
}

function Message({ msg, responseMode, onDownload }) {
  return (
    <div className={`msg ${msg.role} fade-in`}>
      <div className={`msg-avatar ${msg.role}-avatar`}>
        {msg.role === 'bot' ? <BotIcon /> : <span>{msg.userInitial}</span>}
      </div>
      <div className="msg-content">
        <div className="msg-bubble">
          <div className="msg-text">
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>

          {msg.data && msg.data.rows && msg.data.rows.length > 0 && (
            <DataTable rows={msg.data.rows} columns={msg.data.columns} />
          )}

          {(responseMode === 'data_sql' || responseMode === 'data_sql_excel') && msg.data?.sql && (
            <SqlBlock sql={msg.data.sql} />
          )}

          {responseMode === 'data_sql_excel' && msg.data?.rows?.length > 0 && (
            <button
              className="download-btn"
              onClick={() => onDownload(msg.data.rows, msg.data.columns)}
            >
              📥 Télécharger Excel ({msg.data.row_count} lignes)
            </button>
          )}
        </div>
        <span className="msg-time">{msg.time}</span>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user, logout, ALL_TENANTS } = useAuth();
  const navigate = useNavigate();

  const [activeTenant, setActiveTenant] = useState(null);
  const [responseMode, setResponseMode] = useState('data');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchTenant, setSearchTenant] = useState('');

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const authorizedIds = user?.authorizedTenants?.map(t => t.id) || [];

  // Set default tenant on load
  useEffect(() => {
    if (user && !activeTenant) {
      const defaultTenant =
        user.authorizedTenants?.find(t => t.id === 'v3_tenant_Site_Safi') ||
        user.authorizedTenants?.[0] ||
        null;
      if (defaultTenant) {
        setActiveTenant(defaultTenant);
        setMessages([{
          role: 'bot',
          text: `Bonjour **${user.prenom || user.email}**. Le tenant **'${defaultTenant.id}'** est actuellement sélectionné. Vos questions concerneront ce tenant. Comment puis-je vous aider ?`,
          time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          id: Date.now(),
        }]);
      }
    }
  }, [user]); // eslint-disable-line

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleTenantSelect = (tenant) => {
    if (!authorizedIds.includes(tenant.id)) return;
    setActiveTenant(tenant);
    const now = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, {
      role: 'bot',
      text: `Tenant changé : **${tenant.id}** est maintenant actif. Vos prochaines questions concerneront ce tenant.`,
      time: now,
      id: Date.now(),
    }]);
  };

  const handleSend = useCallback(async () => {
    const q = input.trim();
    if (!q || loading || !activeTenant) return;

    const now = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    const userMsg = {
      role: 'user',
      text: q,
      time: now,
      id: Date.now(),
      userInitial: (user?.prenom?.[0] || user?.email?.[0] || 'U').toUpperCase(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const result = await sendQuestion(q, activeTenant.id, responseMode);
      const botNow = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

      if (result.success) {
        const d = result.data;
        setMessages(prev => [...prev, {
          role: 'bot',
          text: d.natural_response || '_Aucune réponse reçue._',
          time: botNow,
          id: Date.now() + 1,
          data: {
            rows: d.rows || [],
            columns: d.columns || [],
            sql: d.sql || null,
            row_count: d.row_count || 0,
          },
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: `❌ **Erreur :** ${result.error}`,
          time: botNow,
          id: Date.now() + 1,
        }]);
      }
    } catch {
      const botNow = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      setMessages(prev => [...prev, {
        role: 'bot',
        text: '❌ Erreur de connexion au serveur.',
        time: botNow,
        id: Date.now() + 1,
      }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, activeTenant, responseMode, user]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDownload = async (rows, columns) => {
    await exportExcel(rows, columns, 'ichat_export');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filteredTenants = ALL_TENANTS.filter(t =>
    t.label.toLowerCase().includes(searchTenant.toLowerCase())
  );

  if (!user) return null;

  return (
    <div className="dashboard">
      {/* ── TOPBAR ─────────────────────────────────────────────── */}
      <header className="topbar">
        <div className="topbar-left">
          <div className="topbar-logo">
            <svg viewBox="0 0 32 32" fill="none" width="28" height="28">
              <rect width="32" height="32" rx="8" fill="url(#topGrad)"/>
              <defs>
                <linearGradient id="topGrad" x1="0" y1="0" x2="32" y2="32">
                  <stop offset="0%" stopColor="#00c9b1"/><stop offset="100%" stopColor="#2196f3"/>
                </linearGradient>
              </defs>
              <circle cx="11" cy="14" r="2" fill="white"/>
              <circle cx="16" cy="12" r="2" fill="white"/>
              <circle cx="21" cy="14" r="2" fill="white"/>
            </svg>
            <span className="topbar-title">CHATBOT MULTI-TENANT</span>
          </div>
        </div>
        <div className="topbar-center">
          <span className="dashboard-title">
            Tableau de bord de{' '}
            <strong>{user.prenom || user.email}</strong>
            {activeTenant && (
              <>
                {' '}-{' '}
                <span className="tenant-badge-name">{'{' + activeTenant.id + '}'}</span>{' '}
                <span className="status-dot">ACTIF</span>
              </>
            )}
          </span>
        </div>
        <div className="topbar-right">
          <div className="user-menu">
            <div className="user-avatar">
              {(user.prenom?.[0] || user.email?.[0] || 'U').toUpperCase()}
            </div>
            <span>{(user.prenom || user.email || 'USER').toUpperCase()}</span>
            <span className="caret">▾</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {/* ── BODY ──────────────────────────────────────────────── */}
      <div className="dashboard-body">

        {/* ── LEFT: Tenant List ─────────────────────────────── */}
        <aside className="tenant-panel">
          <h3 className="panel-title">LISTE DES TENANTS</h3>
          <div className="tenant-search">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Rechercher"
              value={searchTenant}
              onChange={e => setSearchTenant(e.target.value)}
            />
          </div>
          <ul className="tenant-list">
            {filteredTenants.map(tenant => {
              const isAuth = authorizedIds.includes(tenant.id);
              const isActive = activeTenant?.id === tenant.id;
              return (
                <li
                  key={tenant.id}
                  className={`tenant-item ${isActive ? 'active' : ''} ${!isAuth ? 'locked' : ''}`}
                  onClick={() => isAuth && handleTenantSelect(tenant)}
                  title={!isAuth ? 'Accès non autorisé' : tenant.id}
                >
                  <span className={`tenant-radio ${isActive ? 'selected' : ''}`}>
                    {isActive ? '●' : isAuth ? '○' : ''}
                  </span>
                  <span className="tenant-check">
                    {isAuth ? '✅' : '🔒'}
                  </span>
                  <span className="tenant-label">{tenant.label}</span>
                  {isAuth && <span className="tenant-allowed">(allowed)</span>}
                </li>
              );
            })}
          </ul>
        </aside>

        {/* ── CENTER: Chat ──────────────────────────────────── */}
        <main className="chat-panel">
          <div className="chat-messages">
            {messages.map(msg => (
              <Message
                key={msg.id}
                msg={msg}
                responseMode={responseMode}
                onDownload={handleDownload}
              />
            ))}
            {loading && <TypingIndicator />}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-bar">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Écrivez votre question ici..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading || !activeTenant}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={loading || !input.trim() || !activeTenant}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M2 21l21-9L2 3v7l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </main>

        {/* ── RIGHT: Response Options ───────────────────────── */}
        <aside className="options-panel">
          <h3 className="panel-title">OPTIONS DE RÉPONSE</h3>
          <div className="options-list">
            {RESPONSE_MODES.map(mode => (
              <button
                key={mode.id}
                className={`option-card ${responseMode === mode.id ? 'active' : ''}`}
                onClick={() => setResponseMode(mode.id)}
              >
                <div className="option-radio">
                  <span className={responseMode === mode.id ? 'radio-on' : 'radio-off'} />
                </div>
                <div className="option-icon">{mode.icon}</div>
                <span className="option-label">{mode.label}</span>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
