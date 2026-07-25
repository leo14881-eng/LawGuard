"""模型自检能力单元测试：openai_client.list_available_models / orchestrator --list-models。

全部使用 unittest.mock 模拟 OpenAI 客户端，不发起任何真实网络请求。
"""
import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

from automation import config as cfg
from automation import orchestrator
from automation.openai_client import (
    MODEL_RECOMMENDATION_NOTES,
    MODELS_API_DISCLAIMER,
    ModelListError,
    filter_likely_text_models,
    list_available_models,
)

# 与真实 --list-models 输出高度相似的模型 ID 样本，覆盖需要排除与需要保留的各类模型。
_SAMPLE_MODEL_IDS = [
    "gpt-5.5", "gpt-5.5-pro", "gpt-5-mini", "gpt-4.1", "gpt-4.1-mini",
    "gpt-4o", "gpt-4o-mini",
    "o1", "o3", "o3-mini", "o4-mini",
    "gpt-audio", "gpt-audio-mini",
    "gpt-realtime", "gpt-realtime-mini",
    "gpt-4o-mini-transcribe", "gpt-4o-transcribe-diarize",
    "sora-2", "sora-2-pro",
    "gpt-4o-mini-search-preview", "gpt-5-search-api",
    "text-embedding-3-small", "omni-moderation-latest",
    "gpt-image-1", "whisper-1", "tts-1",
    "gpt-3.5-turbo-instruct", "babbage-002", "davinci-002",
]


def _fake_model(model_id: str):
    m = mock.Mock()
    m.id = model_id
    return m


class TestListAvailableModels(unittest.TestCase):
    @mock.patch("automation.openai_client.OpenAI")
    def test_returns_sorted_model_ids_on_success(self, mock_openai_cls):
        fake_client = mock.Mock()
        fake_response = mock.Mock()
        fake_response.data = [_fake_model("gpt-b"), _fake_model("gpt-a"), _fake_model("text-embedding-3")]
        fake_client.models.list.return_value = fake_response
        mock_openai_cls.return_value = fake_client

        result = list_available_models("sk-test-not-real")

        self.assertEqual(result, ["gpt-a", "gpt-b", "text-embedding-3"])

    @mock.patch("automation.openai_client.OpenAI")
    def test_permission_denied_raises_model_list_error(self, mock_openai_cls):
        fake_client = mock.Mock()
        fake_client.models.list.side_effect = PermissionError("账户无权限访问模型列表")
        mock_openai_cls.return_value = fake_client

        with self.assertRaises(ModelListError):
            list_available_models("sk-test-not-real")

    @mock.patch("automation.openai_client.OpenAI")
    def test_network_error_raises_model_list_error(self, mock_openai_cls):
        fake_client = mock.Mock()
        fake_client.models.list.side_effect = ConnectionError("网络连接失败")
        mock_openai_cls.return_value = fake_client

        with self.assertRaises(ModelListError):
            list_available_models("sk-test-not-real")

    def test_filter_excludes_non_text_models(self):
        ids = ["gpt-test", "text-embedding-3-small", "whisper-1", "dall-e-3"]
        filtered = filter_likely_text_models(ids)
        self.assertEqual(filtered, ["gpt-test"])

    def test_filter_falls_back_to_full_list_when_all_excluded(self):
        ids = ["text-embedding-3-small", "whisper-1"]
        filtered = filter_likely_text_models(ids)
        self.assertEqual(filtered, ids)


class TestFilterLikelyTextModelsDetailed(unittest.TestCase):
    """针对真实模型命名样本逐类校验排除/保留是否符合预期。"""

    def setUp(self):
        self.filtered = filter_likely_text_models(_SAMPLE_MODEL_IDS)

    def test_audio_models_excluded(self):
        self.assertNotIn("gpt-audio", self.filtered)
        self.assertNotIn("gpt-audio-mini", self.filtered)

    def test_realtime_models_excluded(self):
        self.assertNotIn("gpt-realtime", self.filtered)
        self.assertNotIn("gpt-realtime-mini", self.filtered)

    def test_transcribe_models_excluded(self):
        self.assertNotIn("gpt-4o-mini-transcribe", self.filtered)
        self.assertNotIn("gpt-4o-transcribe-diarize", self.filtered)

    def test_sora_models_excluded(self):
        self.assertNotIn("sora-2", self.filtered)
        self.assertNotIn("sora-2-pro", self.filtered)

    def test_search_models_excluded(self):
        self.assertNotIn("gpt-4o-mini-search-preview", self.filtered)
        self.assertNotIn("gpt-5-search-api", self.filtered)

    def test_legacy_babbage_davinci_instruct_excluded(self):
        self.assertNotIn("babbage-002", self.filtered)
        self.assertNotIn("davinci-002", self.filtered)
        self.assertNotIn("gpt-3.5-turbo-instruct", self.filtered)

    def test_embedding_moderation_image_audio_helper_models_excluded(self):
        self.assertNotIn("text-embedding-3-small", self.filtered)
        self.assertNotIn("omni-moderation-latest", self.filtered)
        self.assertNotIn("gpt-image-1", self.filtered)
        self.assertNotIn("whisper-1", self.filtered)
        self.assertNotIn("tts-1", self.filtered)

    def test_gpt_5_5_and_pro_retained(self):
        self.assertIn("gpt-5.5", self.filtered)
        self.assertIn("gpt-5.5-pro", self.filtered)

    def test_gpt_5_mini_retained(self):
        self.assertIn("gpt-5-mini", self.filtered)

    def test_gpt_4_1_retained(self):
        self.assertIn("gpt-4.1", self.filtered)
        self.assertIn("gpt-4.1-mini", self.filtered)

    def test_o_series_retained(self):
        self.assertIn("o1", self.filtered)
        self.assertIn("o3", self.filtered)
        self.assertIn("o3-mini", self.filtered)
        self.assertIn("o4-mini", self.filtered)


