#!/usr/bin/env python3
"""
Script to search src/models directory and automatically update ModelConfigs array in lappdefine.ts
"""
import argparse
import re
import logging
from pathlib import Path
try:
    from importlib.metadata import version as get_version
    __version__ = get_version('acting-doll-server')
except Exception:
    __version__ = '--,--,--'

str_format = '[%(levelname)s]\t%(message)s'
# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format=str_format
)
logger = logging.getLogger(__name__)


def _find_model_directories(models_dir: Path) -> list[str]:
    """
    Search for directories with .model3.json files in src/models folder

    Args:
        models_dir: Path to models directory

    Returns:
        List of model directory names (sorted)
    """
    model_dirs = []

    if not models_dir.exists():
        logger.error(f'{models_dir} not found')
        return model_dirs

    for item in models_dir.iterdir():
        if item.is_dir():
            # Check if .model3.json file exists
            model3_files = list(item.glob('*.model3.json'))
            if model3_files:
                model_dirs.append(item.name)

    return sorted(model_dirs)


def _update_lappdefine_ts(file_path: Path, model_dirs: list[str],
                          horizontal: float, vertical: float, scale: float,
                          custom: bool) -> bool:
    """
    Update ModelConfigs array in lappdefine.ts

    Args:
        file_path: Path to lappdefine.ts
        model_dirs: List of model directory names

    Returns:
        Whether the update was successful
    """
    if not file_path.exists():
        logger.error(f'{file_path} not found')
        return False

    # Read file
    content = file_path.read_text(encoding='utf-8')

    # Search and replace ModelConfigs array section
    # Search for export const ModelConfigs: ModelConfig[] = [...]; format
    pattern = r'(export const ModelConfigs: ModelConfig\[\] = \[)[^\]]*(\];)'

    # Generate new array content
    if model_dirs:
        model_entries = []
        for dir_name in model_dirs:
            # Default: custom flag false, initial position, scale 1.5
            model_entries.append(
                f"  {{ name: '{dir_name}', isCustom: {str(custom).lower()}, "
                f"initX: {horizontal}, "
                f"initY: {vertical}, "
                f"initScale: {scale} }}"
            )
        new_array_content = '\n' + ',\n'.join(model_entries) + '\n'
    else:
        new_array_content = ''

    replacement = f'\\g<1>{new_array_content}\\g<2>'

    # 置換を実行
    new_content, count = re.subn(
        pattern, replacement, content, flags=re.DOTALL)

    if count == 0:
        logger.warning('# ModelConfigs array not found')
        return False

    # Write to file
    file_path.write_text(new_content, encoding='utf-8')
    logger.info(f' - {file_path.name}')

    return True


def run_update_model():
    """Main process to update model configs in lappdefine.ts"""

    try:
        parser = argparse.ArgumentParser(
            description='ModelConfigs Auto Update Script'
        )
        parser.add_argument('-v', '--version', action='version',
                            version=f'%(prog)s {__version__}')
        parser.add_argument('-x', '--horizontal', type=float, default=0.4,
                            help='Initial horizontal position of the model')
        parser.add_argument('-y', '--vertical', type=float, default=-0.4,
                            help='Initial vertical position of the model')
        parser.add_argument('-s', '--scale', type=float, default=1.4,
                            help='Initial scale of the model')
        parser.add_argument('--custom', action='store_true', default=False,
                            help='Whether to set isCustom flag to true for all models')
        parser.add_argument('--workspace', type=str, default=str(Path(__file__).parent.parent.resolve()),
                            help='Path to the workspace directory')

        args = parser.parse_args()

        def _path(path_str: str, sub_dir: str) -> Path:
            try:
                path = Path(path_str) / sub_dir
                if path.exists():
                    return path.resolve().absolute()
                path = Path('/root/workspace/adapter') / sub_dir
                if path.exists():
                    return path.resolve().absolute()
            except:
                pass
            raise ValueError(f'Invalid path: {path_str}')

        # Update global model position and custom flag based on arguments
        models_dir = _path(args.workspace, 'Cubism/Resources')
        lappdefine_path = _path(args.workspace, 'acting_doll/src/base/lappdefine.ts')

        logger.info('=' * 60)
        logger.info(f'[ModelConfigs Auto Update Script]')
        logger.info(f'Model dir   : {models_dir}')
        logger.info(f'Update file : {lappdefine_path}')
        logger.info('=' * 60)

        # Search for model directories
        logger.info('# Searching for model directories...')
        model_dirs = _find_model_directories(models_dir)

        if not model_dirs:
            logger.warning('Warning: No directories with .model3.json files found')
            return

        logger.info(f'# Detected model count: {len(model_dirs)}')
        for dir_name in model_dirs:
            logger.info(f'  - {dir_name}')

        # Update lappdefine.ts
        logger.info('# Updating files...')
        success = _update_lappdefine_ts(lappdefine_path, model_dirs,
                                        args.horizontal, args.vertical,
                                        args.scale, args.custom)

        if success:
            logger.info('=== Update completed! ===')
        else:
            logger.error('=== Update failed ===')
    except Exception as e:
        logger.error(f'Error: {e}')


if __name__ == "__main__":
    run_update_model()
