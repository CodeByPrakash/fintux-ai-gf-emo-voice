import { useState, useEffect } from 'react';
import { apiFetch, apiDelete, apiPost } from '../utils/api';

export default function MemoryPage() {
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' | 'context' | 'vector'
  const [memories, setMemories] = useState([]);
  const [search, setSearch] = useState('');
  const [counts, setCounts] = useState({ count: 0, vector_count: 0, graph_node_count: 0 });

  // Graph state
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [newSource, setNewSource] = useState('Prixu');
  const [newRel, setNewRel] = useState('LIKES');
  const [newTarget, setNewTarget] = useState('');

  // Context state
  const [contextData, setContextData] = useState({
    recent_messages_count: 0,
    rolling_summary: '',
    user_profile: {},
    max_recent_messages: 14
  });

  const loadData = () => {
    // Counts
    apiFetch('/memories/count')
      .then(d => setCounts(d))
      .catch(() => { });

    // Graph
    apiFetch('/memories/graph')
      .then(d => setGraphData(d))
      .catch(() => { });

    // Context Window
    apiFetch('/chat/context')
      .then(d => setContextData(d))
      .catch(() => { });

    // Vector memories
    if (search.trim()) {
      apiFetch(`/memories/search?q=${encodeURIComponent(search)}&n=20`)
        .then(setMemories)
        .catch(() => { });
    } else {
      apiFetch('/memories?limit=50')
        .then(setMemories)
        .catch(() => { });
    }
  };

  useEffect(loadData, []);

  const handleSearch = (e) => {
    if (e.key === 'Enter') loadData();
  };

  const handleDeleteVector = async (id) => {
    await apiDelete(`/memories/${id}`);
    loadData();
  };

  const handleDeleteNode = async (nodeId) => {
    await apiDelete(`/memories/graph/node/${nodeId}`);
    loadData();
  };

  const handleAddEdge = async (e) => {
    e.preventDefault();
    if (!newTarget.trim()) return;
    await apiPost('/memories/graph/edge', {
      source: newSource.trim(),
      relation: newRel.trim(),
      target: newTarget.trim(),
      weight: 1.5,
      context: 'Added manually via Memory Bank'
    });
    setNewTarget('');
    loadData();
  };

  return (
    <div className="memory-page">
      <h1>MEMORY & KNOWLEDGE GRAPH</h1>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
        {counts.graph_node_count || 0} Knowledge Nodes • {graphData.edges?.length || 0} Relations • {counts.vector_count || 0} Vector Embeddings
      </div>

      {/* Tabs */}
      <div className="memory-tabs">
        <button
          className={`memory-tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          <span>🕸️</span> Knowledge Graph (Nodes & Relations)
        </button>
        <button
          className={`memory-tab-btn ${activeTab === 'context' ? 'active' : ''}`}
          onClick={() => setActiveTab('context')}
        >
          <span>📜</span> Context Window & Recaps
        </button>
        <button
          className={`memory-tab-btn ${activeTab === 'vector' ? 'active' : ''}`}
          onClick={() => setActiveTab('vector')}
        >
          <span>💾</span> Vector Memory Bank
        </button>
      </div>

      {/* TAB 1: KNOWLEDGE GRAPH */}
      {activeTab === 'graph' && (
        <div className="graph-container">
          {/* Quick Add Node Fact */}
          <form className="graph-form-card" onSubmit={handleAddEdge}>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', width: '100%', marginBottom: 4 }}>
              ➕ ADD KNOWLEDGE GRAPH RELATION:
            </div>
            <input
              className="graph-input"
              placeholder="Source (e.g. User)"
              value={newSource}
              onChange={e => setNewSource(e.target.value)}
            />
            <input
              className="graph-input"
              placeholder="Relation (e.g. LIKES, WORKING_ON)"
              value={newRel}
              onChange={e => setNewRel(e.target.value)}
            />
            <input
              className="graph-input"
              placeholder="Target Entity (e.g. Cyberpunk, Math Exam)"
              value={newTarget}
              onChange={e => setNewTarget(e.target.value)}
            />
            <button className="btn-primary" type="submit">CONNECT</button>
          </form>

          {/* Graph Nodes Grid */}
          <div>
            <h3 style={{ fontSize: 12, color: 'var(--neon-cyan)', letterSpacing: 1.5, marginBottom: 10 }}>
              ENTITY NODES ({graphData.nodes?.length || 0})
            </h3>
            <div className="graph-nodes-grid">
              {graphData.nodes?.map(node => (
                <div key={node.id} className="graph-node-card">
                  <div>
                    <div className="node-title">{node.label}</div>
                    <span className={`node-badge ${node.entity_type || 'ENTITY'}`}>
                      {node.entity_type || 'ENTITY'}
                    </span>
                  </div>
                  {node.id !== 'user' && node.id !== 'fenry' && (
                    <button
                      className="memory-delete"
                      onClick={() => handleDeleteNode(node.id)}
                      title="Delete Node"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              {(!graphData.nodes || graphData.nodes.length === 0) && (
                <div style={{ color: 'var(--text-dim)', fontSize: 13, gridColumn: '1 / -1' }}>
                  No knowledge graph nodes yet. FENRY will extract entities automatically as you chat!
                </div>
              )}
            </div>
          </div>

          {/* Connected Relations List */}
          <div style={{ marginTop: 12 }}>
            <h3 style={{ fontSize: 12, color: 'var(--neon-magenta)', letterSpacing: 1.5, marginBottom: 10 }}>
              SEMANTIC RELATION EDGES ({graphData.edges?.length || 0})
            </h3>
            <div className="graph-edges-list">
              {graphData.edges?.map(edge => (
                <div key={edge.id} className="graph-edge-item">
                  <div className="edge-visual">
                    <span className="edge-node-badge">{edge.source}</span>
                    <span className="edge-rel-tag">──[{edge.relation}]──►</span>
                    <span className="edge-node-badge">{edge.target}</span>
                    {edge.context && (
                      <span style={{ fontSize: 11, color: 'var(--text-dim)', marginLeft: 8 }}>
                        "{edge.context}"
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--neon-cyan)' }}>
                    wt: {edge.weight}
                  </span>
                </div>
              ))}
              {(!graphData.edges || graphData.edges.length === 0) && (
                <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>
                  No edges formed yet.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CONTEXT WINDOW & ROLLING RECAP */}
      {activeTab === 'context' && (
        <div className="context-panel">
          <div className="context-stat-box">
            <div className="context-title">🪟 ACTIVE CONTEXT WINDOW BUFFER</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
              FENRY keeps a sliding window of recent conversation turns in high-speed context, and continuously rolls older turns into structured summaries and knowledge nodes.
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ background: 'var(--bg-tertiary)', padding: '10px 16px', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Recent Active Turns</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--neon-cyan)' }}>
                  {contextData.recent_messages_count} / {contextData.max_recent_messages * 2}
                </div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '10px 16px', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Long-term Memory Mode</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--neon-green)' }}>
                  Rolling Summary + Graph Active
                </div>
              </div>
            </div>
          </div>

          <div className="context-stat-box">
            <div className="context-title">📜 ROLLING CONVERSATION RECAP</div>
            {contextData.rolling_summary ? (
              <div className="context-summary-text">
                {contextData.rolling_summary}
              </div>
            ) : (
              <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>
                No rolling compaction summary needed yet. As your conversation grows beyond the immediate window, FENRY will automatically summarize key milestones and context here!
              </div>
            )}
          </div>

          <div className="context-stat-box">
            <div className="context-title">👤 EXTRACTED USER PROFILE</div>
            {Object.keys(contextData.user_profile || {}).length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
                {Object.entries(contextData.user_profile).map(([k, v]) => (
                  <div key={k} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase' }}>{k}</div>
                    <div style={{ fontSize: 14, color: 'var(--text-primary)', marginTop: 4 }}>{v}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>
                No custom profile overrides set yet. FENRY dynamically learns your preferences through the Knowledge Graph!
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: VECTOR MEMORY BANK */}
      {activeTab === 'vector' && (
        <>
          <div style={{ display: 'flex', gap: 10 }}>
            <input
              className="memory-search"
              placeholder="Search vector embeddings..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              onKeyDown={handleSearch}
            />
            <button className="btn-primary" onClick={loadData} style={{ alignSelf: 'flex-start' }}>SEARCH</button>
          </div>
          <div className="memory-list">
            {memories.map(m => (
              <div key={m.id} className="memory-item">
                <div>
                  <div className="memory-content">{m.content}</div>
                  <div className="memory-tags">
                    {m.tags?.filter(Boolean).map((t, i) => <span key={i} className="memory-tag">{t}</span>)}
                  </div>
                </div>
                <button className="memory-delete" onClick={() => handleDeleteVector(m.id)} title="Delete">✕</button>
              </div>
            ))}
            {memories.length === 0 && (
              <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: 40 }}>
                No vector memories found. Start chatting to build FENRY's memory! 🧠
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
