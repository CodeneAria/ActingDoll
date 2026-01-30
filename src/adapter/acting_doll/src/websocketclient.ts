/**
 * WebSocket Client for bidirectional communication
 * ブラウザ環境でのWebSocket通信クライアント
 */

import {
  CubismLogVerbose,
  CubismLogError,
  CubismLogInfo
} from '@framework/utils/cubismdebug';
import { LAppMultilingual, MessageKey } from './lappmultilingual';

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
 * 目パチ設定メッセージ
 */
export interface SetEyeBlinkMessage extends WebSocketMessage {
  type: 'set_eye_blink';
  enabled: boolean;
  client_id: string;
}

/**
 * 呼吸設定メッセージ
 */
export interface SetBreathMessage extends WebSocketMessage {
  type: 'set_breath';
  enabled: boolean;
  client_id: string;
}

/**
 * アイドリングモーション設定メッセージ
 */
export interface SetIdleMotionMessage extends WebSocketMessage {
  type: 'set_idle_motion';
  enabled: boolean;
  client_id: string;
}

/**
 * ドラッグ追従設定メッセージ
 */
export interface SetDragFollowMessage extends WebSocketMessage {
  type: 'set_drag_follow';
  enabled: boolean;
  client_id: string;
}

/**
 * 物理演算設定メッセージ
 */
export interface SetPhysicsMessage extends WebSocketMessage {
  type: 'set_physics';
  enabled: boolean;
  client_id: string;
}

/**
 * 表情設定メッセージ
 */
export interface SetExpressionMessage extends WebSocketMessage {
  type: 'set_expression';
  expression: string;
  client_id: string;
}

/**
 * モーション設定メッセージ
 */
export interface SetMotionMessage extends WebSocketMessage {
  type: 'set_motion';
  group: string;
  no?: number;
  priority?: number;
  client_id: string;
}

/**
 * パラメータ設定メッセージ
 */
export interface SetParameterMessage extends WebSocketMessage {
  type: 'set_parameter';
  name: string;
  value: number;
  client_id: string;
}

/**
 * モデル情報リクエストメッセージ
 */
export interface RequestModelInfoMessage extends WebSocketMessage {
  type: 'request_model_info';
}

/**
 * 目パチ情報リクエストメッセージ
 */
export interface RequestEyeBlinkMessage extends WebSocketMessage {
  type: 'request_eye_blink';
}

/**
 * 呼吸情報リクエストメッセージ
 */
export interface RequestBreathMessage extends WebSocketMessage {
  type: 'request_breath';
}

/**
 * アイドリングモーション情報リクエストメッセージ
 */
export interface RequestIdleMotionMessage extends WebSocketMessage {
  type: 'request_idle_motion';
}

/**
 * ドラッグ追従情報リクエストメッセージ
 */
export interface RequestDragFollowMessage extends WebSocketMessage {
  type: 'request_drag_follow';
}

/**
 * 表情情報リクエストメッセージ
 */
export interface RequestExpressionMessage extends WebSocketMessage {
  type: 'request_expression';
}

/**
 * モーション情報リクエストメッセージ
 */
export interface RequestMotionMessage extends WebSocketMessage {
  type: 'request_motion';
}

/**
 * クライアントレスポンスメッセージ
 */
export interface ClientResponseMessage extends WebSocketMessage {
  type: 'client';
  command: string;
  args: any;
}

/**
 * Wavファイル送信メッセージ
 */
export interface SetLipSyncMessage extends WebSocketMessage {
  type: 'set_lipsync';
  wav_data: string; // base64エンコードされたWavデータ
  client_id: string;
}

/**
 * 位置情報リクエストメッセージ
 */
export interface RequestPositionMessage extends WebSocketMessage {
  type: 'request_position';
}

/**
 * 位置設定メッセージ
 */
export interface SetPositionMessage extends WebSocketMessage {
  type: 'set_position';
  x: number;
  y: number;
  relative: boolean;
  client_id: string;
}

/**
 * スケール情報リクエストメッセージ
 */
export interface RequestScaleMessage extends WebSocketMessage {
  type: 'request_scale';
}

/**
 * スケール設定メッセージ
 */
