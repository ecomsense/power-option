import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ["SKIP_PID_LOCK"] = "1"
os.environ["POWER_OPTION_TESTING"] = "1"

sys.path.insert(0, "src")

mock_fileutils = MagicMock()
mock_fileutils.is_file_exists.return_value = True
mock_fileutils.is_file_not_2day.return_value = False
mock_fileutils.get_lst_fm_yml.return_value = {}
mock_fileutils.add_path = MagicMock()
mock_fileutils.is_mk_filepath = MagicMock()
mock_fileutils.copy_file = MagicMock()

mock_logger = MagicMock()

sys.modules["toolkit"] = MagicMock()
sys.modules["toolkit.fileutils"] = MagicMock()
sys.modules["toolkit.fileutils"].Fileutils.return_value = mock_fileutils
sys.modules["toolkit.logger"] = MagicMock()
sys.modules["toolkit.logger"].Logger.return_value = mock_logger

sys.modules["stock_brokers"] = MagicMock()
sys.modules["stock_brokers.zerodha"] = MagicMock()
sys.modules["stock_brokers.zerodha.zerodha"] = MagicMock()

sys.modules["kiteconnect"] = MagicMock()
sys.modules["kiteext"] = MagicMock()

sys.path.insert(0, "src")
os.chdir(Path(__file__).parent.parent)