import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Lock, User, LogIn, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { isAuthenticated, login } from '../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('Vinícius');
  const [password, setPassword] = useState('master');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated()) {
      const next = router.query.next || '/';
      router.replace(next);
    }
  }, [router]);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username.trim(), password);
      const next = router.query.next || '/';
      router.replace(typeof next === 'string' ? next : '/');
    } catch (err) {
      setError(err.message || 'Erro ao autenticar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Entrar — ConfiMinas Engenharia</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="login-bg">
        <div className="login-card">
          <div className="login-logo-wrap">
            <img
              src="/login-logo.png"
              alt="ConfiMinas Engenharia"
              className="login-logo"
              draggable={false}
            />
          </div>

          <div className="login-header">
            <h1>Sistema de Manutenção Preditiva</h1>
            <p>Acesse sua conta para continuar</p>
          </div>

          <form onSubmit={submit} className="login-form" autoComplete="on">
            <label className="login-field">
              <span className="login-label">Usuário</span>
              <div className="login-input-wrap">
                <span className="login-input-icon"><User size={16} /></span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Vinícius"
                  autoComplete="username"
                  required
                />
              </div>
            </label>

            <label className="login-field">
              <span className="login-label">Senha</span>
              <div className="login-input-wrap">
                <span className="login-input-icon"><Lock size={16} /></span>
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="login-eye"
                  onClick={() => setShowPass((s) => !s)}
                  aria-label={showPass ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </label>

            {error && (
              <div className="login-error" role="alert">
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}

            <button type="submit" disabled={loading} className="login-submit">
              {loading ? (
                'Entrando…'
              ) : (
                <>
                  <LogIn size={15} /> Entrar
                </>
              )}
            </button>

          </form>

          <div className="login-footer">
            ConfiMinas Engenharia · Manutenção Preditiva
          </div>
        </div>
      </div>

      <style jsx>{`
        .login-bg {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          background:
            radial-gradient(ellipse 60% 50% at 20% 0%, rgba(59, 108, 244, 0.18), transparent 60%),
            radial-gradient(ellipse 50% 45% at 90% 100%, rgba(99, 102, 241, 0.14), transparent 60%),
            linear-gradient(180deg, #eef2f8 0%, #dde6f3 100%);
        }
        .login-card {
          width: 100%;
          max-width: 420px;
          background: #ffffff;
          border: 1px solid var(--border);
          border-radius: 20px;
          box-shadow: 0 20px 55px rgba(15, 23, 42, 0.12),
                      0 4px 14px rgba(15, 23, 42, 0.06);
          padding: 32px 30px 26px;
          animation: fadeUp 0.45s ease forwards;
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .login-logo-wrap {
          display: flex;
          justify-content: center;
          margin-bottom: 20px;
        }
        .login-logo {
          width: 190px;
          max-width: 100%;
          height: auto;
          user-select: none;
        }
        .login-header {
          text-align: center;
          margin-bottom: 22px;
        }
        .login-header h1 {
          font-size: 15px;
          font-weight: 700;
          color: var(--text);
          margin: 0 0 4px;
        }
        .login-header p {
          font-size: 12.5px;
          color: var(--muted);
          margin: 0;
        }
        .login-form {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .login-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .login-label {
          font-size: 11px;
          font-weight: 600;
          color: var(--text-label);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .login-input-wrap {
          display: flex;
          align-items: center;
          background: #f8fafc;
          border: 1px solid var(--border);
          border-radius: 12px;
          transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
          overflow: hidden;
        }
        .login-input-wrap:focus-within {
          border-color: var(--blue);
          background: #fff;
          box-shadow: var(--ring);
        }
        .login-input-icon {
          display: flex;
          align-items: center;
          padding: 0 8px 0 13px;
          color: var(--muted);
          pointer-events: none;
          flex-shrink: 0;
        }
        .login-input-wrap input {
          flex: 1;
          padding: 11px 10px 11px 4px;
          border: none;
          background: transparent;
          font-size: 14px;
          color: var(--text);
          font-family: inherit;
          outline: none;
        }
        .login-eye {
          display: flex;
          align-items: center;
          padding: 0 10px;
          background: transparent;
          border: 0;
          color: var(--muted);
          cursor: pointer;
          border-radius: 0;
          align-self: stretch;
        }
        .login-eye:hover { color: var(--text); background: #f1f5f9; }
        .login-error {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12.5px;
          color: #b91c1c;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 10px;
          padding: 9px 12px;
        }
        .login-submit {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          line-height: 1;
          margin-top: 4px;
          padding: 12px 16px;
          border-radius: 12px;
          background: linear-gradient(180deg, #4274f7 0%, #3b6cf4 100%);
          color: #fff;
          border: 1px solid #2f5fe6;
          font-weight: 600;
          font-size: 14px;
          cursor: pointer;
          box-shadow: 0 6px 16px rgba(59, 108, 244, 0.28);
          transition: transform 0.08s ease, box-shadow 0.15s ease, opacity 0.15s;
        }
        .login-submit:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 10px 22px rgba(59, 108, 244, 0.32);
        }
        .login-submit:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
        .login-footer {
          margin-top: 22px;
          padding-top: 16px;
          border-top: 1px solid var(--border);
          text-align: center;
          font-size: 11px;
          color: var(--muted);
          letter-spacing: 0.02em;
        }
      `}</style>
    </>
  );
}
