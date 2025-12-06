# CubismContainer

Live2D Cubism SDK for WebをDockerコンテナで動作させるためのツール群です。

## 必要なもの

- Docker
- Python 3.6以上
- PyYAML (`pip install pyyaml`)
- Live2D Cubism SDK for Web (CubismSdkForWeb-5-r.4.zip)

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install pyyaml
```

### 2. Cubism SDK のダウンロード

Live2D Cubism SDK for Webを以下のURLからダウンロードしてください:

**https://www.live2d.com/sdk/download/web/**

ダウンロードした `CubismSdkForWeb-5-r.4.zip` を `./volume/` ディレクトリに配置してください。

```
tools/CubismContainer/
  └── volume/
      └── CubismSdkForWeb-5-r.4.zip  # ここに配置
```

### 3. Dockerコンテナの作成

```bash
python create_container.py
```

このスクリプトは以下の処理を実行します:

1. 設定ファイル (`config.yaml`) を読み込み
2. `volume/` ディレクトリを作成（存在しない場合）
3. Cubism SDKのzipファイルを展開（親フォルダなしで展開）
4. 既存のコンテナとイメージがあれば削除
5. Dockerイメージをビルド
6. Dockerコンテナを起動
7. コンテナ内でnpm installとnpm run buildを実行

エラーが発生した場合は処理を中断し、エラーメッセージを表示します。

### 4. サーバーの起動

```bash
python run.py
```

このスクリプトは以下の処理を実行します:

1. 設定ファイル (`config.yaml`) を読み込み
2. Dockerコンテナを起動
3. コンテナ内でnpm run startを実行
4. http://localhost:5000 でアクセス可能になります

終了する場合は `Ctrl+C` を押してください。

## ファイル構成

- `create_container.py` - Dockerコンテナの作成スクリプト
- `run.py` - サーバー起動スクリプト
- `config.yaml` - 設定ファイル
- `Dockerfile` - Dockerイメージの定義
- `volume/` - Cubism SDKの配置・展開ディレクトリ

## 設定

設定は `config.yaml` ファイルで管理されています。

デフォルトの設定:

- **コンテナ名**: `node_server`
- **イメージ名**: `img_node:latest`
- **ポート**: `5000`
- **SDK配置パス**: `./volume/CubismSdkForWeb-5-r.4.zip`
- **展開先ディレクトリ**: `./volume`

設定を変更する場合は、`config.yaml` ファイルを編集してください。

## エラーハンドリング

スクリプトは以下の場合にエラーを表示して終了します:

- 設定ファイルが見つからない、または読み込めない
- Cubism SDK zipファイルが見つからない
- SDKの展開に失敗
- Dockerイメージのビルドに失敗
- Dockerコンテナの起動に失敗
- npm install/buildに失敗

エラーメッセージに従って問題を解決してください。
