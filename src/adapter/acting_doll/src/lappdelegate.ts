/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

import { CubismFramework, Option } from '@framework/live2dcubismframework';
import * as LAppDefine from './lappdefine';
import { LAppPal } from './lapppal';
import { LAppSubdelegate } from './lappsubdelegate';
import {
  CubismLogDebug,
  CubismLogError,
  CubismLogInfo
} from '@framework/utils/cubismdebug';
import { WebSocketClient } from './websocketclient';
import { LAppMultilingual, MessageKey } from './lappmultilingual';

export let s_instance: LAppDelegate = null;

/**
 * アプリケーションクラス。
 * Cubism SDKの管理を行う。
 */
export class LAppDelegate {
  /**
   * クラスのインスタンス（シングルトン）を返す。
   * インスタンスが生成されていない場合は内部でインスタンスを生成する。
   *
   * @return クラスのインスタンス
   */
  public static getInstance(): LAppDelegate {
    if (s_instance == null) {
      s_instance = new LAppDelegate();
    }

    return s_instance;
  }

  /**
   * クラスのインスタンス（シングルトン）を解放する。
   */
  public static releaseInstance(): void {
    if (s_instance != null) {
      s_instance.release();
    }

    s_instance = null;
  }

  /**
   * ポインタがアクティブになるときに呼ばれる。
   */
  private onPointerBegan(e: PointerEvent): void {
    for (let i = 0; i < this._subdelegates.length; i++) {
      this._subdelegates[i].onPointBegan(e.pageX, e.pageY);
    }
  }

  /**
   * ポインタが動いたら呼ばれる。
   */
  private onPointerMoved(e: PointerEvent): void {
    for (let i = 0; i < this._subdelegates.length; i++) {
      this._subdelegates[i].onPointMoved(e.pageX, e.pageY);
    }
  }

  /**
   * ポインタがアクティブでなくなったときに呼ばれる。
   */
  private onPointerEnded(e: PointerEvent): void {
    for (let i = 0; i < this._subdelegates.length; i++) {
      this._subdelegates[i].onPointEnded(e.pageX, e.pageY);
    }
  }

  /**
   * ポインタがキャンセルされると呼ばれる。
   */
  private onPointerCancel(e: PointerEvent): void {
    for (let i = 0; i < this._subdelegates.length; i++) {
      this._subdelegates[i].onTouchCancel(e.pageX, e.pageY);
    }
  }

  /**
   * Resize canvas and re-initialize view.
   */
  public onResize(): void {
    for (let i = 0; i < this._subdelegates.length; i++) {
      this._subdelegates[i].onResize();
    }
  }

  /**
   * 実行処理。
   */
  public run(): void {
    // メインループ
    const loop = (): void => {
      // インスタンスの有無の確認
      if (s_instance == null) {
        return;
      }

      // 時間更新
      LAppPal.updateTime();

      for (let i = 0; i < this._subdelegates.length; i++) {
        this._subdelegates[i].update();
      }

      // ループのために再帰呼び出し
      requestAnimationFrame(loop);
    };
    loop();
  }

  /**
   * 解放する。
   */
  private release(): void {
    this.releaseEventListener();
    this.releaseSubdelegates();
    this.releaseWebSocket();

    // Cubism SDKの解放
    CubismFramework.dispose();

    this._cubismOption = null;
  }

  /**
   * イベントリスナーを解除する。
   */
  private releaseEventListener(): void {
    document.removeEventListener('pointerup', this.pointBeganEventListener);
    this.pointBeganEventListener = null;
    document.removeEventListener('pointermove', this.pointMovedEventListener);
    this.pointMovedEventListener = null;
    document.removeEventListener('pointerdown', this.pointEndedEventListener);
    this.pointEndedEventListener = null;
    document.removeEventListener('pointerdown', this.pointCancelEventListener);
    this.pointCancelEventListener = null;
  }

  /**
   * Subdelegate を解放する
   */
  private releaseSubdelegates(): void {
    for (let i = 0; i < this._subdelegates.length; i++) {
      this._subdelegates[i].release();
    }

    this._subdelegates.length = 0;
    this._subdelegates = null;
  }

