/**
 * WebSocket Controller for Live2D
 * WebSocket経由でLive2Dモデルを操作するコントローラー
 */

import { WebSocketClient, CommandResponse } from './websocketclient';
import * as LAppDefine from './lappdefine';
import {
  CubismLogError,
  CubismLogInfo
} from '@framework/utils/cubismdebug';

/**
 * Live2Dコントローラークラス
 */
class Live2DController {
  private wsClient: WebSocketClient;
  private controlPanel: HTMLElement | null = null;

  constructor() {
    // WebSocketクライアントを初期化
    this.wsClient = new WebSocketClient(LAppDefine.WebSocketUrl + LAppDefine.WebSocketAddress + ":" + LAppDefine.WebSocketPort);

    // メッセージハンドラを登録
    this.setupMessageHandlers();
  }

  /**
   * 初期化
   */
  public async initialize(): Promise<void> {
    // コントロールパネルを取得
    this.controlPanel = document.getElementById('article_controlPanel');
    if (!this.controlPanel) {
      CubismLogError('コントロールパネルが見つかりません');
      return;
    }

    // WebSocket接続
    try {
      await this.wsClient.connect();
      CubismLogInfo('WebSocketサーバーに接続しました');

      // UIを構築
      this.buildUI();

      // 初期データを取得
      this.loadInitialData();
    } catch (error) {
      CubismLogError('WebSocket接続に失敗しました:', error.toString());
      this.showError('WebSocketサーバーに接続できませんでした。');
    }
  }

  /**
   * メッセージハンドラを設定
   */
  private setupMessageHandlers(): void {
    // コマンドレスポンスハンドラ
    this.wsClient.onMessage('command_response', (data) => {
      const response = data as CommandResponse;
      CubismLogInfo('コマンド応答:', response);

      // コマンドに応じた処理
      this.handleCommandResponse(response);
    });

    // エラーハンドラ
    this.wsClient.onMessage('error', (data) => {
      CubismLogError('サーバーエラー:', data);
      this.showError(`サーバーエラー: ${data.message}`);
    });

    // ウェルカムメッセージハンドラ
    this.wsClient.onMessage('welcome', (data) => {
      CubismLogInfo('ウェルカムメッセージ:', data);
      this.showMessage('サーバーに接続されました');
    });
  }

  /**
   * UIを構築
   */
  private buildUI(): void {
    if (!this.controlPanel) return;

    const html = `
      <div class="controller-container">
        <h1>Live2D WebSocket Controller</h1>

        <div class="status-section">
          <h2>接続状態</h2>
          <div id="connection-status">接続中...</div>
        </div>

        <div class="message-section">
          <div id="message-display"></div>
        </div>

        <div class="model-section">
          <h2>モデル操作</h2>
          <button id="btn-get-models">モデル一覧取得</button>
          <button id="btn-get-model-info">モデル情報取得</button>
          <div id="model-info"></div>
        </div>

        <div class="animation-settings-section">
          <h2>アニメーション設定</h2>
          <div style="margin-top: 8px;">
            <label style="display: flex; align-items: center; margin-bottom: 8px; cursor: pointer;">
              <input type="checkbox" id="eyeBlinkToggle" checked style="margin-right: 8px;">
              <span>自動目パチ (Eye Blink)</span>
            </label>
            <label style="display: flex; align-items: center; margin-bottom: 8px; cursor: pointer;">
              <input type="checkbox" id="breathToggle" checked style="margin-right: 8px;">
              <span>呼吸 (Breath)</span>
            </label>
            <label style="display: flex; align-items: center; margin-bottom: 8px; cursor: pointer;">
              <input type="checkbox" id="idleMotionToggle" style="margin-right: 8px;">
              <span>アイドリングモーション (Idle Motion)</span>
            </label>
            <label style="display: flex; align-items: center; cursor: pointer;">
              <input type="checkbox" id="dragFollowToggle" style="margin-right: 8px;">
              <span>ドラッグ追従 (Drag Follow)</span>
            </label>
          </div>
        </div>

        <div class="motion-group-section">
          <h2>モーショングループ</h2>
          <button id="btn-get-motion-groups">モーショングループ一覧</button>
          <button id="btn-get-current-group">現在のグループ取得</button>
          <div id="motion-groups"></div>
          <select id="select-motion-group" style="margin-top: 10px;">
            <option value="">モーショングループを選択...</option>
          </select>
          <button id="btn-set-motion-group">グループ設定</button>
        </div>

        <div class="motion-section">
          <h2>モーション操作</h2>
          <button id="btn-get-motions">モーション一覧</button>
          <button id="btn-get-current-motion">現在のモーション</button>
          <button id="btn-previous-motion">前のモーション</button>
          <button id="btn-next-motion">次のモーション</button>
          <div id="motion-list"></div>
          <select id="select-motion" style="margin-top: 10px;">
            <option value="">モーションを選択...</option>
          </select>
          <button id="btn-set-motion">モーション設定</button>
        </div>

        <div class="custom-command-section">
          <h2>カスタムコマンド</h2>
          <input type="text" id="input-command" placeholder="コマンドを入力..." />
          <input type="text" id="input-args" placeholder="引数（オプション）..." />
          <button id="btn-send-command">送信</button>
        </div>
      </div>
    `;

    this.controlPanel.innerHTML = html;

    // イベントリスナーを設定
    this.setupEventListeners();
  }

