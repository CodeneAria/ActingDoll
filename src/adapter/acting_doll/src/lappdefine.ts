/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

import { LogLevel } from '@framework/live2dcubismframework';

/**
 * Sample Appで使用する定数
 */

// Canvas width and height pixel values, or dynamic screen size ('auto').
export const CanvasSize: { width: number; height: number } | 'auto' = 'auto';

// キャンバスの数
export const CanvasNum = 1;

// 画面
export const ViewScale = 1.0;
export const ViewMaxScale = 2.0;
export const ViewMinScale = 0.8;

export const ViewLogicalLeft = -1.0;
export const ViewLogicalRight = 1.0;
export const ViewLogicalBottom = -1.0;
export const ViewLogicalTop = 1.0;

export const ViewLogicalMaxLeft = -2.0;
export const ViewLogicalMaxRight = 2.0;
export const ViewLogicalMaxBottom = -2.0;
export const ViewLogicalMaxTop = 2.0;

// 相対パス
export const ResourcesPath = './Resources/';

// シェーダー相対パス
export const ShaderPath = './Framework/Shaders/WebGL/';

// モデルの後ろにある背景の画像ファイル
export const BackImageName = 'back_class_normal.png';

// 歯車
export const GearImageName = 'icon_gear.png';

// 終了ボタン
export const PowerImageName = 'CloseNormal.png';

// モデル定義---------------------------------------------
// モデル設定の型定義
export interface ModelConfig {
  name: string; // モデル名（ディレクトリ名とmodel3.jsonの名前を一致させること）
  isCustom: boolean; // カスタムパラメータIDを使用するか
  initX: number; // 初期位置 X軸
  initY: number; // 初期位置 Y軸
  initScale: number; // 初期スケール
}

// モデル設定配列
export const ModelConfigs: ModelConfig[] = [
  { name: 'Haru', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Hiyori', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Mao', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Mark', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Natori', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Ren', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Rice', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 },
  { name: 'Wanko', isCustom: false, initX: 0.4, initY: -0.4, initScale: 1.4 }
];

// 外部定義ファイル（json）と合わせる
export const MotionGroupIdle = 'Idle'; // アイドリング
export const MotionGroupTapBody = 'TapBody'; // 体をタップしたとき

// 外部定義ファイル（json）と合わせる
export const HitAreaNameHead = 'Head';
export const HitAreaNameBody = 'Body';

// モーションの優先度定数
export const PriorityNone = 0;
export const PriorityIdle = 1;
export const PriorityNormal = 2;
export const PriorityForce = 3;

// MOC3の整合性検証オプション
export const MOCConsistencyValidationEnable = true;
// motion3.jsonの整合性検証オプション
export const MotionConsistencyValidationEnable = true;

// デバッグ用ログの表示オプション
export const DebugLogEnable = false;
export const DebugTouchLogEnable = false;
export const DebugUILogEnable = false;

// Frameworkから出力するログのレベル設定
export const CubismLoggingLevel: LogLevel = LogLevel.LogLevel_Info;

// デフォルトのレンダーターゲットサイズ
export const RenderTargetWidth = 1900;
export const RenderTargetHeight = 1000;

// モデル位置移動量設定
export const ModelPositionMoveStep = 0.01;

// モデルスケールスライダー設定
export const ModelScaleMin = 0.5;
export const ModelScaleMax = 8.0;
export const ModelScaleStep = 0.1;
export const ModelScaleDefault = 1.0;

// WebSocket設定
export const WebSocketUrl = 'ws://';
export const WebSocketPort = '8765';
export const WebSocketAutoConnect = true;
export const WebSocketReconnectAttempts = 5;
export const WebSocketReconnectDelay = 3000;
