from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from vesperando_core import packer, configs


if __name__ == "__main__":
    game_dir: str = configs.Settings.get().get('paths', {}).get('game', '')
    packer.restore_backup(game_dir)