class TestCostFirstRecommendation(unittest.TestCase):
    """Cost First：默认推荐必须是成本最低的 gpt-5-nano，而不是静默内置默认模型。"""

    def test_default_recommendation_is_gpt_5_nano(self):
        self.assertEqual(MODEL_RECOMMENDATION_NOTES[0][0], "gpt-5-nano")

    def test_high_quality_recommendation_is_gpt_5_5(self):
        model_ids = [note[0] for note in MODEL_RECOMMENDATION_NOTES]
        self.assertIn("gpt-5.5", model_ids)

    def test_recommendation_is_not_env_default(self):
        """选型建议只是提示文本，不得让 config.load_config 静默采用推荐模型作为默认值。"""
        from automation import config as cfg

        self.assertFalse(hasattr(cfg, "DEFAULT_MODEL"))


class TestListModelsCommand(unittest.TestCase):
    def setUp(self):
        self._saved_key = os.environ.pop("OPENAI_API_KEY", None)
        self._env_file_patch = mock.patch.object(
            cfg, "ENV_FILE", cfg.PROJECT_ROOT / "automation" / "tests" / "__no_such_env_file__"
        )
        self._env_file_patch.start()
        self.addCleanup(self._env_file_patch.stop)
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        if self._saved_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self._saved_key

    def test_list_models_without_api_key_fails_safely(self):
        args = orchestrator.parse_args(["--list-models"])
        exit_code = orchestrator.handle_list_models(args)
        self.assertEqual(exit_code, orchestrator.EXIT_CONFIG_ERROR)

    @mock.patch("automation.openai_client.list_available_models")
    def test_list_models_prints_models_on_success(self, mock_list):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
        mock_list.return_value = ["gpt-test-a", "gpt-test-b"]
        args = orchestrator.parse_args(["--list-models"])

        exit_code = orchestrator.handle_list_models(args)

        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        mock_list.assert_called_once()

    @mock.patch("automation.openai_client.list_available_models")
    def test_list_models_reports_failure_without_crashing(self, mock_list):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
        mock_list.side_effect = ModelListError("网络异常")
        args = orchestrator.parse_args(["--list-models"])

        exit_code = orchestrator.handle_list_models(args)

        self.assertEqual(exit_code, orchestrator.EXIT_GENERAL_FAILURE)

    def test_list_models_does_not_call_response_generation(self):
        """--list-models 不得触发任何文本生成相关调用（plan_next_task / review_change）。"""
        os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
        with mock.patch("automation.openai_client.list_available_models", return_value=["gpt-test"]):
            with mock.patch("automation.openai_client.plan_next_task") as mock_plan:
                with mock.patch("automation.openai_client.review_change") as mock_review:
                    args = orchestrator.parse_args(["--list-models"])
                    orchestrator.handle_list_models(args)
                    mock_plan.assert_not_called()
                    mock_review.assert_not_called()

    @mock.patch("automation.openai_client.list_available_models")
    def test_list_models_empty_result_reports_safely(self, mock_list):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
        mock_list.return_value = []
        args = orchestrator.parse_args(["--list-models"])

        exit_code = orchestrator.handle_list_models(args)

        self.assertEqual(exit_code, orchestrator.EXIT_GENERAL_FAILURE)

    @mock.patch("automation.openai_client.list_available_models")
    def test_output_contains_models_api_disclaimer(self, mock_list):
        os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
        mock_list.return_value = list(_SAMPLE_MODEL_IDS)
        args = orchestrator.parse_args(["--list-models"])

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            orchestrator.handle_list_models(args)

        self.assertIn(MODELS_API_DISCLAIMER, buffer.getvalue())

    @mock.patch("automation.openai_client.list_available_models")
    def test_output_never_contains_api_key(self, mock_list):
        real_looking_key = "sk-test-not-real-should-never-be-printed-9f8e7d"
        os.environ["OPENAI_API_KEY"] = real_looking_key
        mock_list.return_value = list(_SAMPLE_MODEL_IDS)
        args = orchestrator.parse_args(["--list-models"])

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            orchestrator.handle_list_models(args)

        self.assertNotIn(real_looking_key, buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
