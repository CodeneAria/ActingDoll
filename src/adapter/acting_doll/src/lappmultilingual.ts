/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

/**
 * 多言語対応メッセージ定義
 */

export type Language = 'ja' | 'en';

interface MessageMap {
    [key: string]: {
        ja: string;
        en: string;
    };
}

/**
 * メッセージ定義
 */
const messages: MessageMap = {
    // モデル読み込み関連
    MODEL_DATA_NOT_EXIST: {
        ja: 'モデルデータが存在しません。',
        en: 'Model data does not exist.'
    },
    TEXTURE_FILENAME_NULL: {
        ja: 'テクスチャファイル名がnullです',
        en: 'getTextureFileName null'
    },

    // モーション関連
    CANT_START_MOTION: {
        ja: "[APP] モーションを開始できません。",
        en: "[APP] can't start motion."
    },
    START_MOTION: {
        ja: '[APP] モーション開始: [{0}_{1}]',
        en: '[APP] start motion: [{0}_{1}]'
    },
    LOAD_MOTION: {
        ja: '[APP] モーション読み込み: {0} => [{1}]',
        en: '[APP] load motion: {0} => [{1}]'
    },

    // 表情関連
    EXPRESSION_SET: {
        ja: '[APP] 表情設定: [{0}]',
        en: '[APP] expression: [{0}]'
    },
    EXPRESSION_IS_NULL: {
        ja: '[APP] 表情[{0}]はnullです',
        en: '[APP] expression[{0}] is null'
    },

    // イベント関連
    EVENT_FIRED: {
        ja: '{0} がLAppModelで発火しました!!',
        en: '{0} is fired on LAppModel!!'
    },

    // MOC3整合性チェック関連
    INCONSISTENT_MOC3: {
        ja: 'MOC3の整合性がありません。',
        en: 'Inconsistent MOC3.'
    },
    CONSISTENT_MOC3: {
        ja: 'MOC3の整合性が確認されました。',
        en: 'Consistent MOC3.'
    },

    // エラーメッセージ関連
    FAILED_TO_LOAD_FILE: {
        ja: 'ファイルの読み込みに失敗しました: {0}',
        en: 'Failed to load file {0}'
    },
    FAILED_TO_SETUP_LAYOUT: {
        ja: 'setupLayout()に失敗しました。',
        en: 'Failed to setupLayout().'
    },
    FAILED_TO_GET_PHYSICS_PARAMS: {
        ja: '物理演算パラメータの取得に失敗しました: {0}',
        en: 'Failed to get physics parameter names: {0}'
    },
    FAILED_TO_GET_BREATH_PARAMS: {
        ja: '呼吸パラメータの取得に失敗しました: {0}',
        en: 'Failed to get breath parameter names: {0}'
    },
    CANT_START_MOTION_FILE: {
        ja: 'モーション {0} を開始できません',
        en: "Can't start motion {0}"
    },
    CANT_MOTION_NO_OVERFLOW: {
        ja: '指定されたモーションは範囲外です: {0}',
        en: "Overflow motion no: {0}"
    },

    // LAppLive2DManager関連
    TAP_POINT: {
        ja: '[APP] タップ位置: {x: {0} y: {1}}',
        en: '[APP] tap point: {x: {0} y: {1}}'
    },
    HIT_AREA: {
        ja: '[APP] ヒット領域: [{0}]',
        en: '[APP] hit area: [{0}]'
    },
    MODEL_INDEX: {
        ja: '[APP] モデルインデックス: {0}',
        en: '[APP] model index: {0}'
    },
    MOTION_BEGAN: {
        ja: 'モーション開始',
        en: 'Motion Began'
    },
    MOTION_FINISHED: {
        ja: 'モーション終了',
        en: 'Motion Finished'
    },

    // LAppDelegate関連（WebSocket）
    CANVAS_CONTEXT_LOST: {
        ja: 'インデックス {0} のCanvas のコンテキストが失われました。WebGLRenderingContext の取得制限に達した可能性があります。',
        en: 'The context for Canvas at index {0} was lost, possibly because the acquisition limit for WebGLRenderingContext was reached.'
    },
    WS_WELCOME_RECEIVED: {
        ja: '[WebSocket] ウェルカムメッセージを受信しました: {0}',
        en: '[WebSocket] Welcome message received: {0}'
    },
    WS_BROADCAST_RECEIVED: {
        ja: '[WebSocket] ブロードキャストメッセージを受信: {0}',
        en: '[WebSocket] Broadcast message received: {0}'
    },
    WS_CONNECTION_FAILED: {
        ja: '[WebSocket] 接続に失敗しました: {0}',
        en: '[WebSocket] Connection failed: {0}'
    },
    WS_EYE_BLINK_SET: {
        ja: '[WebSocket] 自動目パチを設定しました: {0}',
        en: '[WebSocket] Eye blink set: {0}'
    },
    WS_BREATH_SET: {
        ja: '[WebSocket] 呼吸を設定しました: {0}',
        en: '[WebSocket] Breath set: {0}'
    },
    WS_IDLE_MOTION_SET: {
        ja: '[WebSocket] アイドリングモーションを設定しました: {0}',
        en: '[WebSocket] Idle motion set: {0}'
    },
    WS_DRAG_FOLLOW_SET: {
        ja: '[WebSocket] ドラッグ追従を設定しました: {0}',
        en: '[WebSocket] Drag follow set: {0}'
    },
    WS_PHYSICS_SET: {
        ja: '[WebSocket] 物理演算を設定しました: {0}',
        en: '[WebSocket] Physics set: {0}'
    },
    WS_EXPRESSION_SET: {
        ja: '[WebSocket] 表情を設定しました: {0}',
        en: '[WebSocket] Expression set: {0}'
    },
    WS_MOTION_SET: {
        ja: '[WebSocket] モーションを設定しました: {0} {1}',
        en: '[WebSocket] Motion set: {0} {1}'
    },
    WS_PARAM_NOT_FOUND: {
        ja: '[WebSocket] パラメータが見つかりません: {0}',
        en: '[WebSocket] Parameter not found: {0}'
    },
    WS_PARAMS_SET: {
        ja: '[WebSocket] パラメータを一括設定しました: {0}個成功, {1}個失敗',
        en: '[WebSocket] Parameters set: {0} succeeded, {1} failed'
    },
    WS_CLIENT_INITIALIZED: {
        ja: '[WebSocket] WebSocketクライアントを初期化しました',
        en: '[WebSocket] WebSocket client initialized'
    },
    WS_CLIENT_RELEASED: {
        ja: '[WebSocket] WebSocketクライアントを解放しました',
        en: '[WebSocket] WebSocket client released'
    },

    // LAppUI関連
    UI_ELEMENTS_NOT_FOUND: {
        ja: '[LAppUI] 必要なUI要素が見つかりません',
        en: '[LAppUI] Required UI elements not found'
    },
    UI_MODEL_LOADED: {
        ja: '[LAppUI] モデルが読み込まれました。UIを更新します',
        en: '[LAppUI] Model loaded, updating UI'
    },
    UI_EYE_BLINK_TOGGLED: {
        ja: '[LAppUI] 目パチ: {0}',
        en: '[LAppUI] Eye blink: {0}'
    },
    UI_BREATH_TOGGLED: {
        ja: '[LAppUI] 呼吸: {0}',
        en: '[LAppUI] Breath: {0}'
    },
    UI_IDLE_MOTION_TOGGLED: {
        ja: '[LAppUI] アイドリングモーション: {0}',
        en: '[LAppUI] Idle motion: {0}'
    },
    UI_DRAG_FOLLOW_TOGGLED: {
        ja: '[LAppUI] ドラッグ追従: {0}',
        en: '[LAppUI] Drag follow: {0}'
    },
    UI_PHYSICS_TOGGLED: {
        ja: '[LAppUI] 物理演算: {0}',
        en: '[LAppUI] Physics: {0}'
    },

    // WebSocketClient関連
    WS_CONNECTING: {
        ja: 'サーバーに接続中: {0}',
        en: 'Connecting to server: {0}'
    },
    WS_CONNECTED: {
        ja: 'WebSocketサーバーに接続しました',
        en: 'Connected to WebSocket server'
    },
    WS_CLOSED: {
        ja: 'WebSocket接続が閉じられました {0}',
        en: 'WebSocket connection closed {0}'
    },
    WS_ERROR: {
        ja: 'WebSocketエラー: {0}',
        en: 'WebSocket error: {0}'
    },
    WS_RECEIVED: {
        ja: '受信: {0}',
        en: 'Received: {0}'
    },
    WS_INVALID_JSON: {
        ja: '不正なJSON形式: {0} {1}',
        en: 'Invalid JSON format: {0} {1}'
    },
    WS_DISCONNECTED: {
        ja: 'WebSocketサーバーから切断しました',
        en: 'Disconnected from WebSocket server'
    },
    WS_RECONNECTING: {
        ja: '再接続を試みます... ({0}/{1})',
        en: 'Attempting to reconnect... ({0}/{1})'
    },
    WS_RECONNECT_FAILED: {
        ja: '再接続に失敗しました: {0}',
        en: 'Reconnection failed: {0}'
    },
    WS_MAX_RECONNECT_REACHED: {
        ja: '最大再接続試行回数に達しました',
        en: 'Maximum reconnection attempts reached'
    },
    WS_SENDING: {
        ja: '送信: {0}',
        en: 'Sending: {0}'
    },
    WS_NOT_CONNECTED: {
        ja: 'WebSocket接続が開いていません',
        en: 'WebSocket connection is not open'
    },
    WS_WELCOME_MSG: {
        ja: 'ウェルカムメッセージ: {0}',
        en: 'Welcome message: {0}'
    },
    WS_ECHO_RESPONSE: {
        ja: 'エコー応答: {0}',
        en: 'Echo response: {0}'
    },
    WS_BROADCAST_FROM: {
        ja: 'ブロードキャスト from {0}: {1}',
        en: 'Broadcast from {0}: {1}'
    },
    WS_CLIENT_CONNECTED: {
        ja: '新しいクライアントが接続しました (合計: {0})',
        en: 'New client connected (total: {0})'
    },
    WS_CLIENT_DISCONNECTED: {
        ja: 'クライアントが切断しました (合計: {0})',
        en: 'Client disconnected (total: {0})'
    },
    WS_COMMAND_RESPONSE: {
        ja: 'コマンド応答: {0}',
        en: 'Command response: {0}'
    },
    WS_ERROR_MSG: {
        ja: 'エラー: {0}',
        en: 'Error: {0}'
    },
    WS_EYE_BLINK_SETTING: {
        ja: '目パチ設定: {0}',
        en: 'Eye blink setting: {0}'
    },
    WS_BREATH_SETTING: {
        ja: '呼吸設定: {0}',
        en: 'Breath setting: {0}'
    },
    WS_IDLE_MOTION_SETTING: {
        ja: 'アイドリングモーション設定: {0}',
        en: 'Idle motion setting: {0}'
    },
    WS_DRAG_FOLLOW_SETTING: {
        ja: 'ドラッグ追従設定: {0}',
        en: 'Drag follow setting: {0}'
    },
    WS_PHYSICS_SETTING: {
        ja: '物理演算設定: {0}',
        en: 'Physics setting: {0}'
    },
    WS_EXPRESSION_SETTING: {
        ja: '表情設定: {0}',
        en: 'Expression setting: {0}'
    },
    WS_MOTION_SETTING: {
        ja: 'モーション設定: グループ={0}, インデックス={1}',
        en: 'Motion setting: group={0}, index={1}'
    },
    WS_PARAM_RECEIVED: {
        ja: 'パラメータ設定を受信',
        en: 'Parameter setting received'
    },
    WS_MODEL_INFO_REQUEST: {
        ja: 'モデル情報リクエストを受信',
        en: 'Model info request received'
    },
    WS_EYE_BLINK_REQUEST: {
        ja: '目パチ情報リクエストを受信',
        en: 'Eye blink info request received'
    },
    WS_BREATH_REQUEST: {
        ja: '呼吸情報リクエストを受信',
        en: 'Breath info request received'
    },
    WS_IDLE_MOTION_REQUEST: {
        ja: 'アイドリングモーション情報リクエストを受信',
        en: 'Idle motion info request received'
    },
    WS_DRAG_FOLLOW_REQUEST: {
        ja: 'ドラッグ追従情報リクエストを受信',
        en: 'Drag follow info request received'
    },
    WS_PHYSICS_REQUEST: {
        ja: '物理演算情報リクエストを受信',
        en: 'Physics info request received'
    },
    WS_EXPRESSION_REQUEST: {
        ja: '表情情報リクエストを受信',
        en: 'Expression info request received'
    },
    WS_MOTION_REQUEST: {
        ja: 'モーション情報リクエストを受信',
        en: 'Motion info request received'
    },
    WS_UNHANDLED_MESSAGE: {
        ja: '未処理のメッセージタイプ: {0} {1}',
        en: 'Unhandled message type: {0} {1}'
    },

    // WebSocketメッセージ送信・接続
    WS_SENT: {
        ja: '送信: {0}',
        en: 'Sent: {0}'
    },
    WS_NOT_OPEN: {
        ja: 'WebSocket接続が開いていません',
        en: 'WebSocket connection is not open'
    },
    WS_WELCOME_MESSAGE: {
        ja: 'ウェルカムメッセージ: {0}',
        en: 'Welcome message: {0}'
    },
    WS_ERROR_MESSAGE: {
        ja: 'エラー: {0}',
        en: 'Error: {0}'
    },

    // Controller関連
    CTRL_PANEL_NOT_FOUND: {
        ja: 'コントロールパネルが見つかりません',
        en: 'Control panel not found'
    },
    CTRL_WS_CONNECTED: {
        ja: 'WebSocketサーバーに接続しました',
        en: 'Connected to WebSocket server'
    },
    CTRL_WS_FAILED: {
        ja: 'WebSocket接続に失敗しました: {0}',
        en: 'WebSocket connection failed: {0}'
    },
    CTRL_WS_FAILED_SHOW: {
        ja: 'サーバーに接続できませんでした。',
        en: 'Server connection failed'
    },
    CTRL_CMD_RESPONSE: {
        ja: 'コマンド応答: {0}',
        en: 'Command response: {0}'
    },
    CTRL_SERVER_ERROR: {
        ja: 'サーバーエラー: {0}',
        en: 'Server error: {0}'
    },
    CTRL_WELCOME_MSG: {
        ja: 'ウェルカムメッセージ: {0}',
        en: 'Welcome message: {0}'
    },
    CTRL_COMMAND_RESPONSE: {
        ja: 'コマンド応答: {0}',
        en: 'Command response: {0}'
    },
    CTRL_WELCOME_MESSAGE: {
        ja: 'ウェルカムメッセージ: {0}',
        en: 'Welcome message: {0}'
    },
    CTRL_SELECT_CLIENT_AND_MESSAGE: {
        ja: 'クライアントとメッセージを入力してください',
        en: 'Please select a client and enter a message'
    },
    CTRL_SELECT_MODEL: {
        ja: 'モデルを選択してください',
        en: 'Please select a model'
    },
    CTRL_SELECT_CLIENT: {
        ja: 'クライアントを選択してください',
        en: 'Please select a client'
    },
    CTRL_SELECT_CLIENT_AND_EXPRESSION: {
        ja: 'クライアントと表情を選択してください',
        en: 'Please select a client and expression'
    },
    CTRL_SELECT_CLIENT_GROUP_NUMBER: {
        ja: 'クライアント、グループ、番号を選択してください',
        en: 'Please select a client, group, and number'
    },
    CTRL_ENTER_PARAMETER_VALUES: {
        ja: 'パラメータ値を入力してください',
        en: 'Please enter parameter values'
    },
    CTRL_ERROR: {
        ja: 'エラー: {0}',
        en: 'Error: {0}'
    },
    CTRL_SERVER_CONNECTED: {
        ja: 'サーバーに接続されました',
        en: 'Connected to server'
    },

    // LAppWavFileHandler関連
    WAV_ERROR: {
        ja: 'WAVファイルエラー: {0}',
        en: 'WAV file error: {0}'
    },

    // LAppView関連
    VIEW_TOUCHES_ENDED: {
        ja: '[APP] touchesEnded x: {0} y: {1}',
        en: '[APP] touchesEnded x: {0} y: {1}'
    },

    // LAppSubdelegate関連
    SUBDELEGATE_VERTEX_SHADER_FAILED: {
        ja: 'vertexShaderの作成に失敗しました',
        en: 'Failed to create vertexShader'
    },
    SUBDELEGATE_FRAGMENT_SHADER_FAILED: {
        ja: 'fragmentShaderの作成に失敗しました',
        en: 'Failed to create fragmentShader'
    },
    SUBDELEGATE_VIEW_NOT_FOUND: {
        ja: 'viewが見つかりません',
        en: 'view notfound'
    },

    // 共通
    ENABLED: {
        ja: '有効',
        en: 'enabled'
    },
    DISABLED: {
        ja: '無効',
        en: 'disabled'
    },
    RANDOM: {
        ja: 'ランダム',
        en: 'random'
    }
};

