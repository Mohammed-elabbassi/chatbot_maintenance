// src/pages/LoginPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginUser } from '../services/api';
import './LoginPage.css';
const MyLogo = require('./logo.png');

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) { setError('Veuillez saisir votre email.'); return; }
    if (!password.trim()) { setError('Veuillez saisir votre mot de passe.'); return; }
    setLoading(true);
    setError('');
    try {
      const result = await loginUser(email, password);
      if (result.success) {
        login(result.data);
        navigate('/dashboard');
      } else {
        setError(result.error || 'Email ou mot de passe incorrect.');
      }
    } catch {
      setError('Erreur de connexion au serveur.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg">
        <div className="login-bg-circle c1" />
        <div className="login-bg-circle c2" />
        <div className="login-bg-circle c3" />
      </div>

      <div className="login-card fade-in">
        {/* Logo */}
        <div className="login-logo">
          <div className="logo-icon">
            <img src={MyLogo} alt="Logo" style={{width:'80px', height:'60px', objectFit:'contain'}} />
          </div>
          <div className="logo-text">
            <span className="logo-name">I-Chat</span>
            <span className="logo-tagline">Votre Assistant Intelligent</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="login-tabs">
          <button className="tab active">Connexion</button>
        </div>
        <div className="tab-underline" />

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <span className="input-icon">@</span>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="input-group">
            <span className="input-icon">x</span>
            <input
              type={showPass ? 'text' : 'password'}
              placeholder="Passe"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={loading}
            />
            <button
              type="button"
              className="toggle-pass"
              onClick={() => setShowPass(v => !v)}
              tabIndex={-1}
            >
              {showPass ? '👁' : '👁‍🗨'}
            </button>
          </div>

          {error && (
            <div className="login-error fade-in">
              <span>⚠</span> {error}
            </div>
          )}

          <button className="login-btn" type="submit" disabled={loading}>
            {loading ? (
              <span className="btn-spinner" />
            ) : (
              'SE CONNECTER'
            )}
          </button>
        </form>

        {/* Demo hint */}
        <p className="login-hint">Code par défaut : <code>admin</code></p>
      </div>
    </div>
  );
}