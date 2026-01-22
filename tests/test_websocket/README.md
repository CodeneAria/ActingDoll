# WebSocket 相互通信システム

PythonでWebSocketを使用した双方向通信のサンプル実装です。

## 機能

- **サーバー** (`server.py`)
  - 複数クライアントの接続管理
  - メッセージのブロードキャスト
  - エコーバック機能
  - コマンド処理（status, ping）
  - クライアント接続/切断の通知

- **クライアント** (`client.py`)
  - サーバーへの接続/切断
  - メッセージ送信（エコー、ブロードキャスト）
  - コマンド送信
  - 対話モード
  - 自動デモモード

## 依存関係のインストール

```bash
pip install websockets
```

## 使い方

### 1. サーバーの起動

```bash
python tests/test_websocket/server.py
```

サーバーは `ws://localhost:8765` で起動します。

### 2. クライアントの起動

#### 対話モード（デフォルト）

```bash
python tests/test_websocket/client.py
```

対話モードでは以下のコマンドが使用できます：

- `echo <text>` - エコーメッセージを送信
- `broadcast <text>` - 全クライアントにメッセージをブロードキャスト
- `status` - サーバーのステータスを取得
- `ping` - Pingを送信
- `quit` - クライアントを終了

#### 自動デモモード

```bash
python tests/test_websocket/client.py demo
```

## メッセージフォーマット

### エコーメッセージ

```json
{
  "type": "echo",
  "text": "Hello",
  "timestamp": "2025-12-14T10:00:00"
}
```

### ブロードキャストメッセージ

```json
{
  "type": "broadcast",
  "content": "こんにちは",
  "timestamp": "2025-12-14T10:00:00"
}
```

### コマンド

```json
{
  "type": "command",
  "command": "status",
  "timestamp": "2025-12-14T10:00:00"
}
```

## 実行例

### ターミナル1（サーバー）

```bash
$ python tests/test_websocket/server.py
2025-12-14 10:00:00 - INFO - WebSocketサーバーを起動中: ws://localhost:8765
2025-12-14 10:00:00 - INFO - サーバーが起動しました。Ctrl+Cで停止します。
2025-12-14 10:00:05 - INFO - 新しいクライアント接続: 127.0.0.1:54321
```

### ターミナル2（クライアント1）

```bash
$ python tests/test_websocket/client.py
2025-12-14 10:00:05 - INFO - サーバーに接続中: ws://localhost:8765
2025-12-14 10:00:05 - INFO - 接続しました
2025-12-14 10:00:05 - INFO - 受信: {'type': 'welcome', 'message': 'WebSocketサーバーに接続しました'}
> broadcast Hello everyone!
2025-12-14 10:00:10 - INFO - 送信: {'type': 'broadcast', 'content': 'Hello everyone!'}
```

### ターミナル3（クライアント2）

```bash
$ python tests/test_websocket/client.py
2025-12-14 10:00:08 - INFO - 接続しました
2025-12-14 10:00:10 - INFO - 受信: {'type': 'broadcast_message', 'from': '127.0.0.1:54321', 'content': 'Hello everyone!'}
```

## カスタマイズ

### ポート番号の変更

`server.py`の`main()`関数内：

```python
host = "localhost"
port = 8765  # 変更したいポート番号
```

`client.py`の`WebSocketClient`クラス：

```python
def __init__(self, uri: str = "ws://localhost:8765"):  # URIを変更
```

### 新しいメッセージタイプの追加

`server.py`の`handle_client()`関数内で新しい`msg_type`を処理：

```python
elif msg_type == "custom":
    # カスタム処理
    response = {"type": "custom_response", "data": "..."}
    await websocket.send(json.dumps(response, ensure_ascii=False))
```

## トラブルシューティング

### `websockets`モジュールが見つからない

```bash
pip install websockets
```

### ポートが既に使用されている

別のポート番号を使用するか、既存のプロセスを終了してください。

### 接続できない

- サーバーが起動しているか確認
- ファイアウォール設定を確認
- ホスト名とポート番号が正しいか確認
