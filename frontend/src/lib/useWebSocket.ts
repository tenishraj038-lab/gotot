"use client";

import { useEffect, useRef, useCallback } from "react";

type ProgressCallback = (data: { status: string; progress: number; message: string }) => void;

export function useWebSocket(taskId: string | null, onProgress: ProgressCallback) {
  const ws = useRef<WebSocket | null>(null);
  const onProgressRef = useRef(onProgress);
  onProgressRef.current = onProgress;

  const connect = useCallback(() => {
    if (!taskId) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.host}`;
    const url = `${host}/ws/progress/${taskId}`;

    try {
      const socket = new WebSocket(url);
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onProgressRef.current(data);
        } catch {}
      };
      socket.onclose = () => {
        ws.current = null;
      };
      socket.onerror = () => {
        ws.current = null;
      };
      ws.current = socket;
    } catch {}
  }, [taskId]);

  useEffect(() => {
    connect();
    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [connect]);

  return ws;
}
