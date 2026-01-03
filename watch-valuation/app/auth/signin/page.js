'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export default function SignIn() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await signIn('credentials', {
        redirect: false,
        email,
        password,
      });

      if (result?.error) {
        setError(result.error);
      } else {
        router.push('/');
      }
    } catch (err) {
      setError('Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  const styles = {
    container: {
      maxWidth: '400px',
      margin: '100px auto',
      padding: '40px',
      position: 'relative',
      zIndex: 1,
    },
    card: {
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      padding: '40px',
      borderRadius: '16px',
      border: '1px solid rgba(255, 20, 147, 0.3)',
      backdropFilter: 'blur(10px)',
    },
    logo: {
      fontSize: '3rem',
      fontWeight: '900',
      background: 'linear-gradient(135deg, #ff1493 0%, #ff69b4 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      textAlign: 'center',
      marginBottom: '10px',
      letterSpacing: '2px',
    },
    subtitle: {
      color: '#aaa',
      textAlign: 'center',
      marginBottom: '30px',
      fontSize: '14px',
    },
    form: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    },
    label: {
      color: '#aaa',
      fontSize: '14px',
      marginBottom: '5px',
    },
    input: {
      padding: '12px 16px',
      fontSize: '16px',
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      border: '2px solid rgba(255, 20, 147, 0.3)',
      borderRadius: '8px',
      color: '#fff',
      outline: 'none',
      transition: 'all 0.3s',
    },
    button: {
      padding: '14px',
      fontSize: '16px',
      backgroundColor: '#ff1493',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontWeight: 'bold',
      transition: 'all 0.3s',
      boxShadow: '0 0 20px rgba(255, 20, 147, 0.4)',
      marginTop: '10px',
    },
    error: {
      padding: '12px',
      backgroundColor: 'rgba(255, 20, 147, 0.1)',
      border: '1px solid #ff1493',
      borderRadius: '8px',
      color: '#ff69b4',
      fontSize: '14px',
    },
    demoInfo: {
      marginTop: '20px',
      padding: '15px',
      backgroundColor: 'rgba(255, 105, 180, 0.1)',
      border: '1px solid rgba(255, 105, 180, 0.3)',
      borderRadius: '8px',
      fontSize: '13px',
      color: '#ff69b4',
    },
    backLink: {
      marginTop: '20px',
      textAlign: 'center',
    },
    link: {
      color: '#ff69b4',
      textDecoration: 'none',
      fontSize: '14px',
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.logo}>LAPOMETRO</h1>
        <p style={styles.subtitle}>Inicia sesión para continuar</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@email.com"
              style={styles.input}
              required
              onFocus={(e) => {
                e.target.style.borderColor = '#ff1493';
                e.target.style.boxShadow = '0 0 20px rgba(255, 20, 147, 0.3)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'rgba(255, 20, 147, 0.3)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div>
            <label style={styles.label}>Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={styles.input}
              required
              onFocus={(e) => {
                e.target.style.borderColor = '#ff1493';
                e.target.style.boxShadow = '0 0 20px rgba(255, 20, 147, 0.3)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'rgba(255, 20, 147, 0.3)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          {error && (
            <div style={styles.error}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.button,
              opacity: loading ? 0.6 : 1,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.backgroundColor = '#ff69b4';
                e.target.style.boxShadow = '0 5px 30px rgba(255, 20, 147, 0.6)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.backgroundColor = '#ff1493';
                e.target.style.boxShadow = '0 0 20px rgba(255, 20, 147, 0.4)';
              }
            }}
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div style={styles.demoInfo}>
          <strong>Cuenta Demo:</strong>
          <br />
          Email: demo@lapometro.com
          <br />
          Contraseña: demo123
        </div>

        <div style={styles.backLink}>
          <a
            href="/"
            style={styles.link}
            onMouseEnter={(e) => e.target.style.color = '#ff1493'}
            onMouseLeave={(e) => e.target.style.color = '#ff69b4'}
          >
            ← Volver al inicio
          </a>
        </div>
      </div>
    </div>
  );
}
