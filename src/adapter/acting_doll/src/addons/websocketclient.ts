/**
 * WebSocket Client for bidirectional communication
 * ブラウザ環境でのWebSocket通信クライアント
 */

import { CubismLogVerbose, CubismLogError, CubismLogInfo, CubismLogDebug }
  from '@framework/utils/cubismdebug';
import { LAppMultilingual, MessageKey } from './lappmultilingual';
import * as LAppDefine from './../base/lappdefine';
import { LAppPal } from './../base/lapppal';
import { LAppSubdelegate } from './../base/lappsubdelegate';

/**
 * WebSocketメッセージの基本型
 */
export interface WebSocketMessage {
  type: string;
  timestamp?: string;
  [key: string]: any;
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

  public setOnMessageHandlers(subdelegate: LAppSubdelegate): void {
    // メッセージハンドラを登録
    this.onMessage('welcome', (data) => {
      const clientId = data.client_id || 'unknown';
      this.setClientId(clientId);
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_WELCOME_RECEIVED, clientId));
    });

    this.onMessage('broadcast_message', (data) => {
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BROADCAST_RECEIVED, data));
    });

    // 接続を試みる
    this.connect().catch((error) => {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_CONNECTION_FAILED, error.toString()));
    });
    // ダイレクトメッセージ受信ハンドラー
    this.onMessage('send', (data: any) => {
      LAppPal.printMessage(`[send] ${data.message}`);
      this.sendResponseSend(data.from || '');
    });
    // 通知メッセージ受信ハンドラー
    this.onMessage('notify', (data: any) => {
      LAppPal.printMessage(`[notify] ${data.message}`);
      this.sendResponseNotify(data.from || '');
    });

    // 各リクエストに対するハンドラーを登録して状態を返す
    this.onMessage('request_eye_blink', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getEyeBlinkEnabled();
            this.sendEyeBlinkStatus(enabled, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_breath', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getBreathEnabled();
            this.sendBreathStatus(enabled, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_idle_motion', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getIdleMotionEnabled();
            this.sendIdleMotionStatus(enabled, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_drag_follow', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getDragFollowEnabled();
            this.sendDragFollowStatus(enabled, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_physics', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getPhysicsEnabled();
            this.sendPhysicsStatus(enabled, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_expression', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const expression = model.getCurrentExpression();
            this.sendExpressionStatus(expression || '', true, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_motion', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const motionInfo = model.getCurrentMotion();
            if (motionInfo) {
              this.sendMotionStatus(motionInfo.group, motionInfo.no, motionInfo.priority, true, data.from || '');
            } else {
              this.sendMotionStatus('', 0, 0, false, data.from || '');
            }
          }
        }
      }
    });

    this.onMessage('request_model_name', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const modelName = model.getModelName();
            this.sendModelName(modelName, data.from || '');
          }
        }
      }
    });

    this.onMessage('request_model_info', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            const motionInfo = model.getCurrentMotion();
            const view = subdelegate.getView();
            let pos_x: number = 0;
            let pos_y: number = 0;
            let scale: number = 1;
            if (view) {
              const viewMatrix = view.getViewMatrix();
              if (viewMatrix) {
                pos_x = parseFloat(viewMatrix.getTranslateX().toFixed(3));
                pos_y = parseFloat(viewMatrix.getTranslateY().toFixed(3));
              }
              scale = parseFloat(viewMatrix.getScaleX().toFixed(2));
            }
            const model_name = model.getModelName();
            const eye_blink = model.getEyeBlinkEnabled();
            const breath = model.getBreathEnabled();
            const idle_motion = model.getIdleMotionEnabled();
            const drag_follow = model.getDragFollowEnabled();
            const physics = model.getPhysicsEnabled();
            const expression = model.getCurrentExpression() || '';
            const motionInfo_group = motionInfo ? motionInfo.group : '';
            const motionInfo_no = motionInfo ? motionInfo.no : 0;
            const motionInfo_priority = motionInfo ? motionInfo.priority : 0;
            this.sendModelInfo(
              model_name, eye_blink,
              breath, idle_motion,
              drag_follow, physics,
              expression,
              motionInfo_group, motionInfo_no, motionInfo_priority,
              pos_x, pos_y, scale,
              data.from || '');
          }
        }
      }
    });

    // 設定メッセージのハンドラー
    this.onMessage('set_eye_blink', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            model.setEyeBlinkEnabled(data.enabled);
            // Update UI toggle
            const ui = subdelegate.getUI();
            if (ui) {
              ui.updateEyeBlinkToggle(data.enabled);
            }
            this.sendEyeBlinkStatus(data.enabled, data.from || '');
            CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EYE_BLINK_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
          }
        }
      }
    });

    this.onMessage('set_breath', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            model.setBreathEnabled(data.enabled);
            // Update UI toggle
            const ui = subdelegate.getUI();
            if (ui) {
              ui.updateBreathToggle(data.enabled);
            }
            this.sendBreathStatus(data.enabled, data.from || '');
            CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BREATH_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
          }
        }
      }
    });

    this.onMessage('set_idle_motion', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            model.setIdleMotionEnabled(data.enabled);
            // Update UI toggle
            const ui = subdelegate.getUI();
            if (ui) {
              ui.updateIdleMotionToggle(data.enabled);
            }
            this.sendIdleMotionStatus(data.enabled, data.from || '');
            CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_IDLE_MOTION_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
          }
        }
      }
    });

    this.onMessage('set_drag_follow', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            model.setDragFollowEnabled(data.enabled);
            // Update UI toggle
            const ui = subdelegate.getUI();
            if (ui) {
              ui.updateDragFollowToggle(data.enabled);
            }
            this.sendDragFollowStatus(data.enabled, data.from || '');
            CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_DRAG_FOLLOW_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
          }
        }
      }
    });

    this.onMessage('set_physics', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model) {
            model.setPhysicsEnabled(data.enabled);
            // Update UI toggle
            const ui = subdelegate.getUI();
            if (ui) {
              ui.updatePhysicsToggle(data.enabled);
            }
            this.sendPhysicsStatus(data.enabled, data.from || '');
            CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PHYSICS_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
          }
        }
      }
    });

    this.onMessage('set_expression', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model && data.expression) {
            const ret_expression = model.setExpression(data.expression);
            if (ret_expression === data.expression) {
              // Update UI select
              const ui = subdelegate.getUI();
              if (ui) {
                ui.updateExpressionSelect(ret_expression);
              }
              this.sendExpressionStatus(ret_expression, true, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EXPRESSION_SET, data.expression));
            } else {
              this.sendExpressionStatus(ret_expression || '', false, data.from || '');
            }
          }
        }
      }
    });

    this.onMessage('set_motion', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model && data.group !== undefined) {
            const no = data.no !== undefined ? data.no : 0;
            const priority = data.priority !== undefined ? data.priority : LAppDefine.PriorityNormal;
            const result = model.startMotion(data.group, no, priority);
            if (result === -1) {
              const motionInfo = model.getCurrentMotion();
              if (null === motionInfo) {
                this.sendMotionStatus('', -1, 0, false, data.from || '');
              } else {
                this.sendMotionStatus(motionInfo.group, motionInfo.no, motionInfo.priority, false, data.from || '');
              }
            } else {
              // Update UI select
              const ui = subdelegate.getUI();
              if (ui) {
                ui.updateMotionSelect(data.group, no);
              }
              this.sendMotionStatus(data.group, no, priority, true, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_MOTION_SET, data.group, no.toString()));
            }
          }
        }
      }
    });

    this.onMessage('set_lipsync', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model && data.wav_data) {
            // base64デコードしてArrayBufferに変換
            try {
              const binaryString = atob(data.wav_data);
              const bytes = new Uint8Array(binaryString.length);
              for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
              }
              const arrayBuffer = bytes.buffer;

              // Wavファイルハンドラーでロード
              model.loadWavFileFromBuffer(arrayBuffer, binaryString.length);
              this.sendLipSyncWav(data.filename || '', true, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.LIPSYNC_RECEIVED, data.filename || 'unknown'));
            } catch (error) {
              CubismLogError(LAppMultilingual.getMessage(MessageKey.LIPSYNC_DECODE_ERROR, error.toString()));
            }
          }
        }
      }
    });

    this.onMessage('set_parameter', (data: any) => {
      if (subdelegate) {
        const live2DManager = subdelegate.getLive2DManager();
        if (live2DManager) {
          const model = live2DManager.getModel(0);
          if (model && data.parameters) {
            // 一括設定モード: {"parameters": {"ParamAngleX": 30, "ParamAngleY": -15, ...}}
            let setCount = 0;
            let notFoundCount = 0;

            for (const paramName in data.parameters) {
              const paramValue = data.parameters[paramName];
              const paramIndex = model.getParameterIndex(paramName);
              if (paramIndex >= 0) {
                model.setParameterValueByIndex(paramIndex, paramValue);
                // Update UI slider
                const ui = subdelegate.getUI();
                if (ui) {
                  ui.updateParameterSlider(paramName, paramValue);
                }
                setCount++;
              } else {
                CubismLogDebug(LAppMultilingual.getMessage(MessageKey.WS_PARAM_NOT_FOUND, paramName));
                notFoundCount++;
              }
            }
            this.sendParameterStatus(setCount, notFoundCount, data.from || '');
            CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PARAMS_SET, setCount.toString(), notFoundCount.toString()));
          }
        }
      }
    });

    this.onMessage('request_position', (data: any) => {
      if (subdelegate) {
        const view = subdelegate.getView();
        if (view) {
          const viewMatrix = view.getViewMatrix();
          if (viewMatrix) {
            const x: number = parseFloat(viewMatrix.getTranslateX().toFixed(3));
            const y: number = parseFloat(viewMatrix.getTranslateY().toFixed(3));
            this.sendResponsePosition(x, y, data.from || '');
          }
        }
      }
    });

    this.onMessage('set_position', (data: any) => {
      if (subdelegate) {
        const view = subdelegate.getView();
        if (view && data.x !== undefined && data.y !== undefined) {
          // Update UI
          const ui = subdelegate.getUI();
          if (ui) {
            ui.moveModel(data.x, data.y, data.relative);
            const viewMatrix = view.getViewMatrix();
            if (viewMatrix) {
              const x: number = parseFloat(viewMatrix.getTranslateX().toFixed(3));
              const y: number = parseFloat(viewMatrix.getTranslateY().toFixed(3));
              this.sendResponsePosition(x, y, data.from || '');
            }
          }
        }
      }
    });

    this.onMessage('request_scale', (data: any) => {
      if (subdelegate) {
        const view = subdelegate.getView();
        if (view) {
          const viewMatrix = view.getViewMatrix();
          const scale: number = parseFloat(viewMatrix.getScaleX().toFixed(2));
          this.sendResponseScale(scale, data.from || '');
        }
      }
    });

    this.onMessage('set_scale', (data: any) => {
      if (subdelegate) {
        const view = subdelegate.getView();
        if (view && data.scale !== undefined) {
          view.setViewScale(data.scale);
          // Update UI
          const ui = subdelegate.getUI();
          if (ui) {
            ui.updateScaleSlider(data.scale);
            this.sendResponseScale(data.scale, data.from || '');
          }
        }
      }
    });

    CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CLIENT_INITIALIZED));
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
    return (this.websocket !== null && this.websocket.readyState === WebSocket.OPEN);
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
   * 現在のモデル名を送信
   * @param modelName モデル名
   * @param from 送信元クライアントID
   */
  public sendModelName(modelName: string, from: string): void {
    this.sendClientResponse('response_model_name', { model_name: modelName }, from);
  }
  /**
   * 現在のモデル名を送信
   * @param modelName モデル名
   * @param from 送信元クライアントID
   */
  public sendModelInfo(
    modelName: string,
    eye_blink: boolean,
    breath: boolean,
    idle_motion: boolean,
    drag_follow: boolean,
    physics: boolean,
    expression: string,
    motion_group: string,
    motion_no: number,
    motion_priority: number,
    positionX: number,
    positionY: number,
    scale: number,
    from: string): void {

    this.sendClientResponse('response_model_info', {
      model_name: modelName, eye_blink: eye_blink, breath: breath,
      idle_motion: idle_motion, drag_follow: drag_follow, physics: physics,
      expression: expression,
      motion: { group: motion_group, no: motion_no, priority: motion_priority },
      position: { x: positionX, y: positionY }, scale: scale
    }, from);
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