  /**
   * APPに必要な物を初期化する。
   */
  public initialize(): boolean {
    // Cubism SDKの初期化
    this.initializeCubism();

    this.initializeSubdelegates();
    this.initializeEventListener();
    this.initializeWebSocket();

    return true;
  }

  /**
   * イベントリスナーを設定する。
   */
  private initializeEventListener(): void {
    this.pointBeganEventListener = this.onPointerBegan.bind(this);
    this.pointMovedEventListener = this.onPointerMoved.bind(this);
    this.pointEndedEventListener = this.onPointerEnded.bind(this);
    this.pointCancelEventListener = this.onPointerCancel.bind(this);

    // ポインタ関連コールバック関数登録
    document.addEventListener('pointerdown', this.pointBeganEventListener, {
      passive: true
    });
    document.addEventListener('pointermove', this.pointMovedEventListener, {
      passive: true
    });
    document.addEventListener('pointerup', this.pointEndedEventListener, {
      passive: true
    });
    document.addEventListener('pointercancel', this.pointCancelEventListener, {
      passive: true
    });
  }

  /**
   * Cubism SDKの初期化
   */
  private initializeCubism(): void {
    LAppPal.updateTime();

    // setup cubism
    this._cubismOption.logFunction = LAppPal.printMessage;
    this._cubismOption.loggingLevel = LAppDefine.CubismLoggingLevel;
    CubismFramework.startUp(this._cubismOption);

    // initialize cubism
    CubismFramework.initialize();
  }

  /**
   * Canvasを生成配置、Subdelegateを初期化する
   */
  private initializeSubdelegates(): void {
    let width: number = 100;
    let height: number = 100;
    if (LAppDefine.CanvasNum > 3) {
      const widthunit: number = Math.ceil(Math.sqrt(LAppDefine.CanvasNum));
      const heightUnit = Math.ceil(LAppDefine.CanvasNum / widthunit);
      width = 100.0 / widthunit;
      height = 100.0 / heightUnit;
    } else {
      width = 100.0 / LAppDefine.CanvasNum;
    }

    this._canvases.length = LAppDefine.CanvasNum;
    this._subdelegates.length = LAppDefine.CanvasNum;
    for (let i = 0; i < LAppDefine.CanvasNum; i++) {
      const canvas = document.createElement('canvas');
      this._canvases[i] = canvas;
      canvas.style.width = `${width}vw`;
      canvas.style.height = `${height}vh`;

      // キャンバスを DOM に追加
      document.body.appendChild(canvas);
    }

    for (let i = 0; i < this._canvases.length; i++) {
      const subdelegate = new LAppSubdelegate();
      subdelegate.initialize(this._canvases[i]);
      this._subdelegates[i] = subdelegate;
    }

    for (let i = 0; i < LAppDefine.CanvasNum; i++) {
      if (this._subdelegates[i].isContextLost()) {
        CubismLogError(
          `The context for Canvas at index ${i} was lost, possibly because the acquisition limit for WebGLRenderingContext was reached.`
        );
      }
    }
  }

  /**
   * Privateなコンストラクタ
   */
  private constructor() {
    this._cubismOption = new Option();
    this._subdelegates = new Array<LAppSubdelegate>();
    this._canvases = new Array<HTMLCanvasElement>();
    this._websocketClient = null;
  }

  /**
   * WebSocketクライアントを初期化
   */
  private initializeWebSocket(): void {
    if (LAppDefine.WebSocketAutoConnect) {
      this._websocketClient = new WebSocketClient(LAppDefine.WebSocketUrl + location.hostname + ':' + LAppDefine.WebSocketPort);

      // メッセージハンドラを登録
      this._websocketClient.onMessage('welcome', (data) => {
        const clientId = data.client_id || 'unknown';
        this._websocketClient.setClientId(clientId);
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_WELCOME_RECEIVED, clientId));
      });

