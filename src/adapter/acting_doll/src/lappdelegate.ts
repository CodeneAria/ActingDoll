/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

import { csmVector } from '@framework/type/csmvector';
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
    for (
      let ite = this._subdelegates.begin();
      ite.notEqual(this._subdelegates.end());
      ite.preIncrement()
    ) {
      ite.ptr().onPointBegan(e.pageX, e.pageY);
    }
  }

  /**
   * ポインタが動いたら呼ばれる。
   */
  private onPointerMoved(e: PointerEvent): void {
    for (
      let ite = this._subdelegates.begin();
      ite.notEqual(this._subdelegates.end());
      ite.preIncrement()
    ) {
      ite.ptr().onPointMoved(e.pageX, e.pageY);
    }
  }

  /**
   * ポインタがアクティブでなくなったときに呼ばれる。
   */
  private onPointerEnded(e: PointerEvent): void {
    for (
      let ite = this._subdelegates.begin();
      ite.notEqual(this._subdelegates.end());
      ite.preIncrement()
    ) {
      ite.ptr().onPointEnded(e.pageX, e.pageY);
    }
  }

  /**
   * ポインタがキャンセルされると呼ばれる。
   */
  private onPointerCancel(e: PointerEvent): void {
    for (
      let ite = this._subdelegates.begin();
      ite.notEqual(this._subdelegates.end());
      ite.preIncrement()
    ) {
      ite.ptr().onTouchCancel(e.pageX, e.pageY);
    }
  }

  /**
   * Resize canvas and re-initialize view.
   */
  public onResize(): void {
    for (let i = 0; i < this._subdelegates.getSize(); i++) {
      this._subdelegates.at(i).onResize();
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

      for (let i = 0; i < this._subdelegates.getSize(); i++) {
        this._subdelegates.at(i).update();
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
    for (
      let ite = this._subdelegates.begin();
      ite.notEqual(this._subdelegates.end());
      ite.preIncrement()
    ) {
      ite.ptr().release();
    }

    this._subdelegates.clear();
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

    this._canvases.prepareCapacity(LAppDefine.CanvasNum);
    this._subdelegates.prepareCapacity(LAppDefine.CanvasNum);
    for (let i = 0; i < LAppDefine.CanvasNum; i++) {
      const canvas = document.createElement('canvas');
      this._canvases.pushBack(canvas);
      canvas.style.width = `${width}vw`;
      canvas.style.height = `${height}vh`;

      // キャンバスを DOM に追加
      document.body.appendChild(canvas);
    }

    for (let i = 0; i < this._canvases.getSize(); i++) {
      const subdelegate = new LAppSubdelegate();
      subdelegate.initialize(this._canvases.at(i));
      this._subdelegates.pushBack(subdelegate);
    }

    for (let i = 0; i < LAppDefine.CanvasNum; i++) {
      if (this._subdelegates.at(i).isContextLost()) {
        CubismLogError(LAppMultilingual.getMessage(MessageKey.CANVAS_CONTEXT_LOST, i.toString()));
      }
    }
  }

  /**
   * Privateなコンストラクタ
   */
  private constructor() {
    this._cubismOption = new Option();
    this._subdelegates = new csmVector<LAppSubdelegate>();
    this._canvases = new csmVector<HTMLCanvasElement>();
    this._websocketClient = null;
  }

  /**
   * WebSocketクライアントを初期化
   */
  private initializeWebSocket(): void {
    if (LAppDefine.WebSocketAutoConnect) {
      this._websocketClient = new WebSocketClient(LAppDefine.WebSocketUrl + LAppDefine.WebSocketAddress + ":" + LAppDefine.WebSocketPort);

      // メッセージハンドラを登録
      this._websocketClient.onMessage('welcome', (data) => {
        CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_WELCOME_RECEIVED));
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
        this._websocketClient.sendResponseSend();
      });
      // 通知メッセージ受信ハンドラー
      this._websocketClient.onMessage('notify', (data: any) => {
        LAppPal.printMessage(`[notify] ${data.message}`);
        this._websocketClient.sendResponseNotify();
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
              this._websocketClient.sendEyeBlinkStatus(enabled);
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
              this._websocketClient.sendBreathStatus(enabled);
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
              this._websocketClient.sendIdleMotionStatus(enabled);
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
              this._websocketClient.sendDragFollowStatus(enabled);
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
              this._websocketClient.sendPhysicsStatus(enabled);
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
              this._websocketClient.sendExpressionStatus(expression || '', true);
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
                this._websocketClient.sendMotionStatus(motionInfo.group, motionInfo.no, motionInfo.priority, true);
              } else {
                this._websocketClient.sendMotionStatus('', 0, 0, false);
              }
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
              const modelName = model.getModelName();
              this._websocketClient.sendModelInfo(modelName);
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
              this._websocketClient.sendEyeBlinkStatus(data.enabled);
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
              this._websocketClient.sendBreathStatus(data.enabled);
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
              this._websocketClient.sendIdleMotionStatus(data.enabled);
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
              this._websocketClient.sendDragFollowStatus(data.enabled);
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
              this._websocketClient.sendPhysicsStatus(data.enabled);
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
                this._websocketClient.sendExpressionStatus(ret_expression, true);
                CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_EXPRESSION_SET, data.expression));
              } else {
                this._websocketClient.sendExpressionStatus(ret_expression || '', false);
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
                  this._websocketClient.sendMotionStatus('', -1, 0, false);
                } else {
                  this._websocketClient.sendMotionStatus(motionInfo.group, motionInfo.no, motionInfo.priority, false);
                }
              } else {
                // Update UI select
                const ui = subdelegate.getUI();
                if (ui) {
                  ui.updateMotionSelect(data.group, no);
                }
                this._websocketClient.sendMotionStatus(data.group, no, priority, true);
                CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_MOTION_SET, data.group, no.toString()));
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
              this._websocketClient.sendParameterStatus(setCount, notFoundCount);
              CubismLogInfo(LAppMultilingual.getMessage(MessageKey.WS_PARAMS_SET, setCount.toString(), notFoundCount.toString()));
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
    if (index < this._subdelegates.getSize()) {
      return this._subdelegates.at(index);
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
  private _canvases: csmVector<HTMLCanvasElement>;

  /**
   * Subdelegate
   */
  private _subdelegates: csmVector<LAppSubdelegate>;

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
