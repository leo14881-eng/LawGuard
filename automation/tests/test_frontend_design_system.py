"""前端设计系统静态校验测试（对应 LAWGUARD_SOT.md P3：产品级界面原则）。

项目当前没有引入任何 JS/Vue 测试框架（package.json 中无 test 脚本），
为避免引入沉重的测试体系，这里用轻量的纯文本静态断言验证关键约束：
Design Token 是否存在、核心通用组件是否具备预期的 props/状态、
LegalDisclaimer 文案是否符合 P-1、页面是否复用组件而非重复裸文案等。
不做任何组件渲染，只做文件内容层面的可靠验证。
"""
import re
import unittest
from pathlib import Path

from automation.config import PROJECT_ROOT

WEB_SRC = PROJECT_ROOT / "web" / "src"


def _read(rel_path: str) -> str:
    path = WEB_SRC / rel_path
    return path.read_text(encoding="utf-8")


class TestDesignTokensExist(unittest.TestCase):
    def setUp(self):
        self.css = _read("style.css")

    def test_color_tokens_present(self):
        for token in (
            "--color-primary", "--color-surface", "--color-bg", "--color-text",
            "--color-success-text", "--color-warning-text", "--color-error-text",
            "--color-info-text", "--color-disabled-text",
        ):
            self.assertIn(token, self.css, f"缺少颜色 token：{token}")

    def test_spacing_scale_present(self):
        for token in ("--space-1", "--space-2", "--space-4", "--space-6", "--space-10"):
            self.assertIn(token, self.css, f"缺少间距 token：{token}")

    def test_typography_scale_present(self):
        for token in (
            "--font-size-page-title", "--font-size-section-title", "--font-size-block-title",
            "--font-size-body", "--font-size-caption", "--font-size-label", "--font-size-metric",
        ):
            self.assertIn(token, self.css, f"缺少字号 token：{token}")

    def test_radius_and_shadow_tokens_present(self):
        for token in ("--radius", "--radius-pill", "--shadow-sm", "--shadow-md"):
            self.assertIn(token, self.css, f"缺少圆角/阴影 token：{token}")

    def test_breakpoints_documented_and_unified(self):
        # 断点统一为 640 / 960，且需在文件中有文档化说明。
        self.assertIn("平板：>= 640px", self.css)
        self.assertIn("桌面：>= 960px", self.css)
        # 全站不应再出现历史上不一致的 800px 断点。
        self.assertNotIn("min-width: 800px", self.css)

    def test_button_and_card_states_covered(self):
        self.assertIn(".btn:disabled", self.css)
        self.assertIn(".btn--loading", self.css)
        self.assertIn(".btn:focus-visible", self.css)
        self.assertIn(".card--interactive", self.css)


class TestCoreComponentsExist(unittest.TestCase):
    def test_status_badge_covers_required_states(self):
        content = _read("components/StatusBadge.vue")
        for state in ("verified", "pending", "expired", "pending-review", "blocked", "missing-source"):
            self.assertIn(state, content, f"StatusBadge 缺少状态：{state}")

    def test_source_citation_card_has_required_fields(self):
        content = _read("components/SourceCitationCard.vue")
        for prop in ("sourceName", "sourceRef", "version", "verifiedDate", "status"):
            self.assertIn(prop, content, f"SourceCitationCard 缺少字段：{prop}")

    def test_legal_disclaimer_matches_p_minus_1_wording(self):
        content = _read("components/LegalDisclaimer.vue")
        self.assertIn("LawGuard 不提供个案法律意见", content)
        self.assertIn("请咨询执业律师或当地法律援助机构", content)
        # 禁止事项 P-1：不得推荐诉讼/辩护/举报策略或规避法律责任方法。
        for forbidden_topic in ("诉讼策略", "辩护方案", "举报方案", "规避法律责任"):
            self.assertIn(forbidden_topic, content)

    def test_app_button_covers_loading_and_disabled(self):
        content = _read("components/AppButton.vue")
        self.assertIn("loading", content)
        self.assertIn("disabled", content)
        self.assertIn("aria-busy", content)

    def test_app_empty_state_exists(self):
        self.assertTrue((WEB_SRC / "components" / "AppEmptyState.vue").exists())

    def test_app_loading_respects_reduced_motion(self):
        content = _read("components/AppLoading.vue")
        self.assertIn("prefers-reduced-motion", content)

    def test_page_header_exists_with_title_and_description_props(self):
        content = _read("components/PageHeader.vue")
        self.assertIn("title", content)
        self.assertIn("description", content)


class TestCorePagesUseDesignSystem(unittest.TestCase):
    """已完成设计系统改造的样板页面：HomeView / DisclaimerView / LegalSourcesView。"""

    def test_home_view_uses_legal_disclaimer_component(self):
        content = _read("views/HomeView.vue")
        self.assertIn("LegalDisclaimer", content)

    def test_disclaimer_view_uses_page_header_and_legal_disclaimer(self):
        content = _read("views/DisclaimerView.vue")
        self.assertIn("PageHeader", content)
        self.assertIn("LegalDisclaimer", content)

    def test_legal_sources_view_uses_source_citation_card(self):
        content = _read("views/LegalSourcesView.vue")
        self.assertIn("SourceCitationCard", content)
        self.assertIn("PageHeader", content)

    def test_no_raw_json_or_stack_trace_markers_in_views(self):
        """页面不得直接向用户展示原始 JSON、堆栈信息或数据库字段名。"""
        forbidden_patterns = [
            re.compile(r"Traceback \(most recent call last\)"),
            re.compile(r'"[a-zA-Z_]+":\s*"[^"]*"\s*,\s*"[a-zA-Z_]+":'),  # 连续 JSON 键值对
            re.compile(r"\bundefined\b"),
            re.compile(r"\bNullPointerException\b"),
        ]
        for view_path in (WEB_SRC / "views").glob("*.vue"):
            content = view_path.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                self.assertIsNone(
                    pattern.search(content),
                    f"{view_path.name} 中疑似包含原始技术细节：{pattern.pattern}",
                )


if __name__ == "__main__":
    unittest.main()
