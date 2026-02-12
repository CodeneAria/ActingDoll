/**
 * WebSocket Controller for Live2D
 * WebSocket経由でLive2Dモデルを操作するコントローラー
 */

import { WebSocketClient, CommandResponse } from './websocketclient';
import * as LAppDefine from './lappdefine';
import { CubismLogError, CubismLogInfo } from '@framework/utils/cubismdebug';
import { LAppMultilingual, MessageKey } from './lappmultilingual';
import { LAppPal } from './lapppal';

/**
 * Live2Dコントローラークラス
 */
class Live2DController {
  private wsClient: WebSocketClient;
  private controlPanel: HTMLElement | null = null;
  private clients: string[] = [];
  private models: string[] = [];
  private expressions: string[] = [];
  private motions: { [key: string]: any[] } = {};
  private parameters: Array<{ Id: string; Name: string }> = [];
  private selectedClientId: string = '';
  private selectedModel: string = '';
  private myClientId: string = '';

  constructor() {
    // WebSocketクライアントを初期化
    this.wsClient = new WebSocketClient(LAppDefine.WebSocketUrl + location.hostname + ':' + LAppDefine.WebSocketPort);

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
      CubismLogError(LAppMultilingual.getMessage(MessageKey.CTRL_PANEL_NOT_FOUND));
      return;
    }