  /**
   * イベントリスナーを設定
   */
  private setupEventListeners(): void {
    // アニメーション設定
    document.getElementById('eyeBlinkToggle')?.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.sendModelCommand('set_eye_blink', target.checked ? 'true' : 'false');
    });

    document.getElementById('breathToggle')?.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.sendModelCommand('set_breath', target.checked ? 'true' : 'false');
    });

    document.getElementById('idleMotionToggle')?.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.sendModelCommand('set_idle_motion', target.checked ? 'true' : 'false');
    });

    document.getElementById('dragFollowToggle')?.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      this.sendModelCommand('set_drag_follow', target.checked ? 'true' : 'false');
    });

    // モデル関連
    document.getElementById('btn-get-models')?.addEventListener('click', () => {
      this.sendModelCommand('get_model', '');
    });

    document.getElementById('btn-get-model-info')?.addEventListener('click', () => {
      this.sendModelCommand('get_model_info', '');
    });

    // モーショングループ関連
    document.getElementById('btn-get-motion-groups')?.addEventListener('click', () => {
      this.sendModelCommand('get_motion_groups', '');
    });

    document.getElementById('btn-get-current-group')?.addEventListener('click', () => {
      this.sendModelCommand('get_current_motion_group', '');
    });

    document.getElementById('btn-set-motion-group')?.addEventListener('click', () => {
      const select = document.getElementById('select-motion-group') as HTMLSelectElement;
      if (select && select.value) {
        this.sendModelCommand('set_motion_group', select.value);
      } else {
        this.showError('モーショングループを選択してください');
      }
    });

    // モーション関連
    document.getElementById('btn-get-motions')?.addEventListener('click', () => {
      this.sendModelCommand('get_motions', '');
    });

    document.getElementById('btn-get-current-motion')?.addEventListener('click', () => {
      this.sendModelCommand('get_current_motion', '');
    });

    document.getElementById('btn-previous-motion')?.addEventListener('click', () => {
      this.sendModelCommand('previous_motion', '');
    });

    document.getElementById('btn-next-motion')?.addEventListener('click', () => {
      this.sendModelCommand('next_motion', '');
    });

    document.getElementById('btn-set-motion')?.addEventListener('click', () => {
      const select = document.getElementById('select-motion') as HTMLSelectElement;
      if (select && select.value) {
        this.sendModelCommand('set_motion_index', select.value);
      } else {
        this.showError('モーションを選択してください');
      }
    });

    // カスタムコマンド
    document.getElementById('btn-send-command')?.addEventListener('click', () => {
      const cmdInput = document.getElementById('input-command') as HTMLInputElement;
      const argsInput = document.getElementById('input-args') as HTMLInputElement;
      if (cmdInput && cmdInput.value) {
        this.sendModelCommand(cmdInput.value, argsInput?.value || '');
      }
    });
  }

  /**
   * モデルコマンドを送信
   */
  private sendModelCommand(command: string, args: string): void {
    this.wsClient.sendCustomMessage('model_command', {
      command: command,
      args: args
    });
    this.showMessage(`コマンド送信: ${command} ${args}`);
  }

  /**
   * コマンドレスポンスを処理
   */
  private handleCommandResponse(response: CommandResponse): void {
    if (response.error) {
      this.showError(`エラー: ${response.error}`);
      return;
    }

    // コマンドごとの処理
    switch (response.command) {
      case 'get_model':
        this.displayModelInfo(response.data);
        break;
      case 'get_model_info':
        this.displayDetailedModelInfo(response.data);
        break;
      case 'get_motion_groups':
        this.displayMotionGroups(response.data);
        break;
      case 'get_current_motion_group':
        this.displayCurrentMotionGroup(response.data);
        break;
      case 'set_motion_group':
        this.showMessage(`モーショングループを設定しました: ${response.data?.motion_group}`);
        break;
      case 'get_motions':
        this.displayMotions(response.data);
        break;
      case 'get_current_motion':
        this.displayCurrentMotion(response.data);
        break;
      case 'set_motion_index':
        this.showMessage(`モーションを設定しました: ${response.data?.motion}`);
        break;
      case 'next_motion':
      case 'previous_motion':
        this.displayCurrentMotion(response.data);
        break;
      default:
        CubismLogInfo('未処理のコマンド:', response.command, response.data);
    }
  }

  /**
   * モデル情報を表示
   */
  private displayModelInfo(data: any): void {
    const element = document.getElementById('model-info');
    if (!element) return;

    element.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  }

  /**
   * 詳細なモデル情報を表示
   */
  private displayDetailedModelInfo(data: any): void {
    const element = document.getElementById('model-info');
    if (!element) return;

    element.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  }

  /**
   * モーショングループ一覧を表示
   */
  private displayMotionGroups(data: any): void {
    const element = document.getElementById('motion-groups');
    const select = document.getElementById('select-motion-group') as HTMLSelectElement;

    if (!element) return;

    element.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;

    // セレクトボックスを更新
    if (select && Array.isArray(data)) {
      select.innerHTML = '<option value="">モーショングループを選択...</option>';
      data.forEach((group: string) => {
        const option = document.createElement('option');
        option.value = group;
        option.textContent = group;
        select.appendChild(option);
      });
    }
  }

  /**
   * 現在のモーショングループを表示
   */
  private displayCurrentMotionGroup(data: any): void {
    this.showMessage(`現在のモーショングループ: ${data}`);
  }

  /**
   * モーション一覧を表示
   */
  private displayMotions(data: any): void {
    const element = document.getElementById('motion-list');
    const select = document.getElementById('select-motion') as HTMLSelectElement;

    if (!element) return;

    element.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;

    // セレクトボックスを更新
    if (select && data.motions && Array.isArray(data.motions)) {
      select.innerHTML = '<option value="">モーションを選択...</option>';
      data.motions.forEach((motion: any, index: number) => {
        const option = document.createElement('option');
        option.value = index.toString();
        option.textContent = typeof motion === 'string' ? motion : `Motion ${index}`;
        select.appendChild(option);
      });
    }
  }

  /**
   * 現在のモーションを表示
   */
  private displayCurrentMotion(data: any): void {
    this.showMessage(`現在のモーション: ${JSON.stringify(data)}`);
  }

  /**
   * 初期データを読み込み
   */
  private loadInitialData(): void {
    // モーショングループ一覧を取得
    this.sendModelCommand('get_motion_groups', '');

    // モデル情報を取得
    this.sendModelCommand('get_model', '');
  }

  /**
   * メッセージを表示
   */
  private showMessage(message: string): void {
    const element = document.getElementById('message-display');
    if (element) {
      const time = new Date().toLocaleTimeString();
      element.innerHTML = `<div class="message">[${time}] ${message}</div>` + element.innerHTML;

      // 最大10件まで表示
      const messages = element.querySelectorAll('.message');
      if (messages.length > 10) {
        messages[messages.length - 1].remove();
      }
    }
  }

  /**
   * エラーを表示
   */
  private showError(message: string): void {
    const element = document.getElementById('message-display');
    if (element) {
      const time = new Date().toLocaleTimeString();
      element.innerHTML = `<div class="error">[${time}] ${message}</div>` + element.innerHTML;

      // 最大10件まで表示
      const messages = element.querySelectorAll('.message, .error');
      if (messages.length > 10) {
        messages[messages.length - 1].remove();
      }
    }
  }

  /**
   * クリーンアップ
   */
  public dispose(): void {
    this.wsClient.disconnect();
  }
}

// グローバルインスタンス
let controller: Live2DController | null = null;

/**
 * ブラウザロード後の処理
 */
window.addEventListener('load', async (): Promise<void> => {
  controller = new Live2DController();
  await controller.initialize();
}, { passive: true });

/**
 * 終了時の処理
 */
window.addEventListener('beforeunload', (): void => {
  if (controller) {
    controller.dispose();
    controller = null;
  }
}, { passive: true });
