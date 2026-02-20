"""
Live2Dモデルの情報を管理するモジュール
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

# ロギング設定
logger = logging.getLogger("ModelManager")
logger.setLevel(logging.INFO)


class ModelManager:
    """
    Live2Dモデルの情報を管理するクラス
    """

    def __init__(self, models_dir: str = "./../Cubism/Resources"):
        self.models_dir = Path(models_dir)
        self.models: Dict[str, dict] = {}
        self.cdi3_data: Dict[str, dict] = {}  # cdi3.jsonのデータを格納
        self.physics3_data: Dict[str, dict] = {}  # physics3.jsonのデータを格納
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
        else:
            logger.info(f"モデル読み取り開始")
            logger.debug(f"  モデルディレクトリ: {self.models_dir}")
        model_count = 0
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name
                model_json = model_dir / f"{model_name}.model3.json"
                cdi3_json = model_dir / f"{model_name}.cdi3.json"
                physics3_json = model_dir / f"{model_name}.physics3.json"
                is_success = True

                # model3.jsonを読み込む
                if model_json.exists():
                    try:
                        with open(model_json, 'r', encoding='utf-8') as f:
                            model_data = json.load(f)
                            self.models[model_name] = model_data
                    except Exception as e:
                        is_success = False
                        logger.error(f"  => モデル読み込み失敗 {model_name}: {e}")
                # cdi3.jsonも読み込む
                if cdi3_json.exists():
                    try:
                        with open(cdi3_json, 'r', encoding='utf-8') as f:
                            cdi3_data = json.load(f)
                            self.cdi3_data[model_name] = cdi3_data
                    except Exception as e:
                        is_success = False
                        logger.error(f"  => cdi3.json読み込み失敗 {model_name}: {e}")

                # physics3.jsonも読み込む
                if physics3_json.exists():
                    try:
                        with open(physics3_json, 'r', encoding='utf-8') as f:
                            physics3_data = json.load(f)
                            self.physics3_data[model_name] = physics3_data
                    except Exception as e:
                        is_success = False
                        logger.error(
                            f"  => physics3.json読み込み失敗 {model_name}: {e}")
                if is_success:
                    logger.debug(f"  => モデル読み込み成功: {model_name}")
                    model_count += 1
        logger.info(f"モデル読み取り完了: [{model_count}] モデルが読み込まれました")

    def get_models(self) -> List[str]:
        """
        利用可能なモデル名のリストを取得
        """
        if len(self.models) > 0:
            return list(self.models.keys())
        else:
            logger.warning("利用可能なモデルが見つかりません")
        return []

    def get_motion_groups(self, model_name: Optional[str] = None) -> List[str]:
        """
        指定モデルのモーショングループ一覧を取得
        """
        target_model = model_name
        if target_model and target_model in self.models:
            motions = self.models[target_model].get(
                'FileReferences', {}).get('Motions', {})
            return list(motions.keys())
        return []

    def get_motions(self, motion_group: str, model_name: Optional[str] = None) -> List[dict]:
        """
        指定モーショングループのモーション一覧を取得
        """
        target_model = model_name
        if target_model and target_model in self.models:
            motions = self.models[target_model].get(
                'FileReferences', {}).get('Motions', {})
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
            self.current_motion_index = (
                self.current_motion_index + 1) % len(motions)
            return self.get_current_motion()
        return None

    def previous_motion(self) -> Optional[dict]:
        """
        前のモーションに戻る
        """
        motions = self.get_motions(self.current_motion_group)
        if motions:
            self.current_motion_index = (
                self.current_motion_index - 1) % len(motions)
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

    def get_cdi3_info(self, model_name: Optional[str] = None) -> Optional[dict]:
        """
        モデルのcdi3.json情報を取得
        """
        target_model = model_name
        if target_model and target_model in self.cdi3_data:
            return self.cdi3_data[target_model]
        return None

    def get_parameters(self, model_name: Optional[str] = None) -> List[dict]:
        """
        モデルのパラメータ一覧をcdi3.jsonから取得
        """
        cdi3_info = self.get_cdi3_info(model_name)
        if cdi3_info:
            return cdi3_info.get('Parameters', [])
        return []

    def get_physics3_info(self, model_name: Optional[str] = None) -> Optional[dict]:
        """
        モデルのphysics3.json情報を取得
        """
        target_model = model_name
        if target_model and target_model in self.physics3_data:
            return self.physics3_data[target_model]
        return None

    def get_physics_output_ids(self, model_name: Optional[str] = None) -> List[str]:
        """
        physics3.jsonのOutputに定義されているパラメータIDのリストを取得
        """
        physics3_info = self.get_physics3_info(model_name)
        output_ids = []
        if physics3_info:
            physics_settings = physics3_info.get('PhysicsSettings', [])
            for setting in physics_settings:
                outputs = setting.get('Output', [])
                for output in outputs:
                    destination = output.get('Destination', {})
                    if destination.get('Target') == 'Parameter':
                        param_id = destination.get('Id')
                        if param_id and param_id not in output_ids:
                            output_ids.append(param_id)
        return output_ids

    def get_parameters_exclude_physics(self, model_name: Optional[str] = None) -> List[dict]:
        """
        モデルのパラメータ一覧からphysics3.jsonのOutputに定義されたIDを除外して取得
        """
        all_parameters = self.get_parameters(model_name)
        physics_output_ids = self.get_physics_output_ids(model_name)

        # physics3.jsonのoutputに含まれていないパラメータのみを返す
        filtered_parameters = [
            param for param in all_parameters
            if param.get('Id') not in physics_output_ids
        ]
        return filtered_parameters
