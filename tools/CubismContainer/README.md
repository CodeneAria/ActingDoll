# CubismContainer

Live2D Cubism SDK for WebをDockerコンテナで動作させるためのツール群です。

## 必要なもの

- Docker
- Python 3.6以上
- Live2D Cubism SDK for Web (CubismSdkForWeb-5-r.4.zip)

## セットアップ

### 1. Cubism SDK のダウンロード

Live2D Cubism SDK for Webを以下のURLからダウンロードしてください:

**https://www.live2d.com/sdk/download/web/**

ダウンロードした `CubismSdkForWeb-5-r.4.zip` を `./volume/` ディレクトリに配置してください。

```
tools/CubismContainer/
  └── volume/
      └── CubismSdkForWeb-5-r.4.zip  # ここに配置
```

### 2. Dockerコンテナの作成

```bash
python create_container.py
```

このスクリプトは以下の処理を実行します:

1. Cubism SDKのzipファイルを展開
2. 既存のコンテナとイメージがあれば削除
3. Dockerイメージをビルド
4. Dockerコンテナを起動
5. コンテナ内でnpm installとnpm run buildを実行

### 3. サーバーの起動

```bash
python run.py
```

このスクリプトは以下の処理を実行します:

1. Dockerコンテナを起動
2. コンテナ内でnpm run startを実行
3. http://localhost:5000 でアクセス可能になります

終了する場合は `Ctrl+C` を押してください。

## ファイル構成

- `create_container.py` - Dockerコンテナの作成スクリプト
- `run.py` - サーバー起動スクリプト
- `Dockerfile` - Dockerイメージの定義
- `volume/` - Cubism SDKの配置ディレクトリ

## 設定

デフォルトの設定:

- **コンテナ名**: `node_server`
- **イメージ名**: `img_node:latest`
- **ポート**: `5000`

設定を変更する場合は、各Pythonスクリプト内の変数を編集してください。
