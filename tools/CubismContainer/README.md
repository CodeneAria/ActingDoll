# CubismContainer

Live2D Cubism SDK for Webを "Dockerコンテナ"で動作させるためのツール群です。

## 必要なもの

- Docker
- Python 3.6以上
- PyYAML (`pip install pyyaml`)
- Live2D Cubism SDK for Web (CubismSdkForWeb-5-r.4)
  - 上記のSDK内に含まれるCoreファイルを `./volume/Core/` に配置する必要があります。
- 利用したい組み込み用Live2Dモデルデータ（`./src/adapter/resources/` に配置）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install pyyaml
```

### 2. Cubism SDK のダウンロード

Live2D Cubism SDK for Webを以下のURLからダウンロードしてください:

**https://www.live2d.com/sdk/download/web/**

ダウンロードした `CubismSdkForWeb-*.zip` を 展開し、Coreフォルダの中身を `./volume/Core/` ディレクトリに配置してください。
"Cubism Core for Web"は、"live2dcubismcore.min.js"しかなくビルドに失敗するため"Cubism SDK for Web"を使用してください。

```tree
tools/CubismContainer/
  └── volume/
      └── Core/
          ├── live2dcubismcore.d.ts
          ├── live2dcubismcore.js
          ├── live2dcubismcore.js.map
          ├── live2dcubismcore.min.js
          └── ... (その他のCoreファイル)
```

### 3. Dockerコンテナの作成

```bash
python CubismContainer.py create
```

このコマンドは以下の処理を実行します:

1. 設定ファイル (`config.yaml`) を読み込み
2. Cubism Coreファイルの存在を確認
3. 既存のコンテナとイメージがあれば削除
4. Dockerイメージをビルド
   1. GitHub から Cubism Web Samples をクローン（または既存リポジトリをチェックアウト）
   2. Cubism Core ファイルをSDKディレクトリにコピー
   3. コンテナ内でnpm installとnpm run buildを実行

エラーが発生した場合は処理を中断し、エラーメッセージを表示します。

### 4. ビルド

```bash
# 開発モードでMCP対応
python CubismContainer.py build --add_mcp

# 本番モードでMCP対応
python CubismContainer.py build --production --add_mcp
```

### 5. サーバーの起動

```bash
python CubismContainer.py start
```

このコマンドは以下の処理を実行します:

1. 設定ファイル (`config.yaml`) を読み込み
2. Dockerコンテナを起動
3. サーバーを起動
   1. http://localhost:5000 でアクセス可能になります

終了する場合は `Ctrl+C` を押してください。

### 6. デモアプリの起動

```bash
python CubismContainer.py start_demo
```

### 7. コンテナ内のシェルアクセス

```bash
python CubismContainer.py exec
```

### 8. ビルド成果物のクリーンアップ

```bash
python CubismContainer.py clean
```

## ファイル構成

- `CubismContainer.py` - 統合された全機能のスクリプト（create, build, clean, exec, start, start_demo）
- `config.yaml` - 設定ファイル
- `volume/`
  - `Dockerfile` - Dockerイメージの定義
  - `Core/` - Cubism Coreファイルの配置ディレクトリ

## 設定

設定は `config.yaml` ファイルで管理されています。

デフォルトの設定:

- docker:

| Key            | デフォルト値      | 概要                       |
| -------------- | ----------------- | -------------------------- |
| dockerfile     | volume/Dockerfile | Dockerfileのパス           |
| image.name     | img_node          | Dockerイメージ名           |
| image.version  | latest            | Dockerイメージのバージョン |
| container.name | node_server       | Dockerコンテナ名           |
| container.port | 5000              | コンテナのポート番号       |

- cubism:

| Key              | デフォルト値                                   | 概要               |
| ---------------- | ---------------------------------------------- | ------------------ |
| sdk_git_repo     | https://github.com/Live2D/CubismWebSamples.git | SDK Git リポジトリ |
| sdk_git_tag      | 5-r.4                                          | SDK Git タグ       |
| archive_core_dir | ./volume/Core                                  | Core配置パス       |


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
