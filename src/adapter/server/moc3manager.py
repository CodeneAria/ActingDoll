"""
Live2Dモデルの情報を管理するモジュール
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelManager:
    """
    Live2Dモデルの情報を管理するクラス
    """
    def __init__(self, models_dir: str = "./src/adapter/resources"):
        self.models_dir = Path(models_dir)
        self.models: Dict[str, dict] = {}
        self.current_motion_group: str = "Idle"
        self.current_motion_index: int = 0
        self.load_models()

    def get_list_models(self):
        return list(self.models.keys())

    def load_models(self):
        """
        モデルディレクトリから全モデルの情報を読み込む
        """
        if not self.models_dir.exists():
            logger.warning(f"モデルディレクトリが見つかりません: {self.models_dir}")
            return

        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name
                model_json = model_dir / f"{model_name}.model3.json"

                if model_json.exists():
                    try:
                        with open(model_json, 'r', encoding='utf-8') as f:
                            model_data = json.load(f)
                            self.models[model_name] = model_data
                        logger.info(f"モデル読み込み成功: {model_name}")
                    except Exception as e:
                        logger.error(f"モデル読み込み失敗 {model_name}: {e}")

    def get_models(self) -> List[str]:
        """
        利用可能なモデル名のリストを取得
        """
        return list(self.models.keys())

    def get_motion_groups(self, model_name: Optional[str] = None) -> List[str]:
        """
        指定モデルのモーショングループ一覧を取得
        """
        target_model = model_name
        if target_model and target_model in self.models:
            motions = self.models[target_model].get('FileReferences', {}).get('Motions', {})
            return list(motions.keys())
        return []

    def get_motions(self, motion_group: str, model_name: Optional[str] = None) -> List[dict]:
        """
        指定モーショングループのモーション一覧を取得
        """
        target_model = model_name
        if target_model and target_model in self.models:
            motions = self.models[target_model].get('FileReferences', {}).get('Motions', {})
            return motions.get(motion_group, [])
        return []

    def get_current_motion_group(self) -> str:
        """
        現在のモーショングループを取得
        """
        return self.current_motion_group

    def set_current_motion_group(self, motion_group: str) -> bool:
        """
        現在のモーショングループを設定
        """
        available_groups = self.get_motion_groups()
        if motion_group in available_groups:
            self.current_motion_group = motion_group
            self.current_motion_index = 0
            logger.info(f"モーショングループ変更: {motion_group}")
            return True
        logger.warning(f"モーショングループが見つかりません: {motion_group}")
        return False

    def get_current_motion_index(self) -> int:
        """
        現在のモーションインデックスを取得
        """
        return self.current_motion_index

    def set_current_motion_index(self, index: int) -> bool:
        """
        現在のモーションインデックスを設定
        """
        motions = self.get_motions(self.current_motion_group)
        if 0 <= index < len(motions):
            self.current_motion_index = index
            logger.info(f"モーションインデックス変更: {index}")
            return True
        logger.warning(f"無効なモーションインデックス: {index}")
        return False

    def get_current_motion(self) -> Optional[dict]:
        """
        現在のモーション情報を取得
        """
        motions = self.get_motions(self.current_motion_group)
        if motions and 0 <= self.current_motion_index < len(motions):
            return motions[self.current_motion_index]
        return None

    def next_motion(self) -> Optional[dict]:
        """
        次のモーションに進む
        """
        motions = self.get_motions(self.current_motion_group)
        if motions:
            self.current_motion_index = (self.current_motion_index + 1) % len(motions)
            return self.get_current_motion()
        return None

    def previous_motion(self) -> Optional[dict]:
        """
        前のモーションに戻る
        """
        motions = self.get_motions(self.current_motion_group)
        if motions:
            self.current_motion_index = (self.current_motion_index - 1) % len(motions)
            return self.get_current_motion()
        return None

    def get_model_info(self, model_name: Optional[str] = None) -> Optional[dict]:
        """
        モデルの完全な情報を取得
        """
        target_model = model_name
        if target_model and target_model in self.models:
            return self.models[target_model]
        return None
