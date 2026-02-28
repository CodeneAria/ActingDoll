# Getting Start

## 事前準備

このプロジェクトには、以下の作業を必要としています

1. 動かしたい対象のモデルデータを準備してください
   1. https://github.com/Live2D/CubismWebSamples.git のResourcesフォルダ内のモデルデータを利用することができます
   2. ご自身で用意したLive2Dモデルデータを使用することも可能です
      1. 利用できるモデルはFrameworkのVersionに依存する場合がございます。 `config.yaml` の `moc3`タグに指定してください
1. Cubism Core を[ダウンロード](https://www.live2d.com/sdk/download/web/)してください
   1. https://www.live2d.com/sdk/download/web/ より、```Cubism SDK for Web```の***最新ベータ版(CubismSdkForWeb-5-r.5-beta.3.1.zip)*** をダウンロードしてください
   2. ダウンロードしたファイルはCreateコマンドの引数に指定します

1. Config.yamlの内容を確認してください
   1. config.yamlの内容を確認し、必要に応じて変更してください
      1. `model_data_path` : モデルデータのパスを指定してください
      2. `cubism_sdk_path` : Cubism SDK for Webのzipファイルのパスを指定してください

## インストール方法

```bash
git clone https://github.com/CodeneAria/ActingDoll.git
cd ActingDoll

# uv を利用してpython環境を構築
uv sync

# [OPTIONS] config.yamlのテンプレートを生成する場合
cubism-container template --output ./config

# config.yamlをすべて指定した場合のコマンド
cubism-container create --config config/config.yaml
# [OPTIONS] config.yamlを指定せずにデフォルトのconfig.yamlを利用する場合
# workspace/config.yamlを生成しますので、編集してご利用ください
cubism-container create --workspace . --code_directory src/adapter --sdk_archive archives/CubismSdkForWeb-5-r.5-beta.3.zip --moc3_file archives/Resources/Haru/Haru.moc3 --docker_container_name Haru

# [TODO]
#   - 指定したモデルは```src/adapter/Cubism/Resources```にコピーされます。以前のモデルが指定が表示されることがあります
```

上記の手順が完了すると、Dockerコンテナが起動し、ブラウザで [http://localhost:8080](http://localhost:8080) にアクセスするとAPI.htmlが表示されます。
