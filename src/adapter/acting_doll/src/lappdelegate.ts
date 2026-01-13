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
import { CubismLogError } from '@framework/utils/cubismdebug';
import { WebSocketClient } from './websocketclient';
import { LAppUI } from './lappui';

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
        console.log('[WebSocket] ウェルカムメッセージを受信しました');
      });

      this._websocketClient.onMessage('broadcast_message', (data) => {
        console.log('[WebSocket] ブロードキャストメッセージを受信:', data);
      });

      // 接続を試みる
      this._websocketClient.connect().catch((error) => {
        console.error('[WebSocket] 接続に失敗しました:', error);
      });

      // 各リクエストに対するハンドラーを登録して状態を返す
      this._websocketClient.onMessage('request_eye_blink', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getEyeBlinkEnabled();
            this._websocketClient.sendEyeBlinkStatus(enabled);
          }
        }
      });

      this._websocketClient.onMessage('request_breath', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getBreathEnabled();
            this._websocketClient.sendBreathStatus(enabled);
          }
        }
      });

      this._websocketClient.onMessage('request_idle_motion', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getIdleMotionEnabled();
            this._websocketClient.sendIdleMotionStatus(enabled);
          }
        }
      });

      this._websocketClient.onMessage('request_drag_follow', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const enabled = model.getDragFollowEnabled();
            this._websocketClient.sendDragFollowStatus(enabled);
          }
        }
      });
      this._websocketClient.onMessage('request_expression', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const expression = model.getCurrentExpression();
            this._websocketClient.sendExpressionStatus(expression || '');
          }
        }
      });

      this._websocketClient.onMessage('request_motion', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const motionInfo = model.getCurrentMotion();
            if (motionInfo) {
              this._websocketClient.sendMotionStatus(motionInfo.group, motionInfo.no);
            } else {
              this._websocketClient.sendMotionStatus('', 0);
            }
          }
        }
      });

      this._websocketClient.onMessage('request_model_info', () => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            const modelName = model.getModelName();
            this._websocketClient.sendModelInfo(modelName);
          }
        }
      });

      // 設定メッセージのハンドラー
      this._websocketClient.onMessage('set_eye_blink', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            model.setEyeBlinkEnabled(data.enabled);
            // Update UI toggle
            const ui = LAppUI.getInstance();
            if (ui) {
              ui.updateEyeBlinkToggle(data.enabled);
            }
            console.log('[WebSocket] 自動目パチを設定しました:', data.enabled);
          }
        }
      });

      this._websocketClient.onMessage('set_breath', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            model.setBreathEnabled(data.enabled);
            // Update UI toggle
            const ui = LAppUI.getInstance();
            if (ui) {
              ui.updateBreathToggle(data.enabled);
            }
            console.log('[WebSocket] 呼吸を設定しました:', data.enabled);
          }
        }
      });

      this._websocketClient.onMessage('set_idle_motion', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            model.setIdleMotionEnabled(data.enabled);
            // Update UI toggle
            const ui = LAppUI.getInstance();
            if (ui) {
              ui.updateIdleMotionToggle(data.enabled);
            }
            console.log('[WebSocket] アイドリングモーションを設定しました:', data.enabled);
          }
        }
      });

      this._websocketClient.onMessage('set_drag_follow', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model) {
            model.setDragFollowEnabled(data.enabled);
            // Update UI toggle
            const ui = LAppUI.getInstance();
            if (ui) {
              ui.updateDragFollowToggle(data.enabled);
            }
            console.log('[WebSocket] ドラッグ追従を設定しました:', data.enabled);
          }
        }
      });

      this._websocketClient.onMessage('set_expression', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model && data.expression) {
            model.setExpression(data.expression);
            // Update UI select
            const ui = LAppUI.getInstance();
            if (ui) {
              ui.updateExpressionSelect(data.expression);
            }
            console.log('[WebSocket] 表情を設定しました:', data.expression);
          }
        }
      });

      this._websocketClient.onMessage('set_motion', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model && data.group !== undefined) {
            const index = data.index !== undefined ? data.index : 0;
            model.startMotion(data.group, index, LAppDefine.PriorityNormal);
            // Update UI select
            const ui = LAppUI.getInstance();
            if (ui) {
              ui.updateMotionSelect(data.group, index);
            }
            console.log('[WebSocket] モーションを設定しました:', data.group, index);
          }
        }
      });

      this._websocketClient.onMessage('set_parameter', (data: any) => {
        const subdelegate = this.getSubdelegate(0);
        if (subdelegate) {
          const live2DManager = subdelegate.getLive2DManager();
          const model = live2DManager.getModel(0);
          if (model && data.parameters) {
            // 一括設定モード: {"parameters": {"ParamAngleX": 30, "ParamAngleY": -15, ...}}
            let setCount = 0;
            let notFoundCount = 0;
            const ui = LAppUI.getInstance();

            for (const paramName in data.parameters) {
              const paramValue = data.parameters[paramName];
              const paramIndex = model.getParameterIndex(paramName);
              if (paramIndex >= 0) {
                model.setParameterValueByIndex(paramIndex, paramValue);
                // Update UI slider
                if (ui) {
                  ui.updateParameterSlider(paramName, paramValue);
                }
                setCount++;
              } else {
                console.warn('[WebSocket] パラメータが見つかりません:', paramName);
                notFoundCount++;
              }
            }
            console.log(`[WebSocket] パラメータを一括設定しました: ${setCount}個成功, ${notFoundCount}個失敗`);
          }
        }
      });


      console.log('[WebSocket] WebSocketクライアントを初期化しました');
    }
  }

  /**
   * WebSocketクライアントを解放
   */
  private releaseWebSocket(): void {
    if (this._websocketClient) {
      this._websocketClient.disconnect();
      this._websocketClient = null;
      console.log('[WebSocket] WebSocketクライアントを解放しました');
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