/**
 * 多言語対応メッセージクラス
 */
export class LAppMultilingual {
    private static _language: Language = 'en';

    /**
     * 言語を設定
     * @param lang 言語コード
     */
    public static setLanguage(lang: Language): void {
        this._language = lang;
    }

    /**
     * 現在の言語を取得
     * @returns 現在の言語コード
     */
    public static getLanguage(): Language {
        return this._language;
    }

    /**
     * メッセージを取得
     * @param key メッセージキー
     * @param params プレースホルダー置換用パラメータ
     * @returns ローカライズされたメッセージ
     */
    public static getMessage(key: string, ...params: any[]): string {
        const messageObj = messages[key];

        if (!messageObj) {
            console.warn(`Message key not found: ${key}`);
            return key;
        }

        let message = messageObj[this._language] || messageObj['en'];

        // プレースホルダー置換 {0}, {1}, ... を置換
        params.forEach((param, index) => {
            message = message.replace(new RegExp(`\\{${index}\\}`, 'g'), String(param));
        });

        return message;
    }
}

/**
 * メッセージキー定義（型安全のため）
 */
export const MessageKey = {
    // モデル読み込み関連
    MODEL_DATA_NOT_EXIST: 'MODEL_DATA_NOT_EXIST',
    TEXTURE_FILENAME_NULL: 'TEXTURE_FILENAME_NULL',

    // モーション関連
    CANT_START_MOTION: 'CANT_START_MOTION',
    START_MOTION: 'START_MOTION',
    LOAD_MOTION: 'LOAD_MOTION',

    // 表情関連
    EXPRESSION_SET: 'EXPRESSION_SET',
    EXPRESSION_IS_NULL: 'EXPRESSION_IS_NULL',

    // イベント関連
    EVENT_FIRED: 'EVENT_FIRED',

    // MOC3整合性チェック関連
    INCONSISTENT_MOC3: 'INCONSISTENT_MOC3',
    CONSISTENT_MOC3: 'CONSISTENT_MOC3',

    // エラーメッセージ関連
    FAILED_TO_LOAD_FILE: 'FAILED_TO_LOAD_FILE',
    FAILED_TO_SETUP_LAYOUT: 'FAILED_TO_SETUP_LAYOUT',
    FAILED_TO_GET_PHYSICS_PARAMS: 'FAILED_TO_GET_PHYSICS_PARAMS',
    FAILED_TO_GET_BREATH_PARAMS: 'FAILED_TO_GET_BREATH_PARAMS',
    CANT_START_MOTION_FILE: 'CANT_START_MOTION_FILE',
    CANT_MOTION_NO_OVERFLOW: 'CANT_MOTION_NO_OVERFLOW',

    // LAppLive2DManager関連
    TAP_POINT: 'TAP_POINT',
    HIT_AREA: 'HIT_AREA',
    MODEL_INDEX: 'MODEL_INDEX',
    MOTION_BEGAN: 'MOTION_BEGAN',
    MOTION_FINISHED: 'MOTION_FINISHED',

    // LAppDelegate関連（WebSocket）
    CANVAS_CONTEXT_LOST: 'CANVAS_CONTEXT_LOST',
    WS_WELCOME_RECEIVED: 'WS_WELCOME_RECEIVED',
    WS_BROADCAST_RECEIVED: 'WS_BROADCAST_RECEIVED',
    WS_CONNECTION_FAILED: 'WS_CONNECTION_FAILED',
    WS_EYE_BLINK_SET: 'WS_EYE_BLINK_SET',
    WS_BREATH_SET: 'WS_BREATH_SET',
    WS_IDLE_MOTION_SET: 'WS_IDLE_MOTION_SET',
    WS_DRAG_FOLLOW_SET: 'WS_DRAG_FOLLOW_SET',
    WS_PHYSICS_SET: 'WS_PHYSICS_SET',
    WS_EXPRESSION_SET: 'WS_EXPRESSION_SET',
    WS_MOTION_SET: 'WS_MOTION_SET',
    WS_PARAM_NOT_FOUND: 'WS_PARAM_NOT_FOUND',
    WS_PARAMS_SET: 'WS_PARAMS_SET',
    WS_CLIENT_INITIALIZED: 'WS_CLIENT_INITIALIZED',
    WS_CLIENT_RELEASED: 'WS_CLIENT_RELEASED',

    // LAppUI関連
    UI_ELEMENTS_NOT_FOUND: 'UI_ELEMENTS_NOT_FOUND',
    UI_MODEL_LOADED: 'UI_MODEL_LOADED',
    UI_EYE_BLINK_TOGGLED: 'UI_EYE_BLINK_TOGGLED',
    UI_BREATH_TOGGLED: 'UI_BREATH_TOGGLED',
    UI_IDLE_MOTION_TOGGLED: 'UI_IDLE_MOTION_TOGGLED',
    UI_DRAG_FOLLOW_TOGGLED: 'UI_DRAG_FOLLOW_TOGGLED',
    UI_PHYSICS_TOGGLED: 'UI_PHYSICS_TOGGLED',

    // WebSocketClient関連
    WS_CONNECTING: 'WS_CONNECTING',
    WS_CONNECTED: 'WS_CONNECTED',
    WS_CLOSED: 'WS_CLOSED',
    WS_ERROR: 'WS_ERROR',
    WS_RECEIVED: 'WS_RECEIVED',
    WS_INVALID_JSON: 'WS_INVALID_JSON',
    WS_DISCONNECTED: 'WS_DISCONNECTED',
    WS_RECONNECTING: 'WS_RECONNECTING',
    WS_RECONNECT_FAILED: 'WS_RECONNECT_FAILED',
    WS_MAX_RECONNECT_REACHED: 'WS_MAX_RECONNECT_REACHED',
    WS_SENDING: 'WS_SENDING',
    WS_NOT_CONNECTED: 'WS_NOT_CONNECTED',
    WS_WELCOME_MSG: 'WS_WELCOME_MSG',
    WS_ECHO_RESPONSE: 'WS_ECHO_RESPONSE',
    WS_BROADCAST_FROM: 'WS_BROADCAST_FROM',
    WS_CLIENT_CONNECTED: 'WS_CLIENT_CONNECTED',
    WS_CLIENT_DISCONNECTED: 'WS_CLIENT_DISCONNECTED',
    WS_COMMAND_RESPONSE: 'WS_COMMAND_RESPONSE',
    WS_ERROR_MSG: 'WS_ERROR_MSG',
    WS_EYE_BLINK_SETTING: 'WS_EYE_BLINK_SETTING',
    WS_BREATH_SETTING: 'WS_BREATH_SETTING',
    WS_IDLE_MOTION_SETTING: 'WS_IDLE_MOTION_SETTING',
    WS_DRAG_FOLLOW_SETTING: 'WS_DRAG_FOLLOW_SETTING',
    WS_PHYSICS_SETTING: 'WS_PHYSICS_SETTING',
    WS_EXPRESSION_SETTING: 'WS_EXPRESSION_SETTING',
    WS_MOTION_SETTING: 'WS_MOTION_SETTING',
    WS_PARAM_RECEIVED: 'WS_PARAM_RECEIVED',
    WS_MODEL_INFO_REQUEST: 'WS_MODEL_INFO_REQUEST',
    WS_EYE_BLINK_REQUEST: 'WS_EYE_BLINK_REQUEST',
    WS_BREATH_REQUEST: 'WS_BREATH_REQUEST',
    WS_IDLE_MOTION_REQUEST: 'WS_IDLE_MOTION_REQUEST',
    WS_DRAG_FOLLOW_REQUEST: 'WS_DRAG_FOLLOW_REQUEST',
    WS_PHYSICS_REQUEST: 'WS_PHYSICS_REQUEST',
    WS_EXPRESSION_REQUEST: 'WS_EXPRESSION_REQUEST',
    WS_MOTION_REQUEST: 'WS_MOTION_REQUEST',
    WS_UNHANDLED_MESSAGE: 'WS_UNHANDLED_MESSAGE',

    // WebSocketメッセージ送信・接続
    WS_SENT: 'WS_SENT',
    WS_NOT_OPEN: 'WS_NOT_OPEN',
    WS_WELCOME_MESSAGE: 'WS_WELCOME_MESSAGE',
    WS_ERROR_MESSAGE: 'WS_ERROR_MESSAGE',

    // Controller関連
    CTRL_PANEL_NOT_FOUND: 'CTRL_PANEL_NOT_FOUND',
    CTRL_WS_CONNECTED: 'CTRL_WS_CONNECTED',
    CTRL_WS_FAILED: 'CTRL_WS_FAILED', CTRL_WS_FAILED_SHOW: 'CTRL_WS_FAILED_SHOW',


    CTRL_CMD_RESPONSE: 'CTRL_CMD_RESPONSE',
    CTRL_SERVER_ERROR: 'CTRL_SERVER_ERROR',
    CTRL_WELCOME_MSG: 'CTRL_WELCOME_MSG',
    CTRL_COMMAND_RESPONSE: 'CTRL_COMMAND_RESPONSE',
    CTRL_WELCOME_MESSAGE: 'CTRL_WELCOME_MESSAGE',
    CTRL_SELECT_CLIENT_AND_MESSAGE: 'CTRL_SELECT_CLIENT_AND_MESSAGE',
    CTRL_SELECT_MODEL: 'CTRL_SELECT_MODEL',
    CTRL_SELECT_CLIENT: 'CTRL_SELECT_CLIENT',
    CTRL_SELECT_CLIENT_AND_EXPRESSION: 'CTRL_SELECT_CLIENT_AND_EXPRESSION',
    CTRL_SELECT_CLIENT_GROUP_NUMBER: 'CTRL_SELECT_CLIENT_GROUP_NUMBER',
    CTRL_ENTER_PARAMETER_VALUES: 'CTRL_ENTER_PARAMETER_VALUES',
    CTRL_ERROR: 'CTRL_ERROR',
    CTRL_SERVER_CONNECTED: 'CTRL_SERVER_CONNECTED',
    // LAppWavFileHandler関連
    WAV_ERROR: 'WAV_ERROR',

    // LAppView関連
    VIEW_TOUCHES_ENDED: 'VIEW_TOUCHES_ENDED',

    // LAppSubdelegate関連
    SUBDELEGATE_VERTEX_SHADER_FAILED: 'SUBDELEGATE_VERTEX_SHADER_FAILED',
    SUBDELEGATE_FRAGMENT_SHADER_FAILED: 'SUBDELEGATE_FRAGMENT_SHADER_FAILED',
    SUBDELEGATE_VIEW_NOT_FOUND: 'SUBDELEGATE_VIEW_NOT_FOUND',

    // 共通
    ENABLED: 'ENABLED',
    DISABLED: 'DISABLED',
    RANDOM: 'RANDOM'
} as const;
