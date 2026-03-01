# CubismContainer

Live2D Cubism SDK for Webを "Dockerコンテナ"で動作させるためのツール群です。

## 必要なもの

- Docker
- Python 3.12 以上
- PyYAML (`pip install pyyaml`)
- Live2D Cubism SDK for Web (5-r.5-beta.3)
  - `archives/` フォルダに `CubismSdkForWeb-5-r.5-beta.3.zip` を配置
- Live2D モデルデータ（`src/adapter/Resources/` に配置） - オプション

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install pyyaml
```

### 2. Cubism SDK のダウンロード

Live2D Cubism SDK for Webを以下のURLからダウンロードしてください:

**https://www.live2d.com/sdk/download/web/**

ダウンロードした `CubismSdkForWeb-*.zip` を `archives/` フォルダに配置してください。
このファイルは `create` コマンド実行時に自動的に展開されます。

```tree
Archives/
  └── CubismSdkForWeb-5-r.5-beta.3.zip
```

### 3. コンテナの作成と起動

```bash
python cubism_container.py create --workspace . --config config/config.yaml
```

このコマンドは以下の処理を実行します:

1. 設定ファイル (`config.yaml`) を読み込み
2. モデルデータを更新
3. Dockerイメージをビルド
   - GitHub から Cubism Framework をクローン
   - SDK アーカイブを展開して Framework に統合
   - コンテナ内で npm install とビルドを実行
4. Dockerコンテナを起動
   - http://localhost:8080 でHTTPサーバーが起動
   - WebSocket は localhost:8765 で待機

完了後、ブラウザで http://localhost:8080 にアクセスしてください。

## コマンドリファレンス

### create
Docker イメージとコンテナを作成して起動します。

```bash
python cubism_container.py create \
  --workspace . \
  --config config/config.yaml
```

**主要オプション:**
- `--workspace`: ワークスペースのパス
- `--config`: config.yaml のパス
- `--docker_image_name`: Docker イメージ名（デフォルト: acting_doll_image）
- `--docker_container_name`: Docker コンテナ名
- `--port_http`: HTTP サーバーポート
- `--port_websocket`: WebSocket ポート

### rebuild
コンテナ内でプロジェクトを再ビルドします。

```bash
python cubism_container.py rebuild --config config/config.yaml
```

**主要オプション:**
- `--config`: config.yaml のパス
- `-d, --development`: 開発モードでビルド
- `--docker_container_name`: Docker コンテナ名
- `--no_build_node_modules`: node_modules をビルドしない
- `--no_build_mcp`: MCP をビルドしない

### template
テンプレートファイル（config.yaml, Dockerfile）を生成します。

```bash
python cubism_container.py template --output config/
```

### exec
コンテナ内のシェルにアクセスします。

```bash
python cubism_container.py exec --config config/config.yaml
```

### stop_server
サーバーを停止します。

```bash
python cubism_container.py stop_server --config config/config.yaml
```

## 設定

設定は `config.yaml` ファイルで管理されています。

**主要な設定項目:**

| キー                  | デフォルト値                                 | 説明                     |
| --------------------- | -------------------------------------------- | ------------------------ |
| docker.image.name     | acting_doll_image                            | Docker イメージ名        |
| docker.container.name | acting_doll_server_sample                    | Docker コンテナ名        |
| server.port.cubism    | 8080                                         | HTTP サーバーポート      |
| server.port.websocket | 8765                                         | WebSocket ポート         |
| cubism.framework_repo | https://github.com/Live2D/CubismWebFramework | Framework Git リポジトリ |
| cubism.framework_tag  | 5-r.5-beta.3                                 | Framework Git タグ       |


設定を変更する場合は、`config.yaml` ファイルを編集してください。

## Docker内のフォルダ構成

```tree
${HOME}
└── workspace
    ├── adapter    : (ActingDoll用アダプタコード, src/adapterからマウント)
    └── Cubism
        ├── Core       : (Cubism Coreファイル, volume/Coreからマウント, 公式からダウンロードしたファイルを格納する)
        ├── Framework  : (Cubism Frameworkファイル, GitHubからクローンする)
        ├── Samples    : (Cubism Samplesファイル, GitHubからクローンする)
        └── models     : (Live2Dモデルデータ, src/Cubism/Resourcesからマウント, ユーザーが配置する)
```


## エラーハンドリング

スクリプトは以下の場合にエラーを表示して終了します:

- 設定ファイルが見つからない、または読み込めない
- Cubism Core ディレクトリまたはファイルが見つからない
- Git クローンまたはチェックアウトに失敗
- Core ファイルのコピーに失敗
- Dockerイメージのビルドに失敗
- Dockerコンテナの起動に失敗
- npm install/buildに失敗

エラーメッセージに従って問題を解決してください。
