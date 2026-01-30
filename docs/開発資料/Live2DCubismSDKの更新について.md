# Live2D Cubism SDKの更新について

Live2D Cubism SDKのVersionを上げたい場合の対処になります。

## 修正が必要になる個所

- タグの更新
  - [ ] ```src/config.yaml```のタグの更新
  - [ ] ```tools/CubismContainer/volume/Dockerfile```にもタグの更新
- Live2D Cubism Coreの更新
  - [ ] ```src/Cubism/Core```を対象のVersionに更新してください
- Sampleコードの適用
  - [ ] サンプルより```src/adapter/acting_doll```を更新する。変更内容は下記参照


### Sampleコードの適用手順

1. **タグ更新**と**Live2D Cubism Coreの更新**を実行後、DockerImage/Containerを作成しなおしてください
  - 作り直したDockerImage/ContainerにCubismWebSamplesのサンプルコードがあるため

2. 最新に置き換える
  - package.json