      this._websocketClient.onMessage('broadcast_message', (data) => {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BROADCAST_RECEIVED, data));
      });

      // 接続を試みる
      this._websocketClient.connect().catch((error) => {
        CubismLogError(LAppMultilingual.getMessage(MessageKey.WS_CONNECTION_FAILED, error.toString()));
      });
      // ダイレクトメッセージ受信ハンドラー
      this._websocketClient.onMessage('send', (data: any) => {
        LAppPal.printMessage(`[send] ${data.message}`);
        this._websocketClient.sendResponseSend(data.from || '');
      });
      // 通知メッセージ受信ハンドラー
      this._websocketClient.onMessage('notify', (data: any) => {
        LAppPal.printMessage(`[notify] ${data.message}`);
        this._websocketClient.sendResponseNotify(data.from || '');
      });

      // 各リクエストに対するハンドラーを登録して状態を返す
      this._websocketClient.onMessage('request_eye_blink', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const enabled = model.getEyeBlinkEnabled();
              this._websocketClient.sendEyeBlinkStatus(enabled, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_breath', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const enabled = model.getBreathEnabled();
              this._websocketClient.sendBreathStatus(enabled, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_idle_motion', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const enabled = model.getIdleMotionEnabled();
              this._websocketClient.sendIdleMotionStatus(enabled, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_drag_follow', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const enabled = model.getDragFollowEnabled();
              this._websocketClient.sendDragFollowStatus(enabled, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_physics', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const enabled = model.getPhysicsEnabled();
              this._websocketClient.sendPhysicsStatus(enabled, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_expression', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const expression = model.getCurrentExpression();
              this._websocketClient.sendExpressionStatus(expression || '', true, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_motion', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const motionInfo = model.getCurrentMotion();
              if (motionInfo) {
                this._websocketClient.sendMotionStatus(motionInfo.group, motionInfo.no, motionInfo.priority, true, data.from || '');
              } else {
                this._websocketClient.sendMotionStatus('', 0, 0, false, data.from || '');
              }
            }
          }
        }
      });

      this._websocketClient.onMessage('request_model_name', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          if (live2DManager) {
            const model = live2DManager.getModel(0);
            if (model) {
              const modelName = model.getModelName();
              this._websocketClient.sendModelName(modelName, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('request_model_info', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
                scale = viewMatrix.getScaleX();
              }
              this._websocketClient.sendModelInfo(
                model.getModelName(), model.getEyeBlinkEnabled(),
                model.getBreathEnabled(), model.getIdleMotionEnabled(),
                model.getDragFollowEnabled(), model.getPhysicsEnabled(),
                model.getCurrentExpression() || '',
                motionInfo.group || '', motionInfo.no || 0, motionInfo.priority || 0,
                pos_x, pos_y, scale,
                data.from || '');
            }
          }
        }
      });

      // 設定メッセージのハンドラー
      this._websocketClient.onMessage('set_eye_blink', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
              this._websocketClient.sendEyeBlinkStatus(data.enabled, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EYE_BLINK_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
            }
          }
        }
      });

      this._websocketClient.onMessage('set_breath', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
              this._websocketClient.sendBreathStatus(data.enabled, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_BREATH_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
            }
          }
        }
      });

      this._websocketClient.onMessage('set_idle_motion', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
              this._websocketClient.sendIdleMotionStatus(data.enabled, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_IDLE_MOTION_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
            }
          }
        }
      });

      this._websocketClient.onMessage('set_drag_follow', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
              this._websocketClient.sendDragFollowStatus(data.enabled, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_DRAG_FOLLOW_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
            }
          }
        }
      });

      this._websocketClient.onMessage('set_physics', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
              this._websocketClient.sendPhysicsStatus(data.enabled, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PHYSICS_SET, data.enabled ? LAppMultilingual.getMessage(MessageKey.ENABLED) : LAppMultilingual.getMessage(MessageKey.DISABLED)));
            }
          }
        }
      });

      this._websocketClient.onMessage('set_expression', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
                this._websocketClient.sendExpressionStatus(ret_expression, true, data.from || '');
                CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EXPRESSION_SET, data.expression));
              } else {
                this._websocketClient.sendExpressionStatus(ret_expression || '', false, data.from || '');
              }
            }
          }
        }
      });

      this._websocketClient.onMessage('set_motion', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
                  this._websocketClient.sendMotionStatus('', -1, 0, false, data.from || '');
                } else {
                  this._websocketClient.sendMotionStatus(motionInfo.group, motionInfo.no, motionInfo.priority, false, data.from || '');
                }
              } else {
                // Update UI select
                const ui = subdelegate.getUI();
                if (ui) {
                  ui.updateMotionSelect(data.group, no);
                }
                this._websocketClient.sendMotionStatus(data.group, no, priority, true, data.from || '');
                CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_MOTION_SET, data.group, no.toString()));
              }
            }
          }
        }
      });

      this._websocketClient.onMessage('set_lipsync', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
                this._websocketClient.sendLipSyncWav(data.filename || '', true, data.from || '');
                CubismLogInfo(LAppMultilingual.getMessage(MessageKey.LIPSYNC_RECEIVED, data.filename || 'unknown'));
              } catch (error) {
                CubismLogError(LAppMultilingual.getMessage(MessageKey.LIPSYNC_DECODE_ERROR, error.toString()));
              }
            }
          }
        }
      });

      this._websocketClient.onMessage('set_parameter', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
              this._websocketClient.sendParameterStatus(setCount, notFoundCount, data.from || '');
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PARAMS_SET, setCount.toString(), notFoundCount.toString()));
            }
          }
        }
      });

      this._websocketClient.onMessage('request_position', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const view = subdelegate.getView();
          if (view) {
            const viewMatrix = view.getViewMatrix();
            if (viewMatrix) {
              const x: number = parseFloat(viewMatrix.getTranslateX().toFixed(3));
              const y: number = parseFloat(viewMatrix.getTranslateY().toFixed(3));
              this._websocketClient.sendResponsePosition(x, y, data.from || '');
            }
          }
        }
      });

      this._websocketClient.onMessage('set_position', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
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
                this._websocketClient.sendResponsePosition(x, y, data.from || '');
              }
            }
          }
        }
      });

      this._websocketClient.onMessage('request_scale', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const view = subdelegate.getView();
          if (view) {
            const viewMatrix = view.getViewMatrix();
            const scale = viewMatrix.getScaleX();
            this._websocketClient.sendResponseScale(scale, data.from || '');
          }
        }
      });

      this._websocketClient.onMessage('set_scale', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const view = subdelegate.getView();
          if (view && data.scale !== undefined) {
            view.setViewScale(data.scale);
            // Update UI
            const ui = subdelegate.getUI();
            if (ui) {
              ui.updateScaleSlider(data.scale);
              this._websocketClient.sendResponseScale(data.scale, data.from || '');
            }
          }
        }
      });

      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CLIENT_INITIALIZED));
    }
  }

  /**
   * WebSocketクライアントを解放
   */
  private releaseWebSocket(): void {
    if (this._websocketClient) {
      this._websocketClient.disconnect();
      this._websocketClient = null;
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_CLIENT_RELEASED));
    }
  }

  /**
   * WebSocketクライアントを取得
   */
  public getWebSocketClient(): WebSocketClient | null {
    return this._websocketClient;
  }

  /**
   * 最初のSubdelegateを取得
   */
  public getSubdelegate(index: number = 0): LAppSubdelegate | null {
    if (index < this._subdelegates.length) {
      return this._subdelegates[index];
    }
    return null;
  }

  /**
   * Cubism SDK Option
   */
  private _cubismOption: Option;

  /**
   * 操作対象のcanvas要素
   */
  private _canvases: Array<HTMLCanvasElement>;

  /**
   * Subdelegate
   */
  private _subdelegates: Array<LAppSubdelegate>;

  /**
   * 登録済みイベントリスナー 関数オブジェクト
   */
  private pointBeganEventListener: (this: Document, ev: PointerEvent) => void;

  /**
   * 登録済みイベントリスナー 関数オブジェクト
   */
  private pointMovedEventListener: (this: Document, ev: PointerEvent) => void;

  /**
   * 登録済みイベントリスナー 関数オブジェクト
   */
  private pointEndedEventListener: (this: Document, ev: PointerEvent) => void;

  /**
   * 登録済みイベントリスナー 関数オブジェクト
   */
  private pointCancelEventListener: (this: Document, ev: PointerEvent) => void;

  /**
   * WebSocketクライアント
   */
  private _websocketClient: WebSocketClient | null;
}
