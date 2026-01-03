'use client';

import { useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

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

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <header style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '10px' }}>⌚ Valorador de Relojes</h1>
        <p style={{ color: '#666' }}>Encuentra el valor de mercado de relojes usados basado en ventas reales de eBay</p>
      </header>

      <form onSubmit={handleSearch} style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ej: Rolex Submariner, Omega Speedmaster, Seiko SKX007..."
            style={{
              flex: 1,
              padding: '12px 16px',
              fontSize: '16px',
              border: '2px solid #ddd',
              borderRadius: '8px',
              outline: 'none',
            }}
            onFocus={(e) => e.target.style.borderColor = '#0070f3'}
            onBlur={(e) => e.target.style.borderColor = '#ddd'}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '12px 32px',
              fontSize: '16px',
              backgroundColor: loading ? '#ccc' : '#0070f3',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
            }}
          >
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
      </form>

      {error && (
        <div style={{
          padding: '16px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '8px',
          color: '#c33',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {data && (
        <div>
          {data.summary.count === 0 ? (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              backgroundColor: '#f5f5f5',
              borderRadius: '8px',
            }}>
              <p style={{ fontSize: '18px', color: '#666' }}>
                No se encontraron ventas para "{query}". Intenta con otra búsqueda.
              </p>
            </div>
          ) : (
            <>
              <div style={{
                backgroundColor: '#f9f9f9',
                padding: '24px',
                borderRadius: '8px',
                marginBottom: '30px'
              }}>
                <h2 style={{ marginTop: 0, marginBottom: '20px' }}>📊 Resumen de Mercado</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                  <div>
                    <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Precio Medio</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#0070f3' }}>
                      {data.summary.currency} ${data.summary.averagePrice.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Rango de Precio</div>
                    <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                      ${data.summary.minPrice.toFixed(2)} - ${data.summary.maxPrice.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Ventas Encontradas</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                      {data.summary.count}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Valor Estimado</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#10b981' }}>
                      ${data.summary.averagePrice.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>

              {data.chartData && data.chartData.length > 0 && (
                <div style={{
                  backgroundColor: 'white',
                  padding: '24px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  marginBottom: '30px'
                }}>
                  <h2 style={{ marginTop: 0, marginBottom: '20px' }}>📈 Evolución de Precios</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data.chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="averagePrice" stroke="#0070f3" name="Precio Medio" strokeWidth={2} />
                      <Line type="monotone" dataKey="minPrice" stroke="#10b981" name="Precio Mínimo" strokeWidth={1} strokeDasharray="5 5" />
                      <Line type="monotone" dataKey="maxPrice" stroke="#ef4444" name="Precio Máximo" strokeWidth={1} strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div style={{
                backgroundColor: 'white',
                padding: '24px',
                borderRadius: '8px',
                border: '1px solid #ddd'
              }}>
                <h2 style={{ marginTop: 0, marginBottom: '20px' }}>🏷️ Ventas Recientes ({data.items.length})</h2>
                <div style={{ display: 'grid', gap: '16px' }}>
                  {data.items.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        display: 'flex',
                        gap: '16px',
                        padding: '16px',
                        backgroundColor: '#f9f9f9',
                        borderRadius: '8px',
                        border: '1px solid #eee'
                      }}
                    >
                      {item.image && (
                        <img
                          src={item.image}
                          alt={item.title}
                          style={{
                            width: '100px',
                            height: '100px',
                            objectFit: 'cover',
                            borderRadius: '4px'
                          }}
                        />
                      )}
                      <div style={{ flex: 1 }}>
                        <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>
                          <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: '#0070f3', textDecoration: 'none' }}>
                            {item.title}
                          </a>
                        </h3>
                        <div style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>
                          Condición: {item.condition}
                        </div>
                        <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px' }}>
                          Vendido: {new Date(item.endTime).toLocaleDateString('es-ES')}
                        </div>
                        <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#0070f3' }}>
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

      <footer style={{ marginTop: '60px', paddingTop: '20px', borderTop: '1px solid #ddd', textAlign: 'center', color: '#666' }}>
        <p>Datos obtenidos de ventas reales en eBay • Precios actualizados en tiempo real</p>
      </footer>
    </div>
  );
}
