import React, { useState, useEffect, useRef } from 'react';
import { Search, Activity, Download, Construction } from 'lucide-react';
import './index.css';

function App() {
  // Form State
  const [activeTab, setActiveTab] = useState('gmap');
  const [keyword, setKeyword] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [filterNoPhone, setFilterNoPhone] = useState(false);
  const [filterHasWebsite, setFilterHasWebsite] = useState(false);
  const [filterNoReview, setFilterNoReview] = useState(false);
  const [filterLowRating, setFilterLowRating] = useState(false);

  // App State
  const [logs, setLogs] = useState([]);
  const [records, setRecords] = useState([]);
  const [scraping, setScraping] = useState(false);
  const wsRef = useRef(null);
  const consoleEndRef = useRef(null);

  useEffect(() => {
    // Auto-scroll console
    if (consoleEndRef.current && scraping) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, scraping]);

  const downloadCSV = () => {
    if (records.length === 0) return;

    // Create headers
    const headers = Object.keys(records[0]).join(',');

    // Create rows
    const rows = records.map(record => {
      return Object.values(record).map(value => {
        // Escape quotes and wrap in quotes if contains comma
        const strValue = String(value || '');
        if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
          return `"${strValue.replace(/"/g, '""')}"`;
        }
        return strValue;
      }).join(',');
    });

    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `scrapiky_${keyword.replace(/\s+/g, '_')}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const startScraping = (e) => {
    e.preventDefault();
    if (!keyword) return;

    setScraping(true);
    setRecords([]);
    setLogs(["> Initializing connection..."]);

    const wsUrl = `ws://localhost:8000/ws/scrape`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setLogs((prev) => [...prev, "> Connected to server. Sending request..."]);
      ws.send(JSON.stringify({
        keyword,
        max_results: Math.min(parseInt(maxResults, 10) || 10, 10),
        filter_no_phone: filterNoPhone,
        filter_has_website: filterHasWebsite,
        filter_no_review: filterNoReview,
        filter_low_rating: filterLowRating
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'log') {
        const cleanMsg = message.data.replace(/\u001b\[\d+;\d+m|\u001b\[\d+m/g, '');
        setLogs((prev) => [...prev, cleanMsg]);
      } else if (message.type === 'result') {
        setRecords(message.data);
      } else if (message.type === 'status' || message.type === 'error') {
        setLogs((prev) => [...prev, `[${message.type.toUpperCase()}] ${message.data}`]);
        if (message.type === 'error' || message.data.includes("completed")) {
          setScraping(false);
        }
      }
    };

    ws.onclose = () => {
      setScraping(false);
      setLogs((prev) => [...prev, "> Connection closed."]);
    };

    ws.onerror = (error) => {
      console.error("WebSocket Error:", error);
      setScraping(false);
      setLogs((prev) => [...prev, "[ERROR] WebSocket connection failed."]);
    };
  };

  return (
    <div className="app-container">
      <nav className="nav-bar">
        <div className="logo" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Scrapiky
          <span style={{ fontSize: '0.75rem', backgroundColor: '#e5e7eb', padding: '0.1rem 0.5rem', borderRadius: '1rem', color: '#6b7280', fontWeight: 'bold' }}>BETA</span>
        </div>
      </nav>

      <div className="dashboard-grid">
        {/* LEFT COLUMN - SPAN 5 */}
        <div className="left-panel">
          <div className="dashboard-card" style={{ flex: 1, marginBottom: 0 }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Configuration</h2>

            <div className="tabs-container">
              <button
                type="button"
                className={`tab-btn ${activeTab === 'gmap' ? 'active' : ''}`}
                onClick={() => setActiveTab('gmap')}
              >
                GMap
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'twitter' ? 'active' : ''}`}
                onClick={() => setActiveTab('twitter')}
              >
                Twitter
              </button>
            </div>

            {activeTab === 'twitter' ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
                <Construction size={48} style={{ marginBottom: '1rem', color: '#9ca3af' }} />
                <h3>Under Development</h3>
                <p style={{ fontSize: '0.875rem' }}>This feature is coming soon.</p>
              </div>
            ) : (
              <form onSubmit={startScraping}>
                <div className="form-group">
                  <label>Keyword Search</label>
                  <input
                    type="text"
                    className="input-text"
                    placeholder="e.g. Cafe in Jakarta"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    disabled={scraping}
                    required
                  />
                </div>

                <div className="form-group" style={{ marginTop: "1rem" }}>
                  <label>Max Results</label>
                  <input 
                    type="number" 
                    className="input-text" 
                    placeholder="e.g. 10" 
                    value={maxResults}
                    onChange={(e) => {
                      let val = e.target.value;
                      if (val !== '') {
                        let num = parseInt(val, 10);
                        if (num > 10) val = '10';
                      }
                      setMaxResults(val);
                    }}
                    disabled={scraping}
                    min="1"
                    max="10"
                    required
                  />
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.25rem", fontStyle: "italic" }}>
                    Currently in beta test, only can proceed 10 data only per user
                  </p>
                </div>

                <div className="form-group" style={{ marginTop: "1rem" }}>
                  <label>Skip if:</label>
                  <div className="checkbox-group" style={{ marginLeft: "1rem", marginTop: "0.5rem" }}>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={filterNoPhone}
                        onChange={(e) => setFilterNoPhone(e.target.checked)}
                        disabled={scraping}
                      />
                      &nbsp;&nbsp;no phone
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={filterHasWebsite}
                        onChange={(e) => setFilterHasWebsite(e.target.checked)}
                        disabled={scraping}
                      />
                      &nbsp;&nbsp;no website
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={filterNoReview}
                        onChange={(e) => setFilterNoReview(e.target.checked)}
                        disabled={scraping}
                      />
                      &nbsp;&nbsp;no review
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={filterLowRating}
                        onChange={(e) => setFilterLowRating(e.target.checked)}
                        disabled={scraping}
                      />
                      &nbsp;&nbsp;ratings &lt; 3
                    </label>
                  </div>
                </div>

                <button type="submit" className="btn-primary" style={{ width: "100%", marginTop: "2rem" }} disabled={scraping}>
                  {scraping ? <Activity size={20} className="animate-spin" /> : <Search size={20} />}
                  {scraping ? 'Harvesting in Progress...' : 'Start Harvesting'}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN - SPAN 7 */}
        <div className="right-panel">
          {!scraping && records.length > 0 ? (
            <div className="results-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div className="console-header" style={{ marginBottom: '1rem' }}>
                <h3>Harvest Results ({records.length})</h3>
                <button onClick={downloadCSV} className="btn-outline" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'white' }}>
                  <Download size={16} /> Download CSV
                </button>
              </div>

              <div className="table-container">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th style={{ position: 'sticky', top: 0, zIndex: 10 }}>Name</th>
                      <th style={{ position: 'sticky', top: 0, zIndex: 10 }}>Rating</th>
                      <th style={{ position: 'sticky', top: 0, zIndex: 10 }}>Reviews</th>
                      <th style={{ position: 'sticky', top: 0, zIndex: 10 }}>Category</th>
                      <th style={{ position: 'sticky', top: 0, zIndex: 10 }}>Phone</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((r, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 500 }}>{r.name}</td>
                        <td>{r.rating || '-'}</td>
                        <td>{r.review_count || '-'}</td>
                        <td>{r.category || '-'}</td>
                        <td>{r.phone || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div className="console-header" style={{ marginBottom: '1rem' }}>
                <h3>Process Log</h3>
                {scraping && <span style={{ color: "#1a56db", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.5rem" }}><Activity size={14} className="animate-spin" /> Running</span>}
              </div>
              <div className="console-container">
                {logs.length === 0 ? (
                  <div style={{ color: "#6b7280", fontStyle: "italic" }}>Waiting to start...</div>
                ) : (
                  logs.map((log, index) => (
                    <div key={index} className="console-line">{log}</div>
                  ))
                )}
                <div ref={consoleEndRef} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