export interface SetScaleMessage extends WebSocketMessage {
  type: 'set_scale';
  scale: number;
  client_id: string;
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
  private clientId: string | null = null;

  /**
   * コンストラクタ
   * @param uri WebSocketサーバーのURI
   */
  constructor(uri: string) {
    this.uri = uri;
  }

  /**
   * サーバーに接続
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CONNECTING, this.uri));

      this.websocket = new WebSocket(this.uri);

      this.websocket.onopen = () => {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CONNECTED));
        this.running = true;
        this.reconnectAttempts = 0;
        resolve();
      };

      this.websocket.onclose = (event) => {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CLOSED, event));
        this.running = false;
        this.handleReconnect();
      };

      this.websocket.onerror = (error) => {
        CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_ERROR, error.toString()));
        reject(error);
      };

      this.websocket.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          CubismLogVerbose(LAppMultilingual.getMessage(MessageKey.WS_RECEIVED, JSON.stringify(data)));
          this.handleMessage(data);
        } catch (error) {
          CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_INVALID_JSON, event.data, error.toString()));
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
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_DISCONNECTED));
    }
  }

  /**
   * 再接続を試みる
   */
  private handleReconnect(): void {
    if ((this.reconnectAttempts < this.maxReconnectAttempts) || (0 === this.maxReconnectAttempts)) {
      this.reconnectAttempts++;
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_RECONNECTING, this.reconnectAttempts.toString(), this.maxReconnectAttempts.toString()));

