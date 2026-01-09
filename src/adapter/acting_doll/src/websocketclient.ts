/**
 * WebSocket Client for bidirectional communication
 * ブラウザ環境でのWebSocket通信クライアント
 */

/**
 * WebSocketメッセージの基本型
 */
export interface WebSocketMessage {
  type: string;
  timestamp?: string;
  [key: string]: any;
}

/**
 * エコーメッセージ
 */
export interface EchoMessage extends WebSocketMessage {
  type: 'echo';
  text: string;
}

/**
 * ブロードキャストメッセージ
 */
export interface BroadcastMessage extends WebSocketMessage {
  type: 'broadcast';
  content: string;
}

/**
 * コマンドメッセージ
 */
export interface CommandMessage extends WebSocketMessage {
  type: 'command';
  command: string;
}

/**
 * ウェルカムレスポンス
 */
export interface WelcomeResponse extends WebSocketMessage {
  type: 'welcome';
  message: string;
  client_id: string;
}

/**
 * エコーレスポンス
 */
export interface EchoResponse extends WebSocketMessage {
  type: 'echo_response';
  original: any;
}

/**
 * ブロードキャストレスポンス
 */
export interface BroadcastResponse extends WebSocketMessage {
  type: 'broadcast_message';
  from: string;
  content: string;
}

/**
 * クライアント接続通知
 */
export interface ClientConnectedMessage extends WebSocketMessage {
  type: 'client_connected';
  client_id: string;
  total_clients: number;
}

/**
 * クライアント切断通知
 */
export interface ClientDisconnectedMessage extends WebSocketMessage {
  type: 'client_disconnected';
  client_id: string;
  total_clients: number;
}

/**
 * コマンドレスポンス
 */
export interface CommandResponse extends WebSocketMessage {
  type: 'command_response';
  command: string;
  data?: any;
  error?: string;
}

/**
 * エラーメッセージ
 */
export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  message: string;
}

/**
 * メッセージハンドラの型
 */
export type MessageHandler = (data: WebSocketMessage) => void;

/**
 * WebSocketクライアントクラス
 */
export class WebSocketClient {
  private uri: string;
  private websocket: WebSocket | null = null;
  private running: boolean = false;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 0; // 0で無制限
  private reconnectDelay: number = 3000;

  /**
   * コンストラクタ
   * @param uri WebSocketサーバーのURI（デフォルト: ws://localhost:8765）
   */
  constructor(uri: string = 'ws://localhost:8765') {
    this.uri = uri;
  }

  /**
   * サーバーに接続
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log(`サーバーに接続中: ${this.uri}`);

      this.websocket = new WebSocket(this.uri);

      this.websocket.onopen = () => {
        console.log('WebSocketサーバーに接続しました');
        this.running = true;
        this.reconnectAttempts = 0;
        resolve();
      };

      this.websocket.onclose = (event) => {
        console.log('WebSocket接続が閉じられました', event);
        this.running = false;
        this.handleReconnect();
      };

      this.websocket.onerror = (error) => {
        console.error('WebSocketエラー:', error);
        reject(error);
      };

      this.websocket.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          console.log('受信:', data);
          this.handleMessage(data);
        } catch (error) {
          console.error('不正なJSON形式:', event.data, error);
        }
      };
    });
  }

  /**
   * サーバーから切断
   */
  public disconnect(): void {
    if (this.websocket) {
      this.running = false;
      this.websocket.close();
      this.websocket = null;
      console.log('WebSocketサーバーから切断しました');
    }
  }

  /**
   * 再接続を試みる
   */
  private handleReconnect(): void {
    if ((this.reconnectAttempts < this.maxReconnectAttempts) || (0 === this.maxReconnectAttempts)) {
      this.reconnectAttempts++;
      console.log(
        `再接続を試みます... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );

      setTimeout(() => {
        this.connect().catch((error) => {
          console.error('再接続に失敗しました:', error);
        });
      }, this.reconnectDelay);
    } else {
      console.error('最大再接続試行回数に達しました');
    }
  }

  /**
   * メッセージを送信
   * @param message 送信するメッセージ
   */
  public sendMessage(message: WebSocketMessage): void {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      const messageJson = JSON.stringify({
        ...message,
        timestamp: new Date().toISOString()
      });
      this.websocket.send(messageJson);
      console.log('送信:', message);
    } else {
      console.error('WebSocket接続が開いていません');
    }
  }

  /**
   * エコーメッセージを送信
   * @param text エコーするテキスト
   */
  public sendEcho(text: string): void {
    this.sendMessage({
      type: 'echo',
      text: text
    });
  }

  /**
   * ブロードキャストメッセージを送信
   * @param content ブロードキャストする内容
   */
  public sendBroadcast(content: string): void {
    this.sendMessage({
      type: 'broadcast',
      content: content
    });
  }

  /**
   * コマンドを送信
   * @param command コマンド文字列
   */
  public sendCommand(command: string): void {
    this.sendMessage({
      type: 'command',
      command: command
    });
  }

  /**
   * カスタムメッセージを送信
   * @param type メッセージタイプ
   * @param data メッセージデータ
   */
  public sendCustomMessage(type: string, data: any): void {
    this.sendMessage({
      type: type,
      ...data
    });
  }

  /**
   * 受信したメッセージを処理
   * @param data 受信したメッセージ
   */
  private handleMessage(data: WebSocketMessage): void {
    const msgType = data.type || 'unknown';

    // タイプ別のハンドラを実行
    const handlers = this.messageHandlers.get(msgType);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }

    // 全メッセージハンドラを実行
    const allHandlers = this.messageHandlers.get('*');
    if (allHandlers) {
      allHandlers.forEach((handler) => handler(data));
    }

    // デフォルトのログ出力
    this.logMessage(data);
  }

  /**
   * メッセージのログ出力
   * @param data メッセージデータ
   */
  private logMessage(data: WebSocketMessage): void {
    const msgType = data.type || 'unknown';

    switch (msgType) {
      case 'welcome':
        console.log(`ウェルカムメッセージ: ${(data as WelcomeResponse).message}`);
        break;
      case 'echo_response':
        console.log(`エコー応答:`, (data as EchoResponse).original);
        break;
      case 'broadcast_message':
        const broadcast = data as BroadcastResponse;
        console.log(`ブロードキャスト from ${broadcast.from}: ${broadcast.content}`);
        break;
      case 'client_connected':
        const connected = data as ClientConnectedMessage;
        console.log(
          `新しいクライアントが接続しました (合計: ${connected.total_clients})`
        );
        break;
      case 'client_disconnected':
        const disconnected = data as ClientDisconnectedMessage;
        console.log(
          `クライアントが切断しました (合計: ${disconnected.total_clients})`
        );
        break;
      case 'command_response':
        console.log(`コマンド応答:`, data);
        break;
      case 'error':
        console.error(`エラー: ${(data as ErrorMessage).message}`);
        break;
      default:
        console.log(`未処理のメッセージタイプ: ${msgType}`, data);
    }
  }

  /**
   * メッセージハンドラを登録
   * @param type メッセージタイプ（'*'で全メッセージ）
   * @param handler メッセージハンドラ関数
   */
  public onMessage(type: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  /**
   * メッセージハンドラを削除
   * @param type メッセージタイプ
   * @param handler メッセージハンドラ関数
   */
  public offMessage(type: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * 接続状態を取得
   */
  public isConnected(): boolean {
    return this.websocket !== null && this.websocket.readyState === WebSocket.OPEN;
  }

  /**
   * 実行状態を取得
   */
  public isRunning(): boolean {
    return this.running;
  }
}
