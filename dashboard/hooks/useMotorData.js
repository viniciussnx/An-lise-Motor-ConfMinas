import { useState, useEffect, useCallback, useRef } from 'react';

const API = 'http://localhost:8000';
const POLL_MS = 4000;
const READINGS_LIMIT = 28;
/** Alinhado ao backend: sem leitura nova ≈ simulador/placa parados */
const LIVE_MS = 12000;

function readingsChanged(prev, next) {
  if (prev.length !== next.length) return true;
  if (!next.length) return false;
  return prev[prev.length - 1]?.id !== next[next.length - 1]?.id;
}

function statusChanged(prev, next) {
  if (!prev || !next) return true;
  return (
    prev.is_running !== next.is_running ||
    prev.overall_status !== next.overall_status ||
    prev.data_live !== next.data_live ||
    prev.last_reading?.timestamp !== next.last_reading?.timestamp
  );
}

function ordersChanged(prev, next) {
  if (prev.length !== next.length) return true;
  for (let i = 0; i < next.length; i++) {
    if (prev[i]?.id !== next[i]?.id || prev[i]?.status !== next[i]?.status) return true;
  }
  return false;
}

function isLiveStatus(status) {
  if (!status) return false;
  if (status.data_live === false) return false;
  if (status.data_live === true && status.last_reading) return true;
  const ts = status.last_reading?.timestamp;
  if (!ts) return false;
  const age = Date.now() - new Date(ts).getTime();
  return age >= 0 && age < LIVE_MS;
}

const EMPTY_STATUS = {
  is_running: false,
  nominal_current: 8,
  last_reading: null,
  overall_status: 'no_data',
  data_live: false,
  temp_status: 'no_data',
  vib_status: 'no_data',
  current_status: 'no_data',
  anomalies: [],
};

export default function useMotorData() {
  const [readings, setReadings] = useState([]);
  const [status, setStatus] = useState(null);
  const [orders, setOrders] = useState([]);
  const [online, setOnline] = useState(false);
  const [lastAt, setLastAt] = useState(null);
  const [hasLiveData, setHasLiveData] = useState(false);
  const busy = useRef(false);

  const fetch_ = useCallback(async (force = false) => {
    if (!force && busy.current) return;
    busy.current = true;
    try {
      const [r, s, o] = await Promise.all([
        fetch(`${API}/api/readings?limit=${READINGS_LIMIT}`).then((x) => x.json()),
        fetch(`${API}/api/status`).then((x) => x.json()),
        fetch(`${API}/api/service-orders`).then((x) => x.json()),
      ]);

      const live = isLiveStatus(s);
      setHasLiveData(live);
      setReadings(live ? r : []);
      setStatus((prev) => {
        const next = live ? s : { ...EMPTY_STATUS, nominal_current: s?.nominal_current ?? 8 };
        return statusChanged(prev, next) ? next : prev;
      });
      setOrders((prev) => (ordersChanged(prev, o) ? o : prev));
      setOnline(true);
      setLastAt(new Date());
    } catch {
      setOnline(false);
      setHasLiveData(false);
      setReadings([]);
      setStatus((prev) => (prev?.data_live === false ? prev : EMPTY_STATUS));
    } finally {
      busy.current = false;
    }
  }, []);

  useEffect(() => {
    fetch_();
    const t = setInterval(fetch_, POLL_MS);
    return () => clearInterval(t);
  }, [fetch_]);

  const refresh = useCallback(() => fetch_(true), [fetch_]);

  return { readings, status, orders, online, lastAt, refresh, hasLiveData };
}

export { API, LIVE_MS };