    // WebSocket接続
    try {
      await this.wsClient.connect();
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.CTRL_WS_CONNECTED));

      // UIを構築
      this.buildUI();

      // 初期データを取得
      this.loadInitialData();
    } catch (error) {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.CTRL_WS_FAILED, error.toString()));
      this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_WS_FAILED_SHOW, error.toString()));
    }
  }

  /**
   * メッセージハンドラを設定
   */
  private setupMessageHandlers(): void {
    // メッセージハンドラを登録
    this.wsClient.onMessage('server_heartbeat', (data) => {
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.SERVER_HEARTBEAT, data.timestamp || 'unknown'));
    });
    // コマンドレスポンスハンドラ
    this.wsClient.onMessage('command_response', (data) => {
      const response = data as CommandResponse;
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.CTRL_CMD_RESPONSE, response));

      // コマンドに応じた処理
      this.handleCommandResponse(response);
    });

    // エラーハンドラ
    this.wsClient.onMessage('error', (data) => {
      CubismLogError(LAppMultilingual.getMessage(MessageKey.CTRL_SERVER_ERROR, data));
      this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SERVER_ERROR, `${data.message}`));
    });

    // ウェルカムメッセージハンドラ
    this.wsClient.onMessage('welcome', (data) => {
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.CTRL_WELCOME_MSG, data));
      this.showMessage(LAppMultilingual.getMessage(MessageKey.CTRL_SERVER_CONNECTED));
      // クライアントIDを保存して表示
      if (data.client_id) {
        this.myClientId = data.client_id;
        this.updateConnectionStatus();
      }
    });

    // 認証成功ハンドラ
    this.wsClient.onMessage('auth_success', (data) => {
      CubismLogInfo('認証成功: ' + JSON.stringify(data));
      this.showMessage('認証に成功しました');
      this.updateAuthStatus(true);
    });

    // 認証失敗ハンドラ
    this.wsClient.onMessage('auth_failed', (data) => {
      CubismLogError('認証失敗: ' + JSON.stringify(data));
      this.showError('認証に失敗しました: ' + (data.message || '不明なエラー'));
      this.updateAuthStatus(false);
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
    <div id="connection-status">接続済み</div>
    <div id="my-client-id" style="margin-top: 5px; font-size: 0.9em; color: #666;">クライアントID: 取得中...</div>
  </div>

  <div class="message-section">
    <div id="message-display"></div>
  </div>

  <h2>認証</h2>
  <div class="auth-section">
    <div id="auth-status" style="padding: 10px; margin-bottom: 10px; border-radius: 5px; background-color: #f0f0f0;">
      認証状態: <span id="auth-status-text" style="font-weight: bold;">未認証</span>
    </div>
    <div style="margin-top: 10px;">
      <input type="password" id="input-auth-token" placeholder="認証トークン" style="width: 300px;" />
      <button id="btn-authenticate">認証 (auth)</button>
    </div>
    <div style="margin-top: 5px; font-size: 0.9em; color: #666;">
      ※ set_lipsync_from_file コマンドを使用するには認証が必要です
    </div>
  </div>

  <h2>基本コマンド</h2>
  <div class="basic-commands-section">
    <div style="margin-top: 10px;">
      <input type="text" id="input-notify" placeholder="通知メッセージ" style="width: 300px;" />
      <button id="btn-notify">通知送信 (notify)</button>
    </div>
    <div>
      <button id="btn-model-list">モデル一覧取得 (model list)</button>
    </div>
  </div>

  <h2>クライアント制御</h2>
  <div class="client-selection-section">
    <h3>基本</h3>
    <select id="select-client" style="width: 300px;">
      <option value="">クライアントを選択...</option>
    </select>
    <button id="btn-list">クライアント一覧取得 (list)</button>
    <div style="margin-top: 10px;">
      <input type="text" id="input-send-message" placeholder="メッセージ" style="width: 200px;" />
      <button id="btn-send">メッセージ送信 (send)</button>
    </div>
    <div class="model-section">
      <h3>モデル操作</h3>
      <button id="btn-client-get-model">モデル取得 (get_model_name)</button>
      <select id="select-model" style="width: 300px; margin-left: 10px;">
        <option value="">モデルを選択...</option>
      </select>
    </div>
    <div class="expression-section">
      <h3>表情操作</h3>
      <button id="btn-model-expressions">表情一覧取得 (get_expressions)</button>
      <button id="btn-get-expression">現在の表情取得 (get_expression)</button>
      <div style="margin-top: 10px;">
        <select id="select-expression" style="width: 300px;">
          <option value="">表情を選択...</option>
        </select>
        <button id="btn-set-expression">表情設定</button>
      </div>
    </div>
    <div class="motion-section">
      <h3>モーション操作</h3>
      <button id="btn-model-motions">モーション一覧取得 (get_motions)</button>
      <button id="btn-get-motion">現在のモーション取得</button>
      <div style="margin-top: 10px;">
        <select id="select-motion-group" style="width: 200px;">
          <option value="">グループを選択...</option>
        </select>
        <select id="select-motion-no" style="width: 100px;">
          <option value="">番号...</option>
        </select>
        <select id="select-motion-priority" style="width: 150px;">
          <option value="0">None(0)</option>
          <option value="1">Idle(1)</option>
          <option value="2" selected>Normal(2)</option>
          <option value="3">Force(3)</option>
        </select>
        <button id="btn-set-motion">モーション設定</button>
      </div>
    </div>
    <div class="client-commands-section">
      <h3>アニメーション設定</h3>
      <div style="margin-top: 8px;">
        <h4>目パチ(get_eye_blink/set_eye_blink)</h4>
        <button id="btn-get-eye-blink">状態取得</button>
        <button id="btn-set-eye-blink-enabled">有効</button>
        <button id="btn-set-eye-blink-disabled">無効</button>
      </div>
      <div style="margin-top: 8px;">
        <h4>呼吸(get_breath/set_breath)</h4>
        <button id="btn-get-breath">状態取得</button>
        <button id="btn-set-breath-enabled">有効</button>
        <button id="btn-set-breath-disabled">無効</button>
      </div>
      <div style="margin-top: 8px;">
        <h4>アイドリングモーション(get_idle_motion/set_idle_motion)</h4>
        <button id="btn-get-idle-motion">状態取得</button>
        <button id="btn-set-idle-motion-enabled">有効</button>
        <button id="btn-set-idle-motion-disabled">無効</button>
      </div>
      <div style="margin-top: 8px;">
        <h4>ドラッグ追従(get_drag_follow/set_drag_follow)</h4>
        <button id="btn-get-drag-follow">状態取得</button>
        <button id="btn-set-drag-follow-enabled">有効</button>
        <button id="btn-set-drag-follow-disabled">無効</button>
      </div>
      <div style="margin-top: 8px;">
        <h4>物理演算(get_physics/set_physics)</h4>
        <button id="btn-get-physics">状態取得</button>
        <button id="btn-set-physics-enabled">有効</button>
        <button id="btn-set-physics-disabled">無効</button>
      </div>
    </div>
    <div class="parameter-section">
      <h3>パラメータ操作</h3>
      <button id="btn-model-parameters">パラメータ一覧取得 (get_parameters)</button>
      <div id="parameter-list" style="margin-top: 10px; max-height: 300px; overflow-y: auto;"></div>
      <button id="btn-set-parameters" style="margin-top: 10px;">パラメータ設定</button>
    </div>
    <div class="lipsync-section">
      <h3>リップシンク</h3>
      <div style="margin-top: 10px;">
        <input type="file" id="input-wav-file" accept=".wav" style="width: 300px;" />
        <button id="btn-send-wav">Wavファイル送信</button>
      </div>
    </div>
    <div class="transform-section">
      <h3>位置・スケール操作</h3>
      <div style="margin-top: 10px;">
        <button id="btn-get-position">位置取得 (get_position)</button>
        <div style="margin-top: 10px;">
          <input type="number" id="input-position-x" placeholder="X座標" step="0.1" style="width: 100px;" value="0" />
          <input type="number" id="input-position-y" placeholder="Y座標" step="0.1" style="width: 100px;" value="0" />
          <label style="margin-left: 10px;">
            <input type="checkbox" id="checkbox-position-relative" />
            相対移動
          </label>
          <button id="btn-set-position">位置設定 (set_position)</button>
        </div>
      </div>
      <div style="margin-top: 10px;">
        <button id="btn-get-scale">スケール取得 (get_scale)</button>
        <div style="margin-top: 10px;">
          <input type="number" id="input-scale" placeholder="スケール" step="0.1" min="0.1" max="3.0" style="width: 100px;" value="1.0" />
          <button id="btn-set-scale">スケール設定 (set_scale)</button>
        </div>
      </div>
    </div>
    <div class="custom-command-section" hidden>
      <h3>カスタムコマンド</h3>
      <input type="text" id="input-command" placeholder="コマンドを入力..." style="width: 500px;" />
      <button id="btn-send-command">送信</button>
    </div>
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
    // 認証ボタン
    document.getElementById('btn-authenticate')?.addEventListener('click', () => {
      const input = document.getElementById('input-auth-token') as HTMLInputElement;
      if (input && input.value) {
        this.authenticate(input.value);
      } else {
        this.showError('認証トークンを入力してください');
      }
    });

    // 基本コマンド
    document.getElementById('btn-list')?.addEventListener('click', () => {
      this.sendCommand('list');
    });

    document.getElementById('btn-notify')?.addEventListener('click', () => {
      const input = document.getElementById('input-notify') as HTMLInputElement;
      if (input && input.value) {
        this.sendCommand(`notify ${input.value}`);
      }
    });

    document.getElementById('btn-send')?.addEventListener('click', () => {
      const input = document.getElementById('input-send-message') as HTMLInputElement;
      if (input && input.value && this.selectedClientId) {
        this.sendCommand(`send ${this.selectedClientId} ${input.value}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT_AND_MESSAGE));
      }
    });

    document.getElementById('select-client')?.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      this.selectedClientId = target.value;
      this.showMessage(`クライアント選択: ${this.selectedClientId}`);
      this.updateModelName();
    });

    // モデル関連
    document.getElementById('btn-model-list')?.addEventListener('click', () => {
      this.sendCommand('model list');
    });

    document.getElementById('select-model')?.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      this.selectedModel = target.value;
      this.showMessage(`モデル選択: ${this.selectedModel}`);
      if ('' !== this.selectedModel) {
        this.sendCommand(`model get_expressions ${this.selectedModel}`);
        this.sendCommand(`model get_motions ${this.selectedModel}`);
        this.sendCommand(`model get_parameters ${this.selectedModel}`);
      }
    });

    document.getElementById('btn-model-expressions')?.addEventListener('click', () => {
      if (this.selectedModel) {
        this.sendCommand(`model get_expressions ${this.selectedModel}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_MODEL));
      }
    });

    document.getElementById('btn-model-motions')?.addEventListener('click', () => {
      if (this.selectedModel) {
        this.sendCommand(`model get_motions ${this.selectedModel}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_MODEL));
      }
    });

    document.getElementById('btn-model-parameters')?.addEventListener('click', () => {
      if (this.selectedModel) {
        this.sendCommand(`model get_parameters ${this.selectedModel}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_MODEL));
      }
    });

    // クライアントコマンド - モデル取得
    document.getElementById('btn-client-get-model')?.addEventListener('click', () => {
      if (this.selectedClientId) {
        this.sendCommand(`client ${this.selectedClientId} get_model_name`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
      }
    });

    // アニメーション設定
    this.setupAnimationButtons();

    // 表情操作
    document.getElementById('btn-get-expression')?.addEventListener('click', () => {
      if (this.selectedClientId) {
        this.sendCommand(`client ${this.selectedClientId} get_expression`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
      }
    });

    document.getElementById('btn-set-expression')?.addEventListener('click', () => {
      const select = document.getElementById('select-expression') as HTMLSelectElement;
      if (this.selectedClientId && select && select.value) {
        this.sendCommand(`client ${this.selectedClientId} set_expression ${select.value}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT_AND_EXPRESSION));
      }
    });

    // モーション操作
    document.getElementById('btn-get-motion')?.addEventListener('click', () => {
      if (this.selectedClientId) {
        this.sendCommand(`client ${this.selectedClientId} get_motion`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
      }
    });

    document.getElementById('btn-set-motion')?.addEventListener('click', () => {
      const groupSelect = document.getElementById('select-motion-group') as HTMLSelectElement;
      const noSelect = document.getElementById('select-motion-no') as HTMLSelectElement;
      const prioritySelect = document.getElementById('select-motion-priority') as HTMLSelectElement;
      if (this.selectedClientId && groupSelect && groupSelect.value && noSelect && noSelect.value) {
        const priority = prioritySelect && prioritySelect.value ? prioritySelect.value : '2';
        this.sendCommand(`client ${this.selectedClientId} set_motion ${groupSelect.value} ${noSelect.value} ${priority}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT_GROUP_NUMBER));
      }
    });

    // パラメータ設定
    document.getElementById('btn-set-parameters')?.addEventListener('click', () => {
      if (!this.selectedClientId) {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        return;
      }

      const params: string[] = [];
      this.parameters.forEach((param, index) => {
        const input = document.getElementById(`param-value-${index}`) as HTMLInputElement;
        if (input && input.value) {
          params.push(`${param.Id}=${input.value}`);
        }
      });

      if (params.length > 0) {
        this.sendCommand(`client ${this.selectedClientId} set_parameter ${params.join(' ')}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_ENTER_PARAMETER_VALUES));
      }
    });

    // Wavファイル送信
    document.getElementById('btn-send-wav')?.addEventListener('click', async () => {
      const fileInput = document.getElementById('input-wav-file') as HTMLInputElement;
      if (!this.selectedClientId) {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        return;
      }
      if (fileInput && fileInput.files && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target && e.target.result) {
            const arrayBuffer = e.target.result as ArrayBuffer;
            const bytes = new Uint8Array(arrayBuffer);
            let binary = '';
            for (let i = 0; i < bytes.byteLength; i++) {
              binary += String.fromCharCode(bytes[i]);
            }
            const base64 = btoa(binary);
            this.sendCommand(`client ${this.selectedClientId} set_lipsync ${base64}`);
            this.showMessage(`Wavファイル送信: ${file.name}`);
          }
        };
        reader.readAsArrayBuffer(file);
      } else {
        this.showError('Wavファイルを選択してください');
      }
    });

    // 位置・スケール操作
    document.getElementById('btn-get-position')?.addEventListener('click', () => {
      if (!this.selectedClientId) {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        return;
      }
      this.sendCommand(`client ${this.selectedClientId} get_position`);
    });

    document.getElementById('btn-set-position')?.addEventListener('click', () => {
      if (!this.selectedClientId) {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        return;
      }
      const xInput = document.getElementById('input-position-x') as HTMLInputElement;
      const yInput = document.getElementById('input-position-y') as HTMLInputElement;
      const relativeCheckbox = document.getElementById('checkbox-position-relative') as HTMLInputElement;
      if (xInput && yInput && xInput.value && yInput.value) {
        const relativeOption = relativeCheckbox && relativeCheckbox.checked ? ' relative' : '';
        this.sendCommand(`client ${this.selectedClientId} set_position ${xInput.value} ${yInput.value}${relativeOption}`);
      } else {
        this.showError('X座標とY座標を入力してください');
      }
    });

    document.getElementById('btn-get-scale')?.addEventListener('click', () => {
      if (!this.selectedClientId) {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        return;
      }
      this.sendCommand(`client ${this.selectedClientId} get_scale`);
    });

    document.getElementById('btn-set-scale')?.addEventListener('click', () => {
      if (!this.selectedClientId) {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        return;
      }
      const scaleInput = document.getElementById('input-scale') as HTMLInputElement;
      if (scaleInput && scaleInput.value) {
        this.sendCommand(`client ${this.selectedClientId} set_scale ${scaleInput.value}`);
      } else {
        this.showError('スケール値を入力してください');
      }
    });

    // カスタムコマンド
    document.getElementById('btn-send-command')?.addEventListener('click', () => {
      const cmdInput = document.getElementById('input-command') as HTMLInputElement;
      if (cmdInput && cmdInput.value) {
        this.sendCommand(cmdInput.value);
      }
    });
  }

  /**
   * アニメーション設定ボタンをセットアップ
   */
  private setupAnimationButtons(): void {
    const commands = [
      { get: 'btn-get-eye-blink', enable: 'btn-set-eye-blink-enabled', disable: 'btn-set-eye-blink-disabled', name: 'eye_blink' },
      { get: 'btn-get-breath', enable: 'btn-set-breath-enabled', disable: 'btn-set-breath-disabled', name: 'breath' },
      { get: 'btn-get-idle-motion', enable: 'btn-set-idle-motion-enabled', disable: 'btn-set-idle-motion-disabled', name: 'idle_motion' },
      { get: 'btn-get-drag-follow', enable: 'btn-set-drag-follow-enabled', disable: 'btn-set-drag-follow-disabled', name: 'drag_follow' },
      { get: 'btn-get-physics', enable: 'btn-set-physics-enabled', disable: 'btn-set-physics-disabled', name: 'physics' }
    ];

    commands.forEach(cmd => {
      document.getElementById(cmd.get)?.addEventListener('click', () => {
        if (this.selectedClientId) {
          this.sendCommand(`client ${this.selectedClientId} get_${cmd.name}`);
        } else {
          this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        }
      });

      document.getElementById(cmd.enable)?.addEventListener('click', () => {
        if (this.selectedClientId) {
          this.sendCommand(`client ${this.selectedClientId} set_${cmd.name} enabled`);
        } else {
          this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        }
      });

      document.getElementById(cmd.disable)?.addEventListener('click', () => {
        if (this.selectedClientId) {
          this.sendCommand(`client ${this.selectedClientId} set_${cmd.name} disabled`);
        } else {
          this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SELECT_CLIENT));
        }
      });
    });
  }

  /**
   * コマンドを送信
   */
  private sendCommand(command: string): void {
    this.wsClient.sendCommand(command);
    this.showMessage(`コマンド送信: ${command}`);
  }

  /**
   * 認証を実行
   */
  private authenticate(token: string): void {
    this.wsClient.sendAuth(token);
    this.showMessage('認証を試行中...');
  }

  /**
   * 認証状態を更新
   */
  private updateAuthStatus(authenticated: boolean): void {
    const statusText = document.getElementById('auth-status-text');
    const statusDiv = document.getElementById('auth-status');
    if (statusText && statusDiv) {
      if (authenticated) {
        statusText.textContent = '認証済み';
        statusDiv.style.backgroundColor = '#d4edda';
        statusDiv.style.color = '#155724';
      } else {
        statusText.textContent = '未認証';
        statusDiv.style.backgroundColor = '#f8d7da';
        statusDiv.style.color = '#721c24';
      }
    }
  }

  /**
   * 接続状態を更新
   */
  private updateConnectionStatus(): void {
    const element = document.getElementById('my-client-id');
    if (element && this.myClientId) {
      element.textContent = `クライアントID: ${this.myClientId}`;
    }
  }

  /**
   * コマンドレスポンスを処理
   */
  private handleCommandResponse(response: CommandResponse): void {
    if (response.error) {
      this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_ERROR, response.error));
      return;
    }

    const command = response.command || '応答';
    const client_id = response.client_id || 'unknown';
    const data = response.data || {};
    if (JSON.stringify(data).length > 2) {
      this.showMessage(`[${client_id}] ${command}: ${JSON.stringify(data)}`);
    } else {
      this.showMessage(`受信: ${JSON.stringify(response)}`);
    }

    // listコマンドの応答
    if (command === 'list' && data.clients) {
      this.updateClientList(data.clients);
    }

    // model listの応答
    if (command === 'model') {
      const subcommand = response.sub || '';
      if (subcommand === 'list') {
        this.updateModelList(data);
      } else if (subcommand === 'get_expressions') {
        this.updateExpressionList(data);
      } else if (subcommand === 'get_motions') {
        this.updateMotionList(data);
      } else if (subcommand === 'get_parameters') {
        this.updateParameterList(data);
      } else if (subcommand === 'get_model_name') {
        this.selectModel(data.model || '');
      }
    } else if (command === 'response_model_name') {
      this.selectModel(data.model_name || '');
    } else {
      // TODO:他の応答コマンドの処理を記載する必要がある
      // 主にmodel get_系コマンドの応答を処理する
    }
  }

  /**
   * クライアントリストを更新
   */
  private updateClientList(clients: string[]): void {
    this.clients = clients;
    const select = document.getElementById('select-client') as HTMLSelectElement;
    if (!select) return;

    select.innerHTML = '<option value="">クライアントを選択...</option>';
    clients.forEach((clientId: string) => {
      const option = document.createElement('option');
      option.value = clientId;
      option.textContent = clientId;
      select.appendChild(option);
    });

    // 自動選択
    if (clients.length > 0 && !this.selectedClientId) {
      this.selectedClientId = clients[0];
      select.value = clients[0];
      this.showMessage(`クライアント自動選択: ${clients[0]}`);
      this.updateModelName();
    }
  }
  private selectModel(modelName: string): void {
    if ('' === modelName) { return; }
    const select = document.getElementById('select-model') as HTMLSelectElement;
    if (select) {
      select.value = modelName;
      this.selectedModel = modelName;
      this.showMessage(`モデル選択: ${modelName}`);
    }
    this.sendCommand(`model get_expressions ${modelName}`);
    this.sendCommand(`model get_motions ${modelName}`);
    this.sendCommand(`model get_parameters ${modelName}`);
  }

  /**
   * モデルリストを更新
   */
  private updateModelList(models: string[]): void {
    this.models = models;
    const select = document.getElementById('select-model') as HTMLSelectElement;
    if (!select) return;
    select.disabled = true;
    select.innerHTML = '<option value="">モデルを選択...</option>';
    models.forEach((model: string) => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      select.appendChild(option);
    });
  }

  /**
   * 表情リストを更新
   */
  private updateExpressionList(data: any): void {
    this.expressions = data.expressions || [];
    const select = document.getElementById('select-expression') as HTMLSelectElement;
    if (!select) return;

    select.innerHTML = '<option value="">表情を選択...</option>';
    this.expressions.forEach((expr: any) => {
      if ('' === expr.Name) { return; }
      const option = document.createElement('option');
      option.value = expr.Name || '';
      option.textContent = expr.File || '';
      select.appendChild(option);
    });
  }

  /**
   * モーションリストを更新
   */
  private updateMotionList(data: any): void {
    this.motions = data.motions || {};
    const groupSelect = document.getElementById('select-motion-group') as HTMLSelectElement;
    const noSelect = document.getElementById('select-motion-no') as HTMLSelectElement;

    if (groupSelect) {
      groupSelect.innerHTML = '<option value="">グループを選択...</option>';
      Object.keys(this.motions).forEach((group: string) => {
        const option = document.createElement('option');
        option.value = group;
        option.textContent = group.toString() + ` (` + this.motions[group].length + `件)`;
        groupSelect.appendChild(option);
      });

      // グループ選択時に番号を更新
      groupSelect.addEventListener('change', (e) => {
        const target = e.target as HTMLSelectElement;
        if (noSelect && target.value && this.motions[target.value]) {
          noSelect.innerHTML = '<option value="">番号...</option>';
          const count = this.motions[target.value].length;
          for (let i = 0; i < count; i++) {
            const option = document.createElement('option');
            option.value = i.toString();
            option.textContent = this.motions[target.value][i]?.File || i.toString();
            noSelect.appendChild(option);
          }
        }
      });
    }

    if (noSelect) {
      noSelect.innerHTML = '<option value="">番号...</option>';
      // 最初のグループがあれば、その数だけ番号を生成
      const firstGroup = Object.keys(this.motions)[0];
      if (firstGroup) {
        const count = this.motions[firstGroup].length;
        for (let i = 0; i < count; i++) {
          const option = document.createElement('option');
          option.value = i.toString();
          option.textContent = this.motions[firstGroup][i]?.File || i.toString();
          noSelect.appendChild(option);
        }
      }
    }
  }

  /**
   * パラメータリストを更新
   */
  private updateParameterList(data: any): void {
    this.parameters = data.parameters || [];
    const element = document.getElementById('parameter-list');
    if (!element) return;

    const elm_div = document.createElement('div');
    elm_div.style.display = 'grid';
    elm_div.style.gridTemplateColumns = '1fr 1fr 1fr';
    elm_div.style.gap = '5px';
    this.parameters.forEach((param, index) => {
      const item_div = document.createElement('div');
      item_div.style.display = 'flex';
      item_div.style.alignItems = 'center';
      item_div.style.gap = '5px';
      const item_label = document.createElement('label');
      item_label.style.fontSize = '12px';
      item_label.style.minWidth = '120px';
      item_label.textContent = `${param.Name}:`;
      const item_input = document.createElement('input');
      item_input.type = 'number';
      item_input.id = `param-value-${index}`;
      item_input.value = `${param.Id}`;
      item_input.step = '0.1';
      item_input.style.width = '80px';
      item_input.style.padding = '2px';
      item_div.appendChild(item_label);
      item_div.appendChild(item_input);
      elm_div.appendChild(item_div);
    });
    element.innerHTML = elm_div.outerHTML;
  }

  /**
   * モデル情報を更新
   */
  private updateModelName(): void {
    if (this.selectedClientId) {
      this.sendCommand(`client ${this.selectedClientId} get_model_name`);
    }
  }

  /**
   * 初期データを読み込み
   */
  private loadInitialData(): void {
    // クライアント一覧を取得
    this.sendCommand('list');
    // モデル一覧を取得
    this.sendCommand('model list');
  }

  /**
   * メッセージを表示
   */
  private showMessage(message: string): void {
    LAppPal.printMessage(message);
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
    LAppPal.printErrorMessage(message);
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
