'use client';

import { useState } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Home() {
  const { data: session } = useSession();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [uploadMode, setUploadMode] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await axios.get(`/api/ebay?query=${encodeURIComponent(query)}`);
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Error al buscar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);

    // Upload and analyze
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await axios.post('/api/analyze-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.query) {
        setQuery(response.data.query);
        // Automatically search with extracted text
        const searchResponse = await axios.get(`/api/ebay?query=${encodeURIComponent(response.data.query)}`);
        setData(searchResponse.data);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al analizar la imagen');
    } finally {
      setLoading(false);
    }
  };

  const styles = {
    container: {
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '20px',
      position: 'relative',
      zIndex: 1,
    },
    header: {
      textAlign: 'center',
      marginBottom: '50px',
      paddingTop: '40px',
    },
    logo: {
      fontSize: '4rem',
      fontWeight: '900',
      background: 'linear-gradient(135deg, #ff1493 0%, #ff69b4 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      marginBottom: '10px',
      letterSpacing: '2px',
      textShadow: '0 0 30px rgba(255, 20, 147, 0.5)',
    },
    subtitle: {
      color: '#aaa',
      fontSize: '1.1rem',
      marginBottom: '20px',
    },
    authSection: {
      textAlign: 'center',
      marginBottom: '30px',
    },
    authButton: {
      padding: '10px 24px',
      backgroundColor: '#ff1493',
      color: 'white',
      border: 'none',
      borderRadius: '25px',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: 'bold',
      transition: 'all 0.3s',
    },
    userInfo: {
      color: '#ff69b4',
      fontSize: '14px',
    },
    toggleSection: {
      display: 'flex',
      justifyContent: 'center',
      gap: '15px',
      marginBottom: '30px',
    },
    toggleButton: {
      padding: '12px 30px',
      backgroundColor: 'transparent',
      color: '#fff',
      border: '2px solid #ff1493',
      borderRadius: '25px',
      cursor: 'pointer',
      fontSize: '16px',
      fontWeight: 'bold',
      transition: 'all 0.3s',
    },
    toggleButtonActive: {
      backgroundColor: '#ff1493',
      boxShadow: '0 0 20px rgba(255, 20, 147, 0.6)',
    },
    searchForm: {
      marginBottom: '30px',
    },
    inputWrapper: {
      display: 'flex',
      gap: '10px',
      flexDirection: 'column',
    },
    input: {
      padding: '16px 20px',
      fontSize: '16px',
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      border: '2px solid rgba(255, 20, 147, 0.3)',
      borderRadius: '12px',
      color: '#fff',
      outline: 'none',
      transition: 'all 0.3s',
      backdropFilter: 'blur(10px)',
    },
    uploadContainer: {
      padding: '40px',
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      border: '2px dashed rgba(255, 20, 147, 0.5)',
      borderRadius: '12px',
      textAlign: 'center',
      cursor: 'pointer',
      transition: 'all 0.3s',
      backdropFilter: 'blur(10px)',
    },
    uploadInput: {
      display: 'none',
    },
    button: {
      padding: '16px 40px',
      fontSize: '16px',
      backgroundColor: '#ff1493',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      cursor: 'pointer',
      fontWeight: 'bold',
      transition: 'all 0.3s',
      boxShadow: '0 0 20px rgba(255, 20, 147, 0.4)',
    },
    buttonDisabled: {
      backgroundColor: '#666',
      cursor: 'not-allowed',
      boxShadow: 'none',
    },
    error: {
      padding: '16px',
      backgroundColor: 'rgba(255, 20, 147, 0.1)',
      border: '1px solid #ff1493',
      borderRadius: '12px',
      color: '#ff69b4',
      marginBottom: '20px',
      backdropFilter: 'blur(10px)',
    },
    statsCard: {
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      padding: '24px',
      borderRadius: '16px',
      marginBottom: '30px',
      border: '1px solid rgba(255, 20, 147, 0.2)',
      backdropFilter: 'blur(10px)',
    },
    statsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '20px',
    },
    statLabel: {
      fontSize: '14px',
      color: '#aaa',
      marginBottom: '5px',
    },
    statValue: {
      fontSize: '28px',
      fontWeight: 'bold',
      color: '#ff1493',
    },
    chartCard: {
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      padding: '24px',
      borderRadius: '16px',
      border: '1px solid rgba(255, 20, 147, 0.2)',
      marginBottom: '30px',
      backdropFilter: 'blur(10px)',
    },
    itemCard: {
      display: 'flex',
      gap: '16px',
      padding: '20px',
      backgroundColor: 'rgba(255, 255, 255, 0.03)',
      borderRadius: '12px',
      border: '1px solid rgba(255, 20, 147, 0.15)',
      transition: 'all 0.3s',
      backdropFilter: 'blur(10px)',
    },
    itemImage: {
      width: '100px',
      height: '100px',
      objectFit: 'cover',
      borderRadius: '8px',
      border: '2px solid rgba(255, 20, 147, 0.3)',
    },
    itemTitle: {
      margin: '0 0 8px 0',
      fontSize: '16px',
    },
    link: {
      color: '#ff69b4',
      textDecoration: 'none',
      transition: 'color 0.3s',
    },
    footer: {
      marginTop: '60px',
      paddingTop: '20px',
      borderTop: '1px solid rgba(255, 20, 147, 0.3)',
      textAlign: 'center',
      color: '#666',
    },
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.logo}>LAPOMETRO</h1>
        <p style={styles.subtitle}>Encuentra el valor real de cualquier reloj</p>
      </header>

      <div style={styles.authSection}>
        {session ? (
          <div>
            <p style={styles.userInfo}>Hola, {session.user.email}</p>
            <button
              style={{...styles.authButton, marginTop: '10px'}}
              onClick={() => signOut()}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#ff69b4'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#ff1493'}
            >
              Cerrar Sesión
            </button>
          </div>
        ) : (
          <button
            style={styles.authButton}
            onClick={() => signIn()}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#ff69b4'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#ff1493'}
          >
            Iniciar Sesión
          </button>
        )}
      </div>

      <div style={styles.toggleSection}>
        <button
          style={{
            ...styles.toggleButton,
            ...(uploadMode ? {} : styles.toggleButtonActive)
          }}
          onClick={() => setUploadMode(false)}
          onMouseEnter={(e) => {
            if (uploadMode) e.target.style.backgroundColor = 'rgba(255, 20, 147, 0.2)';
          }}
          onMouseLeave={(e) => {
            if (uploadMode) e.target.style.backgroundColor = 'transparent';
          }}
        >
          Buscar por Texto
        </button>
        <button
          style={{
            ...styles.toggleButton,
            ...(uploadMode ? styles.toggleButtonActive : {})
          }}
          onClick={() => setUploadMode(true)}
          onMouseEnter={(e) => {
            if (!uploadMode) e.target.style.backgroundColor = 'rgba(255, 20, 147, 0.2)';
          }}
          onMouseLeave={(e) => {
            if (!uploadMode) e.target.style.backgroundColor = 'transparent';
          }}
        >
          Subir Foto
        </button>
      </div>

      {!uploadMode ? (
        <form onSubmit={handleSearch} style={styles.searchForm}>
          <div style={styles.inputWrapper}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ej: Rolex Submariner, Omega Speedmaster..."
              style={styles.input}
              onFocus={(e) => {
                e.target.style.borderColor = '#ff1493';
                e.target.style.boxShadow = '0 0 20px rgba(255, 20, 147, 0.3)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'rgba(255, 20, 147, 0.3)';
                e.target.style.boxShadow = 'none';
              }}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                ...styles.button,
                ...(loading ? styles.buttonDisabled : {})
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.backgroundColor = '#ff69b4';
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 5px 30px rgba(255, 20, 147, 0.6)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.target.style.backgroundColor = '#ff1493';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 0 20px rgba(255, 20, 147, 0.4)';
                }
              }}
            >
              {loading ? 'Buscando...' : 'Buscar'}
            </button>
          </div>
        </form>
      ) : (
        <div>
          <label
            htmlFor="image-upload"
            style={styles.uploadContainer}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 20, 147, 0.1)';
              e.currentTarget.style.borderColor = '#ff1493';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.borderColor = 'rgba(255, 20, 147, 0.5)';
            }}
          >
            <input
              id="image-upload"
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={styles.uploadInput}
            />
            <div style={{ fontSize: '48px', marginBottom: '10px' }}>📸</div>
            <p style={{ color: '#ff69b4', fontSize: '18px', marginBottom: '5px' }}>
              Sube una foto de tu reloj
            </p>
            <p style={{ color: '#888', fontSize: '14px' }}>
              Analizaremos la imagen y buscaremos su valor
            </p>
            {imagePreview && (
              <img src={imagePreview} alt="Preview" style={{ maxWidth: '200px', marginTop: '20px', borderRadius: '8px' }} />
            )}
          </label>
        </div>
      )}

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

      {data && (
        <div>
          {data.summary.count === 0 ? (
            <div style={{ ...styles.statsCard, textAlign: 'center' }}>
              <p style={{ fontSize: '18px', color: '#888' }}>
                No se encontraron ventas para "{query}". Intenta con otra búsqueda.
              </p>
            </div>
          ) : (
            <>
              <div style={styles.statsCard}>
                <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#ff1493' }}>📊 Resumen de Mercado</h2>
                <div style={styles.statsGrid}>
                  <div>
                    <div style={styles.statLabel}>Precio Medio</div>
                    <div style={styles.statValue}>
                      ${data.summary.averagePrice.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={styles.statLabel}>Rango de Precio</div>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#fff' }}>
                      ${data.summary.minPrice.toFixed(2)} - ${data.summary.maxPrice.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={styles.statLabel}>Ventas Encontradas</div>
                    <div style={styles.statValue}>
                      {data.summary.count}
                    </div>
                  </div>
                  <div>
                    <div style={styles.statLabel}>Valor Estimado</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#ff69b4' }}>
                      ${data.summary.averagePrice.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>

              {data.chartData && data.chartData.length > 0 && (
                <div style={styles.chartCard}>
                  <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#ff1493' }}>📈 Evolución de Precios</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data.chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 20, 147, 0.2)" />
                      <XAxis dataKey="date" stroke="#aaa" />
                      <YAxis stroke="#aaa" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0, 0, 0, 0.9)',
                          border: '1px solid #ff1493',
                          borderRadius: '8px',
                          color: '#fff'
                        }}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="averagePrice" stroke="#ff1493" name="Precio Medio" strokeWidth={3} />
                      <Line type="monotone" dataKey="minPrice" stroke="#ff69b4" name="Precio Mínimo" strokeWidth={2} strokeDasharray="5 5" />
                      <Line type="monotone" dataKey="maxPrice" stroke="#c71585" name="Precio Máximo" strokeWidth={2} strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div style={styles.statsCard}>
                <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#ff1493' }}>🏷️ Ventas Recientes ({data.items.length})</h2>
                <div style={{ display: 'grid', gap: '16px' }}>
                  {data.items.map((item) => (
                    <div
                      key={item.id}
                      style={styles.itemCard}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 20, 147, 0.08)';
                        e.currentTarget.style.transform = 'translateX(5px)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
                        e.currentTarget.style.transform = 'translateX(0)';
                      }}
                    >
                      {item.image && (
                        <img
                          src={item.image}
                          alt={item.title}
                          style={styles.itemImage}
                        />
                      )}
                      <div style={{ flex: 1 }}>
                        <h3 style={styles.itemTitle}>
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={styles.link}
                            onMouseEnter={(e) => e.target.style.color = '#ff1493'}
                            onMouseLeave={(e) => e.target.style.color = '#ff69b4'}
                          >
                            {item.title}
                          </a>
                        </h3>
                        <div style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>
                          Condición: {item.condition}
                        </div>
                        <div style={{ fontSize: '14px', color: '#888', marginBottom: '8px' }}>
                          Vendido: {new Date(item.endTime).toLocaleDateString('es-ES')}
                        </div>
                        <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ff1493' }}>
                          {item.currency} ${item.price.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      <footer style={styles.footer}>
        <p>LAPOMETRO • Datos reales de eBay en tiempo real</p>
      </footer>
    </div>
  );
}