      setTimeout(() => {
        this.connect().catch((error) => {
          CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_RECONNECT_FAILED, error.toString()));
        });
      }, this.reconnectDelay);
    } else {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_MAX_RECONNECT_REACHED));
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
      CubismLogVerbose(LAppMultilingual.getMessage(MessageKey.WS_SENDING, messageJson));
    } else {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_NOT_CONNECTED));
    }
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
    // CubismLogVerbose(LAppMultilingual.getMessage(MessageKey.WS_HANDLED, JSON.stringify(data)));
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

  /**
   * クライアントIDを設定
   * @param clientId クライアントID
   */
  public setClientId(clientId: string): void {
    this.clientId = clientId;
  }

  /**
   * クライアントIDを取得
   * @returns クライアントID
   */
  public getClientId(): string | null {
    return this.clientId;
  }


  /**
   * エコーメッセージを送信
   * @param text エコーするテキスト
   */
  public sendEcho(text: string): void {
    this.sendMessage({ type: 'echo', text: text });
  }

  /**
   * ブロードキャストメッセージを送信
   * @param content ブロードキャストする内容
   */
  public sendBroadcast(content: string): void {
    this.sendMessage({ type: 'broadcast', content: content });
  }

  /**
   * コマンドを送信
   * @param command コマンド文字列
   */
  public sendCommand(command: string): void {
    this.sendMessage({ type: 'command', command: command });
  }

  /**
   * カスタムメッセージを送信
   * @param type メッセージタイプ
   * @param data メッセージデータ
   */
  public sendCustomMessage(type: string, data: any): void {
    this.sendMessage({ type: type, ...data });
  }

  /**
   * クライアントレスポンスをサーバーに送信
   * @param command コマンド名
   * @param args レスポンスデータ
   * @param from送信元クライアントID
   */
  public sendClientResponse(command: string, args: any, from: string): void {
    this.sendMessage({ type: 'client', command: command, args: args, from: from });
  }

  /**
   * 目パチ状態を送信
   * @param enabled 有効/無効
   * @param from 送信元クライアントID
   */
  public sendEyeBlinkStatus(enabled: boolean, from: string): void {
    this.sendClientResponse('response_eye_blink', { enabled }, from);
  }

  /**
   * 呼吸状態を送信
   * @param enabled 有効/無効
   * @param from 送信元クライアントID
   */
  public sendBreathStatus(enabled: boolean, from: string): void {
    this.sendClientResponse('response_breath', { enabled }, from);
  }

  /**
   * アイドリングモーション状態を送信
   * @param enabled 有効/無効
   * @param from 送信元クライアントID
   */
  public sendIdleMotionStatus(enabled: boolean, from: string): void {
    this.sendClientResponse('response_idle_motion', { enabled }, from);
  }

  /**
   * ドラッグ追従状態を送信
   * @param enabled 有効/無効
   * @param from 送信元クライアントID
   */
  public sendDragFollowStatus(enabled: boolean, from: string): void {
    this.sendClientResponse('response_drag_follow', { enabled }, from);
  }

  /**
   * 物理演算状態を送信
   * @param enabled 有効/無効
   * @param from 送信元クライアントID
   */
  public sendPhysicsStatus(enabled: boolean, from: string): void {
    this.sendClientResponse('response_physics', { enabled }, from);
  }

  /**
   * 現在の表情を送信
   * @param expression 表情名
   * @param result 結果
   * @param from 送信元クライアントID
   */
  public sendExpressionStatus(expression: string, result: boolean, from: string): void {
    this.sendClientResponse('response_expression', { expression, result }, from);
  }

  /**
   * 現在のモーションを送信
   * @param group モーショングループ
   * @param no モーションインデックス
   * @param priority 優先度
   * @param result 結果
   * @param from 送信元クライアントID
   */
  public sendMotionStatus(group: string, no: number, priority: number, result: boolean, from: string): void {
    this.sendClientResponse('response_motion', { group, no, priority, result }, from);
  }

  /**
   * パラメータ設定結果を送信
   * @param successful 成功したパラメータ数
   * @param failed 失敗したパラメータ数
   * @param from 送信元クライアントID
   */
  public sendParameterStatus(successful: number, failed: number, from: string): void {
    this.sendClientResponse('response_parameter', { successful, failed }, from);
  }
  /**
   * 現在のモデル情報を送信
   * @param modelName モデル名
   * @param modelData モデル情報
   * @param from 送信元クライアントID
   */
  public sendModelInfo(modelName: string, from: string): void {
    this.sendClientResponse('response_model', { model_name: modelName }, from);
  }
  /**
   * ダイレクトメッセージ送信完了通知
   * @param from 送信元クライアントID
   */
  public sendResponseSend(from: string): void {
    this.sendClientResponse('response_send', {}, from);
  }
  /**
   * 通知メッセージ送信完了通知
   * @param from 送信元クライアントID
   */
  public sendResponseNotify(from: string): void {
    this.sendClientResponse('response_notify', {}, from);
  }

  /**
   * Wavファイルをリップシンク用に送信
   * @param filename ファイル名
   * @param result 結果
   * @param from 送信元クライアントID
   */
  public sendLipSyncWav(filename: string, result: boolean, from: string): void {
    this.sendClientResponse('response_lipsync', { filename, result }, from);
  }

  /**
   * 位置情報を送信
   * @param x X座標
   * @param y Y座標
   * @param from 送信元クライアントID
   */
  public sendResponsePosition(x: number, y: number, from: string): void {
    this.sendClientResponse('response_position', { x, y }, from);
  }

  /**
   * スケール情報を送信
   * @param scale スケール値
   * @param from 送信元クライアントID
   */
  public sendResponseScale(scale: number, from: string): void {
    this.sendClientResponse('response_scale', { scale }, from);
  }

  /**
   * ヒットイベントメッセージを送信
   * @param sprite スプライト名
   * @param posX スプライトのX座標
   * @param posY スプライトのY座標
   * @param x ビューのX座標
   * @param y ビューのY座標
   */
  public sendHit(sprite: string, posX: number, posY: number, x: number, y: number): void {
    this.sendCustomMessage('sprite_hit', {
      sprite: sprite,
      position: { x: posX, y: posY },
      viewPosition: { x, y }
    });
  }

  /**
   * モデルヒットイベントメッセージを送信
   * @param model_name モデル名
   * @param sprite スプライト名
   * @param x ビューのX座標
   * @param y ビューのY座標
   */
  public sendModelHit(model_name: string, sprite: string, x: number, y: number): void {
    this.sendCustomMessage('model_hit', {
      moc_name: model_name,
      sprite: sprite,
      position: { x, y }
    });
  }

  /**
   * 認証メッセージを送信
   * @param token 認証トークン
   */
  public sendAuth(token: string): void {
    this.sendMessage({ type: 'auth', token: token });
  }
}
