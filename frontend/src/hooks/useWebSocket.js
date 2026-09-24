import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../utils/api';

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(false);
  const [affect, setAffect] = useState({ mood: 0.7, energy: 0.8, attachment: 0.5 });
  const [thinkingSteps, setThinkingSteps] = useState([]);
  const wsRef = useRef(null);
  const currentResponseRef = useRef('');

  // Load persistent chat history from context window store
  useEffect(() => {
    fetch('/api/chat/history?limit=30')
      .then(res => res.json())
      .then(data => {
        if (data?.messages && Array.isArray(data.messages)) {
          const loaded = data.messages.map(m => ({
            role: m.role,
            content: m.content,
            time: new Date(m.timestamp),
            streaming: false
          }));
          setMessages(loaded);
        }
      })
      .catch(() => { });
  }, []);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000); };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'message_chunk') {
            currentResponseRef.current += msg.data.content;
            setMessages(prev => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              if (last && (last.role === 'fenry' || last.role === 'fenry') && last.streaming) {
                copy[copy.length - 1] = { ...last, content: currentResponseRef.current };
              } else {
                copy.push({ role: 'fenry', content: currentResponseRef.current, streaming: true, time: new Date() });
              }
              return copy;
            });
          } else if (msg.type === 'message_complete') {
            currentResponseRef.current = '';
            setMessages(prev => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              if (last && (last.role === 'fenry' || last.role === 'fenry') && last.streaming) {
                copy[copy.length - 1] = {
                  ...last,
                  content: msg.data.content,
                  streaming: false,
                  isProactive: msg.data?.is_proactive
                };
                return copy;
              } else {
                return [...copy, {
                  role: 'fenry',
                  content: msg.data.content,
                  streaming: false,
                  time: new Date(),
                  isProactive: msg.data?.is_proactive
                }];
              }
            });
          } else if (msg.type === 'typing') { setTyping(msg.data.active); }
          else if (msg.type === 'affect') { setAffect(msg.data); }
          else if (msg.type === 'thinking') {
            setThinkingSteps(prev => {
              const idx = prev.findIndex(s => s.step === msg.data.step);
              if (idx >= 0) { const c = [...prev]; c[idx] = msg.data; return c; }
              return [...prev, msg.data];
            });
            if (msg.data.step === 'memorize' && msg.data.status === 'done') setTimeout(() => setThinkingSteps([]), 2000);
          }
        } catch (e) { console.error('WS parse:', e); }
      };
      wsRef.current = ws;
    };
    connect();
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, []);

  const sendMessage = useCallback((content) => {
    if (wsRef.current?.readyState === WebSocket.OPEN && content.trim()) {
      setMessages(prev => [...prev, { role: 'user', content, time: new Date() }]);
      wsRef.current.send(JSON.stringify({ content }));
    }
  }, []);

  const triggerProactive = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'trigger_proactive' }));
    }
  }, []);

  return { connected, messages, typing, affect, thinkingSteps, sendMessage, triggerProactive };
}
