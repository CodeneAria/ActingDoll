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
import { LAppMultilingual, MessageKey } from './lappmultilingual';

/**
 * Live2Dコントローラークラス
 */
class Live2DController {
  private wsClient: WebSocketClient;
  private controlPanel: HTMLElement | null = null;
  private clients: string[] = [];
  private models: string[] = [];
  private expressions: string[] = [];
  private motions: { [key: string]: number } = {};
  private parameters: Array<{ id: string; value: number }> = [];
  private selectedClientId: string = '';
  private selectedModel: string = '';

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
      this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_SERVER_ERROR, `${ data.message }`));
    });

    // ウェルカムメッセージハンドラ
    this.wsClient.onMessage('welcome', (data) => {
      CubismLogInfo(LAppMultilingual.getMessage(MessageKey.CTRL_WELCOME_MSG, data));
      this.showMessage(LAppMultilingual.getMessage(MessageKey.CTRL_SERVER_CONNECTED));
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
        </div>

        <div class="message-section">
          <div id="message-display"></div>
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
          <h2>クライアント選択</h2>
          <select id="select-client" style="width: 300px;">
            <option value="">クライアントを選択...</option>
          </select>
          <button id="btn-list">クライアント一覧取得 (list)</button>
        </div>

        <div class="model-section">
          <div style="margin-top: 10px;">
            <input type="text" id="input-send-message" placeholder="メッセージ" style="width: 200px;" />
            <button id="btn-send">メッセージ送信 (send)</button>
          </div>
          <h2>モデル操作</h2>
          <button id="btn-client-get-model">モデル取得 (get_model)</button>
          <select id="select-model" style="width: 300px; margin-left: 10px;">
            <option value="">モデルを選択...</option>
          </select>
          <div style="margin-top: 10px;">
            <button id="btn-model-expressions">表情一覧取得</button>
            <button id="btn-model-motions">モーション一覧取得</button>
            <button id="btn-model-parameters">パラメータ一覧取得</button>
          </div>
          <div id="model-info" style="margin-top: 10px;"></div>
        </div>

        <div class="client-commands-section">

          <h3 style="margin-top: 15px;">アニメーション設定</h3>
          <div style="margin-top: 8px;">
            <button id="btn-get-eye-blink">目パチ/状態取得</button>
            <button id="btn-set-eye-blink-enabled">目パチ/有効</button>
            <button id="btn-set-eye-blink-disabled">目パチ/無効</button>
          </div>
          <div style="margin-top: 8px;">
            <button id="btn-get-breath">呼吸/状態取得</button>
            <button id="btn-set-breath-enabled">呼吸/有効</button>
            <button id="btn-set-breath-disabled">呼吸/無効</button>
          </div>
          <div style="margin-top: 8px;">
            <button id="btn-get-idle-motion">アイドリングモーション/状態取得</button>
            <button id="btn-set-idle-motion-enabled">アイドリングモーション/有効</button>
            <button id="btn-set-idle-motion-disabled">アイドリングモーション/無効</button>
          </div>
          <div style="margin-top: 8px;">
            <button id="btn-get-drag-follow">ドラッグ追従/状態取得</button>
            <button id="btn-set-drag-follow-enabled">ドラッグ追従/有効</button>
            <button id="btn-set-drag-follow-disabled">ドラッグ追従/無効</button>
          </div>
          <div style="margin-top: 8px;">
            <button id="btn-get-physics">物理演算/状態取得</button>
            <button id="btn-set-physics-enabled">物理演算/有効</button>
            <button id="btn-set-physics-disabled">物理演算/無効</button>
          </div>
        </div>

        <div class="expression-section">
          <h2>表情操作</h2>
          <button id="btn-get-expression">現在の表情取得</button>
          <div style="margin-top: 10px;">
            <select id="select-expression" style="width: 300px;">
              <option value="">表情を選択...</option>
            </select>
            <button id="btn-set-expression">表情設定</button>
          </div>
        </div>

        <div class="motion-section">
          <h2>モーション操作</h2>
          <button id="btn-get-motion">現在のモーション取得</button>
          <div style="margin-top: 10px;">
            <select id="select-motion-group" style="width: 200px;">
              <option value="">グループを選択...</option>
            </select>
            <select id="select-motion-no" style="width: 100px;">
              <option value="">番号...</option>
            </select>
            <button id="btn-set-motion">モーション設定</button>
          </div>
        </div>

        <div class="parameter-section">
          <h2>パラメータ操作</h2>
          <div id="parameter-list" style="margin-top: 10px; max-height: 300px; overflow-y: auto;"></div>
          <button id="btn-set-parameters" style="margin-top: 10px;">パラメータ設定</button>
        </div>

        <div class="custom-command-section">
          <h2>カスタムコマンド</h2>
          <input type="text" id="input-command" placeholder="コマンドを入力..." style="width: 500px;" />
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
    });

    // モデル関連
    document.getElementById('btn-model-list')?.addEventListener('click', () => {
      this.sendCommand('model list');
    });

    document.getElementById('select-model')?.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      this.selectedModel = target.value;
      this.showMessage(`モデル選択: ${this.selectedModel}`);
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
        this.sendCommand(`client ${this.selectedClientId} get_model`);
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
      if (this.selectedClientId && groupSelect && groupSelect.value && noSelect && noSelect.value) {
        this.sendCommand(`client ${this.selectedClientId} set_motion ${groupSelect.value} ${noSelect.value}`);
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
          params.push(`${param.id}=${input.value}`);
        }
      });

      if (params.length > 0) {
        this.sendCommand(`client ${this.selectedClientId} set_parameter ${params.join(' ')}`);
      } else {
        this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_ENTER_PARAMETER_VALUES));
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
   * コマンドレスポンスを処理
   */
  private handleCommandResponse(response: CommandResponse): void {
    if (response.error) {
      this.showError(LAppMultilingual.getMessage(MessageKey.CTRL_ERROR, response.error));
      return;
    }

    const data = response.data || {};
    this.showMessage(`応答: ${JSON.stringify(data)}`);

    // listコマンドの応答
    if (data.clients) {
      this.updateClientList(data.clients);
    }

    // model listの応答
    if (data.models) {
      this.updateModelList(data.models);
    }

    // model get_expressionsの応答
    if (data.expressions) {
      this.updateExpressionList(data.expressions);
    }

    // model get_motionsの応答
    if (data.motions) {
      this.updateMotionList(data.motions);
    }

    // model get_parametersの応答
    if (data.parameters) {
      this.updateParameterList(data.parameters);
    }

    // client get_modelの応答
    if (data.model) {
      this.selectedModel = data.model;
      const select = document.getElementById('select-model') as HTMLSelectElement;
      if (select) {
        select.value = data.model;
      }
      this.showMessage(`クライアントのモデル: ${data.model}`);
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
    }
  }

  /**
   * モデルリストを更新
   */
  private updateModelList(models: string[]): void {
    this.models = models;
    const select = document.getElementById('select-model') as HTMLSelectElement;
    if (!select) return;

    select.innerHTML = '<option value="">モデルを選択...</option>';
    models.forEach((model: string) => {
      const option = document.createElement('option');
      option.value = model;
      option.textContent = model;
      select.appendChild(option);
    });

    const element = document.getElementById('model-info');
    if (element) {
      element.innerHTML = `<div>モデル数: ${models.length}</div>`;
    }
  }

  /**
   * 表情リストを更新
   */
  private updateExpressionList(expressions: string[]): void {
    this.expressions = expressions;
    const select = document.getElementById('select-expression') as HTMLSelectElement;
    if (!select) return;

    select.innerHTML = '<option value="">表情を選択...</option>';
    expressions.forEach((expr: string) => {
      const option = document.createElement('option');
      option.value = expr;
      option.textContent = expr;
      select.appendChild(option);
    });

    const element = document.getElementById('model-info');
    if (element) {
      element.innerHTML = `<div>表情リスト: ${expressions.join(', ')}</div>`;
    }
  }

  /**
   * モーションリストを更新
   */
  private updateMotionList(motions: { [key: string]: number }): void {
    this.motions = motions;
    const groupSelect = document.getElementById('select-motion-group') as HTMLSelectElement;
    const noSelect = document.getElementById('select-motion-no') as HTMLSelectElement;

    if (groupSelect) {
      groupSelect.innerHTML = '<option value="">グループを選択...</option>';
      Object.keys(motions).forEach((group: string) => {
        const option = document.createElement('option');
        option.value = group;
        option.textContent = `${group} (${motions[group]}件)`;
        groupSelect.appendChild(option);
      });

      // グループ選択時に番号を更新
      groupSelect.addEventListener('change', (e) => {
        const target = e.target as HTMLSelectElement;
        if (noSelect && target.value && motions[target.value]) {
          noSelect.innerHTML = '<option value="">番号...</option>';
          const count = motions[target.value];
          for (let i = 0; i < count; i++) {
            const option = document.createElement('option');
            option.value = i.toString();
            option.textContent = i.toString();
            noSelect.appendChild(option);
          }
        }
      });
    }

    if (noSelect) {
      noSelect.innerHTML = '<option value="">番号...</option>';
      // 最初のグループがあれば、その数だけ番号を生成
      const firstGroup = Object.keys(motions)[0];
      if (firstGroup) {
        const count = motions[firstGroup];
        for (let i = 0; i < count; i++) {
          const option = document.createElement('option');
          option.value = i.toString();
          option.textContent = i.toString();
          noSelect.appendChild(option);
        }
      }
    }

    const element = document.getElementById('model-info');
    if (element) {
      element.innerHTML = `<div>モーショングループ: ${Object.keys(motions).join(', ')}</div>`;
    }
  }

  /**
   * パラメータリストを更新
   */
  private updateParameterList(parameters: Array<{ id: string; value: number }>): void {
    this.parameters = parameters;
    const element = document.getElementById('parameter-list');
    if (!element) return;

    let html = '<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px;">';
    parameters.forEach((param, index) => {
      html += `
        <div style="display: flex; align-items: center; gap: 5px;">
          <label style="font-size: 12px; min-width: 120px;">${param.id}:</label>
          <input type="number" id="param-value-${index}"
                 value="${param.value}"
                 step="0.1"
                 style="width: 80px; padding: 2px;" />
        </div>
      `;
    });
    html += '</div>';
    element.innerHTML = html;
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
