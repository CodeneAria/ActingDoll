/**
 * WebSocket Client for bidirectional communication
 * ブラウザ環境でのWebSocket通信クライアント
 */

import {
  CubismLogVerbose,
  CubismLogError,
  CubismLogInfo,
  CubismLogDebug
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
      CubismLogDebug(LAppMultilingual.getMessage(MessageKey.WS_SENDING, messageJson));
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
    //this.logMessage(data);
  }

  /**
   * メッセージのログ出力
   * @param data メッセージデータ
   */
  private logMessage(data: WebSocketMessage): void {
    const msgType = data.type || 'unknown';

    switch (msgType) {
      case 'welcome':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_WELCOME_MESSAGE, (data as WelcomeResponse).message));
        break;
      case 'echo_response':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_ECHO_RESPONSE, (data as EchoResponse).original));
        break;
      case 'broadcast_message':
        const broadcast = data as BroadcastResponse;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BROADCAST_FROM, broadcast.from, broadcast.content));
        break;
      case 'client_connected':
        const connected = data as ClientConnectedMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CLIENT_CONNECTED, connected.total_clients.toString()));
        break;
      case 'client_disconnected':
        const disconnected = data as ClientDisconnectedMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CLIENT_DISCONNECTED, disconnected.total_clients.toString()));
        break;
      case 'command_response':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_COMMAND_RESPONSE, data));
        break;
      case 'error':
        CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_ERROR_MESSAGE, (data as ErrorMessage).message));
        break;
      case 'set_eye_blink':
        const eyeBlink = data as SetEyeBlinkMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EYE_BLINK_SETTING,
          eyeBlink.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
        break;
      case 'set_breath':
        const breath = data as SetBreathMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BREATH_SETTING,
          breath.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
        break;
      case 'set_idle_motion':
        const idleMotion = data as SetIdleMotionMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_IDLE_MOTION_SETTING,
          idleMotion.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
        break;
      case 'set_drag_follow':
        const dragFollow = data as SetDragFollowMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_DRAG_FOLLOW_SETTING,
          dragFollow.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
        break;
      case 'set_physics':
        const physics = data as SetPhysicsMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PHYSICS_SETTING,
          physics.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
        break;
      case 'set_expression':
        const expression = data as SetExpressionMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EXPRESSION_SETTING, expression.expression));
        break;
      case 'set_motion':
        const motion = data as SetMotionMessage;
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_MOTION_SETTING, motion.group,
          (motion.no ?? LAppMultilingual.getMessage(MessageKey.RANDOM)).toString()));
        break;
      case 'set_parameter':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PARAM_RECEIVED));
        break;
      case 'request_model_info':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_MODEL_INFO_REQUEST));
        break;
      case 'request_eye_blink':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EYE_BLINK_REQUEST));
        break;
      case 'request_breath':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BREATH_REQUEST));
        break;
      case 'request_idle_motion':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_IDLE_MOTION_REQUEST));
        break;
      case 'request_drag_follow':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_DRAG_FOLLOW_REQUEST));
        break;
      case 'request_physics':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PHYSICS_REQUEST));
        break;
      case 'request_expression':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EXPRESSION_REQUEST));
        break;
      case 'request_motion':
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_MOTION_REQUEST));
        break;
      default:
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_UNHANDLED_MESSAGE, msgType, data));
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
   */
  public sendClientResponse(command: string, args: any): void {
    this.sendMessage({ type: 'client', command: command, args: args });
  }

  /**
   * 目パチ状態を送信
   * @param enabled 有効/無効
   */
  public sendEyeBlinkStatus(enabled: boolean): void {
    this.sendClientResponse('response_eye_blink', { enabled });
  }

  /**
   * 呼吸状態を送信
   * @param enabled 有効/無効
   */
  public sendBreathStatus(enabled: boolean): void {
    this.sendClientResponse('response_breath', { enabled });
  }

  /**
   * アイドリングモーション状態を送信
   * @param enabled 有効/無効
   */
  public sendIdleMotionStatus(enabled: boolean): void {
    this.sendClientResponse('response_idle_motion', { enabled });
  }

  /**
   * ドラッグ追従状態を送信
   * @param enabled 有効/無効
   */
  public sendDragFollowStatus(enabled: boolean): void {
    this.sendClientResponse('response_drag_follow', { enabled });
  }

  /**
   * 物理演算状態を送信
   * @param enabled 有効/無効
   */
  public sendPhysicsStatus(enabled: boolean): void {
    this.sendClientResponse('response_physics', { enabled });
  }

  /**
   * 現在の表情を送信
   * @param expression 表情名
   */
  public sendExpressionStatus(expression: string, result: boolean): void {
    this.sendClientResponse('response_expression', { expression, result });
  }

  /**
   * 現在のモーションを送信
   * @param group モーショングループ
   * @param no モーションインデックス
   */
  public sendMotionStatus(group: string, no: number, priority: number, result: boolean): void {
    this.sendClientResponse('response_motion', { group, no, priority, result });
  }

  /**
   * パラメータ設定結果を送信
   * @param successful 成功したパラメータ数
   * @param failed 失敗したパラメータ数
   */
  public sendParameterStatus(successful: number, failed: number): void {
    this.sendClientResponse('response_parameter', { successful, failed });
  }
  /**
   * 現在のモデル情報を送信
   * @param modelName モデル名
   * @param modelData モデル情報
   */
  public sendModelInfo(modelName: string, modelData?: any): void {
    this.sendClientResponse('response_model', { model_name: modelName, ...modelData });
  }
  /**
   * ダイレクトメッセージ送信完了通知
   */
  public sendResponseSend(): void {
    this.sendClientResponse('response_send', {});
  }
  /**
   * 通知メッセージ送信完了通知
   */
  public sendResponseNotify(): void {
    this.sendClientResponse('response_notify', {});
  }
}
