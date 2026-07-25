"""config.py 单元测试：确认不存在硬编码默认模型，缺失必填配置时安全失败。

测试通过 mock.patch.object 将 ENV_FILE 指向不存在的路径，避免读取开发者
本机真实的 .env.local，保证测试与真实密钥、真实配置完全隔离。
"""
import os
import unittest
from unittest import mock

from automation import config as cfg


class TestLoadConfigSafety(unittest.TestCase):
    def setUp(self):
        self._saved_env = {}
        for key in ("OPENAI_API_KEY", "OPENAI_MODEL", "LAWGUARD_AUTO_COMMIT"):
            self._saved_env[key] = os.environ.pop(key, None)
        self._env_file_patch = mock.patch.object(
            cfg, "ENV_FILE", cfg.PROJECT_ROOT / "automation" / "tests" / "__no_such_env_file__"
        )
        self._env_file_patch.start()

    def tearDown(self):
        self._env_file_patch.stop()
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_missing_api_key_raises_config_error(self):
        os.environ["OPENAI_MODEL"] = "gpt-test"
        with self.assertRaises(cfg.ConfigError):
            cfg.load_config()

    def test_missing_model_raises_config_error(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
        with self.assertRaises(cfg.ConfigError):
            cfg.load_config()

    def test_no_hardcoded_default_model_constant(self):
        """确认源码中不再保留伪装成"已确认可用"的默认模型常量。"""
        self.assertFalse(hasattr(cfg, "DEFAULT_MODEL"))

    def test_model_override_argument_is_honored(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
        config = cfg.load_config(model_override="gpt-explicit-override")
        self.assertEqual(config.openai_model, "gpt-explicit-override")

    def test_valid_config_loads_successfully(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
        os.environ["OPENAI_MODEL"] = "gpt-explicit-from-env"
        config = cfg.load_config()
        self.assertEqual(config.openai_model, "gpt-explicit-from-env")
        self.assertEqual(config.openai_api_key, "sk-test-not-a-real-key")


if __name__ == "__main__":
    unittest.main()
