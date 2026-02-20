# テストディレクトリ

このディレクトリには、ActingDollプロジェクトの各種テストが含まれています。

## 環境セットアップ

### 必要なパッケージのインストール

```bash
pip install -U pytest pytest-asyncio websockets
```


## テストの実行方法

### 前提条件

テスト実行の前提条件として、Cubism Controllerが起動している必要があります。

```bash
# Cubism Controllerの起動
python tools/CubismContainer/create_container.py
python tools/CubismContainer/build.py
python tools/CubismContainer/start.py
```

### 基本的なテストの実行例

```bash
# すべてのテストを実行
pytest tests/ -v -s
# 特定のディレクトリのテストを実行
## WebSocketテストのみ
pytest tests/test_websocket/ -v -s
## MCPテストのみ
pytest tests/test_mcp/ -v -s

### 特定のテストファイルを実行
pytest tests/test_websocket/test_command.py -v -s
### 特定のテストクラスやメソッドを実行
pytest tests/test_websocket/test_command.py::TestBasicCommands -v -s
# 特定のテストメソッドを指定
pytest tests/test_websocket/test_command.py::TestBasicCommands::test_list_command -v -s
```

## トラブルシューティング

### タイムアウトエラーが発生する

- Cubism Controllerが起動しているか確認
- ポート番号が正しいか確認（デフォルト: 8765）
- ファイアウォールがブロックしていないか確認

### クライアントIDが取得できない

- Live2Dクライアントが接続されているか確認
- `test_list_command` が先に実行されているか確認

### モデル情報が取得できない

- `src/adapter/public/Resources/` にLive2Dモデルが配置されているか確認
- モデルディレクトリが正しく設定されているか確認

## 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio公式ドキュメント](https://pytest-asyncio.readthedocs.io/)
- [websockets公式ドキュメント](https://websockets.readthedocs.io/)
