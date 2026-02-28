# ActingDoll

MCPを使ってLLMにLive2Dを動かすための命令を生成してもらうツールです。

## 概要

ActingDollは、Live2DモデルをWebSocketで制御するWebベースのコントローラーです。ブラウザ上のAPI.htmlから、GUIを使用してLive2Dモデルのパラメータ、表情、モーション、背景色などを操作できます。

## アーキテクチャ

- **WebSocketサーバー**: Live2DモデルとWebSocket通信してリアルタイムで制御
- **Webベースコントローラー**: ブラウザ上のAPI.htmlでGUI操作が可能
- **Dockerコンテナ環境**: 統合サーバーとLive2D SDKをDockerコンテナで管理

## 機能

### 基本コマンド
- **通知送信（notify）**: サーバーに通知メッセージを送信
- **モデル一覧取得**: 利用可能なモデルの一覧を取得
- **クライアント一覧取得**: 接続中のLive2Dクライアントの一覧を取得

### クライアント制御
- **メッセージ送信**: 特定のクライアントにメッセージを送信
- **モデル取得**: クライアントが使用しているモデル名を取得
- **モデル選択**: モデルを選択してそのモデルの表情・モーション・パラメータを取得

### アニメーション設定
- **表情設定（set_expression）**: モデルの表情を切り替え（happy, sad, angryなど）
- **現在の表情取得（get_expression）**: 現在のモデルの表情を取得
- **表情一覧取得（get_expressions）**: 利用可能な表情の一覧を取得
- **モーション再生（set_motion）**: 登録されたモーションを再生
- **現在のモーション取得（get_motion）**: 現在のモデルのモーション情報を取得
- **モーション一覧取得（get_motions）**: 利用可能なモーションの一覧を取得
- **目パチ設定（set_eye_blink）**: 目パチアニメーションの有効/無効を設定
- **呼吸設定（set_breath）**: 呼吸アニメーションの有効/無効を設定
- **アイドリングモーション設定（set_idle_motion）**: アイドリングモーションの有効/無効を設定
- **ドラッグ追従設定（set_drag_follow）**: マウスドラッグによる視線追従の有効/無効を設定
- **物理演算設定（set_physics）**: 物理演算の有効/無効を設定

### パラメータ操作
- **パラメータ一覧取得（get_parameters）**: モデルが持つパラメータ（目の開き具合、顔の角度など）の一覧を取得
- **パラメータ設定（set_parameter）**: Live2Dモデルの任意のパラメータ値を設定

### リップシンク
- **Wavファイル送信（set_lipsync）**: 音声ファイルをアップロードしてリップシンク処理を実行
  ※認証が必要です

### 位置・スケール操作
- **位置取得（get_position）**: モデルの現在の位置(X, Y座標)を取得
- **位置設定（set_position）**: モデルの位置を設定（相対移動にも対応）
- **スケール取得（get_scale）**: モデルの現在のスケール値を取得
- **スケール設定（set_scale）**: モデルのスケール値を設定

### 背景色操作
- **背景色設定（set_background_color）**: RGB値(0～255)で背景色を設定
  - カラーピッカーで直感的に色を選択可能
  - RGBスライダーで個別に色値を調整可能
  - 16進数表示で現在の色を確認可能

## インストール

詳細なセットアップ手順は、[GettingStart.md](./GettingStart.md) を参照してください。

基本的なセットアップ手順：

```bash
git clone https://github.com/CodeneAria/ActingDoll.git
cd ActingDoll
# Dockerコンテナを作成してサーバーを起動
python src/CubismContainer/cubism_container.py create --workspace . --config config/config.yaml
```

## 使用方法

### サーバーの起動と操作

Dockerコンテナでサーバーが起動している場合、ブラウザで自動的にAPI.htmlが開き、WebSocket接続でLive2Dモデルを制御できます。

**API.htmlで利用可能な操作：**
- クライアント/モデルの選択
- 表情・モーション・パラメータの設定
- 位置・スケール・背景色の変更
- 認証
- メッセージ送信

### 環境変数

| 変数名              | 説明                               | デフォルト値            |
| ------------------- | ---------------------------------- | ----------------------- |
| `LIVE2D_SERVER_URL` | Live2D Cubism SDK WebサーバーのURL | `http://localhost:5000` |

## コマンドリファレンス

### WebSocketコマンドフォーマット

BaseコマンドとClientコマンドの2種類があります。

#### Baseコマンド

```
auth <token>                    認証トークンを認証
notify <message>                通知メッセージを送信
list                            接続中のクライアント一覧を取得
model list                       利用可能なモデル一覧を取得
model get_expressions <model>   モデルの表情一覧を取得
model get_motions <model>       モデルのモーション一覧を取得
model get_parameters <model>    モデルのパラメータ一覧を取得
send <client_id> <message>      特定のクライアントにメッセージを送信
```

#### Clientコマンド

```
client <client_id> get_model_name                      モデル名を取得
client <client_id> get_expression                      現在の表情を取得
client <client_id> set_expression <expression_id>      表情を設定
client <client_id> get_motion                          現在のモーション情報を取得
client <client_id> set_motion <group> <no> <priority> モーションを設定
client <client_id> get_eye_blink                       目パチ有効状態を取得
client <client_id> set_eye_blink <enabled|disabled>    目パチの有効/無効を設定
client <client_id> get_breath                          呼吸有効状態を取得
client <client_id> set_breath <enabled|disabled>       呼吸の有効/無効を設定
client <client_id> get_idle_motion                     アイドリングモーション有効状態を取得
client <client_id> set_idle_motion <enabled|disabled>  アイドリングモーションの有効/無効を設定
client <client_id> get_drag_follow                     ドラッグ追従有効状態を取得
client <client_id> set_drag_follow <enabled|disabled>  ドラッグ追従の有効/無効を設定
client <client_id> get_physics                         物理演算有効状態を取得
client <client_id> set_physics <enabled|disabled>      物理演算の有効/無効を設定
client <client_id> get_position                        現在の位置を取得
client <client_id> set_position <x> <y> [relative]     位置を設定
client <client_id> get_scale                           現在のスケール値を取得
client <client_id> set_scale <scale>                   スケール値を設定
client <client_id> get_parameters                      パラメータ一覧を取得
client <client_id> set_parameter <param_id>=<value> .. パラメータ値を設定
client <client_id> set_lipsync <base64_data>           リップシンク用音声データを設定
client <client_id> set_background_color <r> <g> <b>   背景色をRGBで設定（0～255）
```


## API.html について

ActingDollはブラウザベースのAPIコントローラーパネル（API.html）を提供しており、以下の機能をGUIで操作できます：

- **Web UIでの直感的操作**: WebSocket接続後、API.htmlを開くと自動的にコントロールパネルが表示されます
- **リアルタイムフィードバック**: コマンド実行結果が即座に表示されます
- **視覚的フィードバック**: 接続状態、認証状態などが色付きで表示されます

## 課題

- API.htmlのUIはあるが、応答性やUXの改善の余地あり
- 以前していしたMOC3ファイルが表示される。理由は前回のモデルデータを消す対応をしていないため。
  - 自身でsrc/adapter/Cubism/Resources内の不要なモデルデータを削除する必要があります

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。
