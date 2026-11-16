/**
 * MediSync AI — WebSocket Client
 * Subscribes to real-time queue updates for a given poli.
 */

import type { Queue } from "@/types";

type QueueUpdateHandler = (update: Queue) => void;
type ConnectionHandler = () => void;

export class QueueWebSocket {
  private ws: WebSocket | null = null;
  private readonly poliName: string;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;

  onUpdate: QueueUpdateHandler | null = null;
  onConnect: ConnectionHandler | null = null;
  onDisconnect: ConnectionHandler | null = null;

  constructor(poliName: string) {
    this.poliName = encodeURIComponent(poliName);
  }

  /** Open the WebSocket connection. */
  connect(): void {
    const wsBase =
      process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
    const url = `${wsBase}/api/queue/ws/${this.poliName}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.onConnect?.();
      // Send a heartbeat ping every 25 s to keep the connection alive
      this.pingInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send("ping");
        }
      }, 25_000);
    };

    this.ws.onmessage = (event: MessageEvent<string>) => {
      if (event.data === "pong") return;
      try {
        const payload = JSON.parse(event.data) as Queue;
        this.onUpdate?.(payload);
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this.cleanup();
      this.onDisconnect?.();
      if (this.shouldReconnect) {
        // Exponential back-off reconnect (5 s)
        this.reconnectTimeout = setTimeout(() => this.connect(), 5_000);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  /** Close the connection permanently. */
  disconnect(): void {
    this.shouldReconnect = false;
    this.cleanup();
    this.ws?.close();
  }

  private cleanup(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }
}
