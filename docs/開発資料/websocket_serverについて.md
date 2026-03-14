# websocket_server について

ActingDoll には WebSocket サーバー機能が組み込まれており、外部アプリケーションと通信することができます。これにより、他のソフトウェアからモデルの状態を取得したり、モデルに対してコマンドを送信したりすることが可能です。

コンテナに組み込めれているため、デバッグする際は以下の対応を行ってください。

1. ```src/adapter/acting_doll/src/base/lappdefine.ts``` 内の `WebSocketPort` を `任意の数字に変える(config.yamlで指定したポート番号以外が望ましい)` に設定します。
2. Rebuild してコンテナを再起動します。```python cubism_container.py rebuild --config config/config.yaml``` を実行してください。
3. VSCodeのデバッグ設定を変更します。
   1. VSCode のデバッグを使う場合は```.vscode/launch.json```内の `args` にある `--port`の引数を`1で設定したWebSocketPortの数字` に変更しててください。


```bash
uv sync
uv run acting_doll_server --port (1で設定したWebSocketPortの数字)
```

ポート番号例:

| **ポート番号** | **概要**                                          |
| -------------- | ------------------------------------------------- |
| 8765           | デフォルトのWebSocketポート番号。変更が推奨される |
| 8766           | Pythonデバッグ用の予備ポート番号                  |
