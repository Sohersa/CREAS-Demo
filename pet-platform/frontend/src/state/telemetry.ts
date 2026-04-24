import { useEffect } from "react";
import { proxy, useSnapshot } from "valtio";

export const telemetry = proxy<{ values: Record<string, number>; connected: boolean }>({
  values: {},
  connected: false,
});

/** Single WebSocket shared across the app — connects once, fans out via valtio. */
let ws: WebSocket | null = null;

export function useTelemetry() {
  useEffect(() => {
    if (ws) return;
    const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/v1/telemetry/stream`;
    ws = new WebSocket(url);
    ws.onopen = () => { telemetry.connected = true; };
    ws.onclose = () => { telemetry.connected = false; ws = null; };
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        telemetry.values[msg.tag] = msg.v;
      } catch { /* ignore malformed */ }
    };
    return () => { ws?.close(); ws = null; };
  }, []);
}

export function useTelemetryValue(tag: string): number | undefined {
  const snap = useSnapshot(telemetry);
  return snap.values[tag];
}
