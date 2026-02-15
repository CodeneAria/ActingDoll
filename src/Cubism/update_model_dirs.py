#!/usr/bin/env python3
"""
src/modelsフォルダを検索して、lappdefine.tsのModelConfigs配列を自動更新するスクリプト
"""
import os
import re
import logging
from pathlib import Path

str_format = '[%(levelname)s]\t%(message)s'
# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format=str_format
)
logger = logging.getLogger(__name__)

MODEL_POSITION = (0.4, -0.4, 1.4)  # (horizontal, vertical, initScale)


def find_model_directories(models_dir: Path) -> list[str]:
    """
    src/modelsフォルダ内で.model3.jsonファイルを持つディレクトリを検索

    Args:
        models_dir: modelsディレクトリのPath

    Returns:
        モデルディレクトリ名のリスト（ソート済み）
    """
    model_dirs = []

    if not models_dir.exists():
        logger.error(f"{models_dir} が見つかりません")
        return model_dirs

    for item in models_dir.iterdir():
        if item.is_dir():
            # .model3.jsonファイルが存在するかチェック
            model3_files = list(item.glob("*.model3.json"))
            if model3_files:
                model_dirs.append(item.name)

    return sorted(model_dirs)


def update_lappdefine_ts(file_path: Path, model_dirs: list[str]) -> bool:
    """
    lappdefine.tsのModelConfigs配列を更新

    Args:
        file_path: lappdefine.tsのPath
        model_dirs: モデルディレクトリ名のリスト

    Returns:
        更新が成功したかどうか
    """
    if not file_path.exists():
        logger.error(f"{file_path} が見つかりません")
        return False

    # ファイルを読み込み
    content = file_path.read_text(encoding='utf-8')

    # ModelConfigs配列の部分を検索して置換
    # export const ModelConfigs: ModelConfig[] = [...]; の形式を探す
    pattern = r'(export const ModelConfigs: ModelConfig\[\] = \[)[^\]]*(\];)'

    # 新しい配列の内容を生成
    if model_dirs:
        model_entries = []
        for dir_name in model_dirs:
            # デフォルトはカスタムフラグfalse、初期位置(0,0)、スケール1.5
            model_entries.append(
                f"  {{ name: '{dir_name}', isCustom: false, "
                f"initX: {MODEL_POSITION[0]}, "
                f"initY: {MODEL_POSITION[1]}, "
                f"initScale: {MODEL_POSITION[2]} }}"
            )
        new_array_content = '\n' + ',\n'.join(model_entries) + '\n'
    else:
        new_array_content = ''

    replacement = f'\\g<1>{new_array_content}\\g<2>'

    # 置換を実行
    new_content, count = re.subn(
        pattern, replacement, content, flags=re.DOTALL)

    if count == 0:
        logger.warning("ModelConfigs配列が見つかりませんでした")
        return False

    # ファイルに書き込み
    file_path.write_text(new_content, encoding='utf-8')
    logger.info(f"✓ {file_path.name} を更新しました")

    return True


def main(work_dir, config_path):
    """メイン処理"""
    # プロジェクトルートディレクトリを取得

    # パスを設定
    models_dir = work_dir / "Cubism" / "Resources"
    lappdefine_path = work_dir / "adapter" / \
        "acting_doll" / "src" / "base" / "lappdefine.ts"

    logger.info("=" * 60)
    logger.info("ModelConfigs自動更新スクリプト")
    logger.info("=" * 60)
    logger.info(f"プロジェクトルート : {work_dir}")
    logger.info(f"モデルディレクトリ : {models_dir}")
    logger.info(f"更新対象ファイル   : {lappdefine_path}")
    logger.info("=" * 60)

    # モデルディレクトリを検索
    logger.info("モデルディレクトリを検索中...")
    model_dirs = find_model_directories(models_dir)

    if not model_dirs:
        logger.warning("警告: .model3.jsonファイルを持つディレクトリが見つかりませんでした")
        return

    logger.info(f"検出されたモデル数: {len(model_dirs)}")
    for dir_name in model_dirs:
        logger.info(f"  - {dir_name}")

    # lappdefine.tsを更新
    logger.info("lappdefine.tsを更新中...")
    success = update_lappdefine_ts(lappdefine_path, model_dirs)

    if success:
        logger.info("✓ 更新が完了しました！")
        logger.info("[注意] カスタムパラメータIDが必要なモデルは、"
                    "手動でlappdefine.tsのisCustomをtrueに変更してください。")
    else:
        logger.error("✗ 更新に失敗しました")


if __name__ == "__main__":
    work_dir = Path(__file__).parent.parent.resolve()
    os.chdir(work_dir)
    config_path = work_dir / "config.yaml"
    main(work_dir, config_path)
