/**
 * HealthGuard AI — Server-Sent Events Hook
 * Replaces polling with push-based real-time updates from the backend.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { SSE_URL } from '../config';

export function useSSE() {
  const [metrics, setMetrics] = useState([]);
  const [latestMetric, setLatestMetric] = useState(null);
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef(null);

  const connect = useCallback(() => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(SSE_URL);
    eventSourceRef.current = es;

    es.onopen = () => {
      setConnected(true);
    };

    es.onerror = () => {
      setConnected(false);
      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        if (eventSourceRef.current === es) {
          connect();
        }
      }, 3000);
    };

    // Handle metric updates
    es.addEventListener('metrics', (e) => {
      try {
        const data = JSON.parse(e.data);
        setLatestMetric(data);
        setMetrics(prev => {
          const updated = [...prev, { ...data, time: data.time || new Date().toLocaleTimeString() }];
          if (updated.length > 50) updated.shift();
          return updated;
        });
      } catch (err) {
        console.error('Failed to parse metrics:', err);
      }
    });

    // Handle agent events
    const agentEvents = ['anomaly_detected', 'diagnosis_complete', 'fix_applied', 'incident_resolved', 'system_started', 'system_stopped', 'error'];
    agentEvents.forEach(eventType => {
      es.addEventListener(eventType, (e) => {
        try {
          const data = JSON.parse(e.data);
          setEvents(prev => {
            const updated = [...prev, { type: eventType, data, timestamp: new Date().toLocaleTimeString() }];
            if (updated.length > 50) updated.shift();
            return updated;
          });
        } catch (err) {
          console.error(`Failed to parse ${eventType}:`, err);
        }
      });
    });

    return es;
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    metrics,
    latestMetric,
    events,
    connected,
    connect,
    disconnect,
    clearMetrics: () => setMetrics([]),
  };
}
