"""security.py 单元测试：路径越界拦截、危险命令拦截、密钥脱敏。"""
import json
import unittest

from automation.security import (
    check_files_lists,
    detect_unsafe_fix_signal,
    is_command_allowed,
    is_safe_declared_forbidden_path,
    is_safe_relative_path,
    normalize_command,
    redact_secrets,
)


class TestPathSafety(unittest.TestCase):
    def test_rejects_parent_traversal(self):
        self.assertFalse(is_safe_relative_path("../outside.txt"))
        self.assertFalse(is_safe_relative_path("web/../../secret.txt"))

    def test_rejects_env_local(self):
        self.assertFalse(is_safe_relative_path(".env.local"))
        self.assertFalse(is_safe_relative_path(".env"))

    def test_rejects_forbidden_dirs(self):
        self.assertFalse(is_safe_relative_path(".git/config"))
        self.assertFalse(is_safe_relative_path("node_modules/vue/index.js"))
        self.assertFalse(is_safe_relative_path("automation/runtime/x.json"))
        self.assertFalse(is_safe_relative_path("automation/reports/x.md"))

    def test_rejects_lawguard_sot(self):
        # LAWGUARD_SOT.md 只保存长期稳定事实，Auto Dev 不得自动修改；
        # 与 CLAUDE.md 的进度记录职责统一收归 docs/project/AUTODEV_PROGRESS.md。
        self.assertFalse(is_safe_relative_path("LAWGUARD_SOT.md"))
        self.assertFalse(is_safe_relative_path("lawguard_sot.md"))

    def test_rejects_absolute_and_drive_paths(self):
        self.assertFalse(is_safe_relative_path("D:/SOFT/LawGuard/web"))
        self.assertFalse(is_safe_relative_path("/etc/passwd"))
        self.assertFalse(is_safe_relative_path("\\\\server\\share"))

    def test_rejects_wildcard(self):
        self.assertFalse(is_safe_relative_path("*"))

    def test_allows_normal_project_path(self):
        self.assertTrue(is_safe_relative_path("web/src/views/HomeView.vue"))
        self.assertTrue(is_safe_relative_path("web/src/data/stages.ts"))

    def test_rejects_lowercase_drive_path(self):
        self.assertFalse(is_safe_relative_path("d:/soft/lawguard/web"))
        self.assertFalse(is_safe_relative_path("c:\\windows\\system32"))

    def test_rejects_unc_path_variants(self):
        self.assertFalse(is_safe_relative_path("//server/share/file.txt"))
        self.assertFalse(is_safe_relative_path("\\\\192.168.1.1\\c$\\secret"))

    def test_rejects_case_variant_env_local(self):
        self.assertFalse(is_safe_relative_path(".ENV.LOCAL"))
        self.assertFalse(is_safe_relative_path(".Env.Local"))

    def test_rejects_case_variant_forbidden_dirs(self):
        self.assertFalse(is_safe_relative_path("NODE_MODULES/vue/index.js"))
        self.assertFalse(is_safe_relative_path(".GIT/config"))
        self.assertFalse(is_safe_relative_path("Automation/Runtime/x.json"))
        self.assertFalse(is_safe_relative_path("AUTOMATION/REPORTS/x.md"))

    def test_rejects_mixed_slash_traversal(self):
        self.assertFalse(is_safe_relative_path("web\\..\\..\\.env.local"))
        self.assertFalse(is_safe_relative_path("web/..\\../secret.txt"))
        self.assertFalse(is_safe_relative_path("automation\\runtime\\x.json"))

    def test_files_list_conflict_detection(self):
        issues = check_files_lists(["web/src/data/stages.ts"], ["web/src/data/stages.ts"])
        self.assertTrue(any("冲突" in i for i in issues))

    def test_files_list_forbidden_path_detected(self):
        issues = check_files_lists(["web/src/data/stages.ts"], ["../outside.txt"])
        self.assertTrue(any("非法路径" in i for i in issues))

    def test_files_forbidden_may_declare_globally_protected_paths(self):
        # 真实运行中 Planner（gpt-5-nano）习惯性地把 LAWGUARD_SOT.md 列入
        # files_forbidden 作为提示；这是合理、安全的冗余声明，不应被判定为
        # 非法路径而导致规划失败——只有 files_allowed 才需要严格排除全局
        # 禁止前缀。
        issues = check_files_lists(
            ["web/src/data/stages.ts"],
            ["LAWGUARD_SOT.md", ".env.local", "automation/runtime"],
        )
        self.assertEqual(issues, [])

    def test_is_safe_declared_forbidden_path_allows_protected_prefixes(self):
        self.assertTrue(is_safe_declared_forbidden_path("LAWGUARD_SOT.md"))
        self.assertTrue(is_safe_declared_forbidden_path(".env.local"))
        self.assertTrue(is_safe_declared_forbidden_path("automation/runtime/x.json"))

    def test_is_safe_declared_forbidden_path_still_rejects_traversal(self):
        self.assertFalse(is_safe_declared_forbidden_path("../outside.txt"))
        self.assertFalse(is_safe_declared_forbidden_path("*"))
        self.assertFalse(is_safe_declared_forbidden_path("D:/SOFT/LawGuard/web"))


class TestCommandSafety(unittest.TestCase):
    def test_allows_whitelisted_commands(self):
        self.assertTrue(is_command_allowed("npm run build"))
        self.assertTrue(is_command_allowed("git diff --check"))
        self.assertEqual(normalize_command("npx vue-tsc --noEmit"), ["npx", "vue-tsc", "--noEmit"])

    def test_rejects_shell_metacharacters(self):
        self.assertFalse(is_command_allowed("npm run build && echo pwned"))
        self.assertFalse(is_command_allowed("npm run build || echo pwned"))
        self.assertFalse(is_command_allowed("npm run build | more"))
        self.assertFalse(is_command_allowed("npm run build > out.txt"))
        self.assertFalse(is_command_allowed("npm run build >> out.txt"))
        self.assertFalse(is_command_allowed("npm run build < in.txt"))
        self.assertFalse(is_command_allowed("npm run build ; echo pwned"))
        self.assertFalse(is_command_allowed("npm run build `echo pwned`"))
        self.assertFalse(is_command_allowed("npm run build $(echo pwned)"))

    def test_rejects_shell_invocation_wrappers(self):
        self.assertFalse(is_command_allowed("cmd /c npm run build"))
        self.assertFalse(is_command_allowed("powershell -Command npm run build"))
        self.assertFalse(is_command_allowed("bash -c \"npm run build\""))

    def test_rejects_dangerous_git_commands(self):
        self.assertFalse(is_command_allowed("git push origin main"))
        self.assertFalse(is_command_allowed("git reset --hard"))
        self.assertFalse(is_command_allowed("git clean -fd"))
        self.assertFalse(is_command_allowed("git commit -m hack"))

    def test_rejects_network_commands(self):
        self.assertFalse(is_command_allowed("curl http://example.com"))
        self.assertFalse(is_command_allowed("wget http://example.com"))

    def test_rejects_unlisted_command(self):
        self.assertFalse(is_command_allowed("python -m http.server"))


class TestSecretRedaction(unittest.TestCase):
    def test_redacts_openai_style_key(self):
        text = "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456"
        redacted = redact_secrets(text)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", redacted)
        self.assertIn("REDACTED", redacted)

    def test_leaves_normal_text_untouched(self):
        text = "这是一段不含密钥的普通日志文本。"
        self.assertEqual(redact_secrets(text), text)

    def test_handles_empty_text(self):
        self.assertEqual(redact_secrets(""), "")
        self.assertIsNone(redact_secrets(None))

    def test_redacts_sk_proj_variant(self):
        text = "泄露示例：sk-proj-AbCdEf1234567890AbCdEf1234567890"
        redacted = redact_secrets(text)
        self.assertNotIn("sk-proj-AbCdEf1234567890AbCdEf1234567890", redacted)
        self.assertIn("REDACTED", redacted)

    def test_redacts_key_embedded_in_sentence(self):
        text = "报错信息中夹带了密钥 sk-abcdefghijklmnop123456 请注意脱敏。"
        redacted = redact_secrets(text)
        self.assertNotIn("sk-abcdefghijklmnop123456", redacted)

    def test_redacts_non_sk_prefixed_assignment(self):
        text = "OPENAI_API_KEY=not-sk-prefixed-secret-value"
        redacted = redact_secrets(text)
        self.assertNotIn("not-sk-prefixed-secret-value", redacted)
        self.assertIn("REDACTED", redacted)

    def test_does_not_corrupt_json_string_terminator(self):
        json_text = '{"stdout": "OPENAI_API_KEY=sk-thisisasecretkey1234567890", "exit_code": 0}'
        redacted = redact_secrets(json_text)
        parsed = json.loads(redacted)
        self.assertEqual(parsed["exit_code"], 0)
        self.assertNotIn("thisisasecretkey1234567890", parsed["stdout"])


class TestDetectUnsafeFixSignal(unittest.TestCase):
    """Validation/Review Auto Fix 安全边界：命中即禁止继续自动重试，需人工决策。"""

    def test_normal_fix_is_safe(self):
        diff = "diff --git a/web/src/x.ts b/web/src/x.ts\n+const a = 1\n"
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout="已修复类型错误。", diff_text=diff))

    def test_claude_self_reported_blocked_is_detected(self):
        stdout = "执行摘要：BLOCKED：缺少可核验法律来源，无法继续实施。"
        self.assertIsNotNone(detect_unsafe_fix_signal(claude_stdout=stdout, diff_text=""))

    def test_sensitive_keyword_in_added_diff_lines_is_detected(self):
        diff = "diff --git a/web/src/x.ts b/web/src/x.ts\n+// 新增身份认证逻辑\n"
        self.assertIsNotNone(detect_unsafe_fix_signal(claude_stdout="已完成修复。", diff_text=diff))

    def test_sensitive_keyword_in_existing_unchanged_lines_is_not_flagged(self):
        # 只扫描本次新增的行（+ 开头），不扫描上下文/删除行，避免误伤既有代码。
        diff = "diff --git a/web/src/x.ts b/web/src/x.ts\n context line about password\n-old password line\n+const b = 2\n"
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout="已完成修复。", diff_text=diff))

    def test_test_weakening_pattern_is_detected(self):
        diff = "diff --git a/web/src/x.test.ts b/web/src/x.test.ts\n+it.skip('should work', () => {})\n"
        self.assertIsNotNone(detect_unsafe_fix_signal(claude_stdout="测试已通过。", diff_text=diff))

    def test_ts_ignore_is_detected(self):
        diff = "diff --git a/web/src/x.ts b/web/src/x.ts\n+// @ts-ignore\n+const c: any = foo()\n"
        self.assertIsNotNone(detect_unsafe_fix_signal(claude_stdout="类型检查已通过。", diff_text=diff))


class TestDetectUnsafeFixSignalBlockedPhraseMatching(unittest.TestCase):
    """2026-07-26 修复：detect_unsafe_fix_signal 此前用 `"blocked" in text.lower()`
    单词包含判断，把 Task #4（Official Channels 新增打印按钮）里 Claude 摘要中的
    "验证结果：BLOCKED——因权限受限无法执行验证命令"误判为需要人工决策，实际是
    工具/环境限制，不是产品/法律/安全层面需要人工决策。改为短语级匹配后，本类
    验证：否定语境不再误判、真正的人工决策请求仍能正确识别、本次真实事故复现。
    """

    # ---- 否定语境：不得判定为 BLOCKED ----
    def test_no_blockers_is_not_blocked(self):
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout="No blockers.", diff_text=""))

    def test_not_blocked_is_not_blocked(self):
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout="Not blocked.", diff_text=""))

    def test_blockers_none_is_not_blocked(self):
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout="Blockers: none.", diff_text=""))

    def test_blocked_issues_none_is_not_blocked(self):
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout="Blocked issues: none.", diff_text=""))

    def test_no_human_decision_needed_is_not_blocked(self):
        self.assertIsNone(
            detect_unsafe_fix_signal(claude_stdout="No human decision needed. All done.", diff_text="")
        )

    def test_chinese_no_blocking_issue_is_not_blocked(self):
        self.assertIsNone(
            detect_unsafe_fix_signal(claude_stdout="没有阻塞问题，不需要人工决策。", diff_text="")
        )

    # ---- 明确阻塞语句：必须判定为 BLOCKED ----
    def test_i_need_human_input_is_blocked(self):
        result = detect_unsafe_fix_signal(
            claude_stdout="I am blocked and need human input to proceed.", diff_text=""
        )
        self.assertIsNotNone(result)

    def test_chinese_needs_user_choice_is_blocked(self):
        result = detect_unsafe_fix_signal(claude_stdout="存在多个实现方案，需要用户选择方案。", diff_text="")
        self.assertIsNotNone(result)

    # ---- 本次真实事故复现：不得再误判 ----
    def test_real_task4_claude_output_is_not_blocked(self):
        real_stdout = (
            "代码改动确认无误，改动本身是最小化的、复用现有组件与既定模式。\n\n"
            "## 执行摘要\n\n"
            "**改动内容**：在 `web/src/views/OfficialChannelsView.vue` 中导入 "
            "`PrintPageButton` 组件，并放入 `PageHeader` 的 `#actions` 插槽中。\n\n"
            "**验证结果：BLOCKED —— 无法执行验证命令**\n\n"
            "我在本次会话中多次尝试执行 `npx vue-tsc --noEmit` 与 `npm run build`"
            "（分别通过 Bash 与 PowerShell 工具，含单独执行、`cd` 后执行等多种方式），"
            "均被系统提示\"This command requires approval\"而无法运行，当前自动化任务"
            "环境中没有人工在场批准该权限请求，因此两项强制验证命令均未能实际执行，"
            "未能取得通过结果。\n\n"
            "请知悉：本次改动范围极小，理论上兼容风险很低；但按规则我不能在未实际"
            "跑通验证命令的情况下宣称\"已通过\"。建议由你本地或在有权限批准命令执行"
            "的环境中手动运行以下命令确认：\n\n```\ncd web\nnpx vue-tsc --noEmit\n"
            "npm run build\n```\n\n"
            "未修改 `LAWGUARD_SOT.md`，未涉及任何法律内容改动，无 P0/P-1 相关风险。"
            "未执行 git commit / push。"
        )
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout=real_stdout, diff_text=""))

    def test_legal_source_missing_convention_still_detected(self):
        # claude_runner.py 的 P0 Prompt 约定 Claude 在缺少可核验法律来源时应写
        # "BLOCKED：缺少可核验法律来源"，改用短语匹配后必须仍能可靠捕获该场景。
        stdout = "执行摘要：BLOCKED：缺少可核验法律来源，无法继续实施。"
        self.assertIsNotNone(detect_unsafe_fix_signal(claude_stdout=stdout, diff_text=""))


class TestSensitiveKeywordScanIsDiffOnly(unittest.TestCase):
    """2026-07-26 修复：Task #8（Privacy 页面新增打印按钮）真实误判：Claude 因
    Bash 工具需要审批、暂时无法执行 npm run build，在执行摘要里写"命令被权限
    系统拦截"——这里"权限系统"指 Claude Code 自身的工具审批沙箱，与应用本身
    要不要做用户权限系统毫无关系；实际 Diff 只新增了两行渲染 PrintPageButton
    的代码，不含任何敏感内容。旧逻辑对 Diff 新增行和 Claude 执行摘要两处都做
    关键词包含判断，这里验证：改为只扫描 Diff 后，摘要/任务描述里出现敏感词
    不再触发；Diff 里真实发生高风险代码行为时仍然可靠拦截。
    """

    _PRIVACY_DIFF = (
        "diff --git a/web/src/views/PrivacyView.vue b/web/src/views/PrivacyView.vue\n"
        "--- a/web/src/views/PrivacyView.vue\n"
        "+++ b/web/src/views/PrivacyView.vue\n"
        "@@ -1,10 +1,15 @@\n"
        " <script setup lang=\"ts\">\n"
        " import PageHeader from '../components/PageHeader.vue'\n"
        "+import PrintPageButton from '../components/PrintPageButton.vue'\n"
        " </script>\n"
        " \n"
        " <template>\n"
        "   <div class=\"container section\">\n"
        "-    <PageHeader title=\"隐私说明\" />\n"
        "+    <PageHeader title=\"隐私说明\">\n"
        "+      <template #actions>\n"
        "+        <PrintPageButton page-title=\"隐私说明 - 法护 LawGuard\" />\n"
        "+      </template>\n"
        "+    </PageHeader>\n"
    )

    # ---- Claude 摘要 / 任务描述里出现敏感词：不得阻塞 ----
    def test_privacy_page_wording_with_permission_system_is_not_blocked(self):
        # 页面正文本身讨论"权限系统"这类话题（例如隐私说明里提到"不涉及权限系统"）
        # 属于普通文案，不是代码行为。
        stdout = "本页面为纯静态说明文字，未涉及权限系统或任何后端逻辑。"
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout=stdout, diff_text=self._PRIVACY_DIFF))

    def test_claude_summary_negating_permission_system_is_not_blocked(self):
        stdout = "本次改动未修改权限系统，仅新增打印按钮。"
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout=stdout, diff_text=self._PRIVACY_DIFF))

    def test_claude_summary_mentioning_own_tool_permission_is_not_blocked(self):
        # 本次真实事故的原始措辞：Claude 描述的是它自己的工具审批沙箱，不是
        # 应用要不要做用户权限系统。
        stdout = (
            "已完成代码改动：在 web/src/views/PrivacyView.vue 中引入 PrintPageButton 组件。\n"
            "尚未执行 npm run build：命令被权限系统拦截，需要你手动批准后我才能继续执行验证。"
        )
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout=stdout, diff_text=self._PRIVACY_DIFF))

    def test_task_description_is_never_scanned(self):
        # detect_unsafe_fix_signal 的入参本就不接收任务对象，这里用一段"如果被
        # 当成敏感文本会触发"的字符串验证：即使拼进 stdout 也不该命中关键词表
        # （因为关键词现在只扫描 diff_text，不扫描 stdout），确认任务描述类
        # 自然语言文本不会被当作阻塞证据。
        task_like_text = "任务背景：本项目此前评估过权限系统与身份认证方案，本次任务与其无关。"
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout=task_like_text, diff_text=self._PRIVACY_DIFF))

    def test_diff_with_only_print_button_is_not_blocked(self):
        self.assertIsNone(
            detect_unsafe_fix_signal(claude_stdout="已完成，构建通过。", diff_text=self._PRIVACY_DIFF)
        )

    # ---- Diff 真实发生高风险代码行为：必须阻塞 ----
    def test_diff_adding_role_permission_check_is_blocked(self):
        diff = (
            "diff --git a/web/src/utils/auth.ts b/web/src/utils/auth.ts\n"
            "+export function hasPermission(user: User, action: string): boolean {\n"
            "+  return checkPermission(user.role, action)\n"
            "+}\n"
        )
        result = detect_unsafe_fix_signal(claude_stdout="已完成权限判断逻辑。", diff_text=diff)
        self.assertIsNotNone(result)

    def test_diff_modifying_router_guard_is_blocked(self):
        diff = (
            "diff --git a/web/src/router/index.ts b/web/src/router/index.ts\n"
            "+router.beforeEach((to, from, next) => {\n"
            "+  if (!isLoggedIn()) return next('/login')\n"
            "+  next()\n"
            "+})\n"
        )
        result = detect_unsafe_fix_signal(claude_stdout="已完成路由鉴权。", diff_text=diff)
        self.assertIsNotNone(result)

    def test_diff_modifying_token_session_logic_is_blocked(self):
        diff = (
            "diff --git a/web/src/utils/auth.ts b/web/src/utils/auth.ts\n"
            "+document.cookie = `access_token=${token}; path=/`\n"
        )
        result = detect_unsafe_fix_signal(claude_stdout="已完成登录态存储。", diff_text=diff)
        self.assertIsNotNone(result)

    def test_explicit_needs_human_decision_on_permission_model_is_blocked(self):
        stdout = "存在多种权限模型可选，需要人工决策权限模型。"
        result = detect_unsafe_fix_signal(claude_stdout=stdout, diff_text="")
        self.assertIsNotNone(result)

    # ---- 本次 Task #8 真实事故复现：不得再误判 ----
    def test_real_task8_claude_output_is_not_blocked(self):
        real_stdout = (
            "The build command keeps getting blocked pending approval and I shouldn't "
            "keep re-issuing the identical call. I need your confirmation to run the "
            "verification build.\n\n"
            "**请确认：是否允许我执行 `npm run build`（在 `web/` 目录下）以验证本次改动？**\n\n"
            "同时说明当前进度：\n\n"
            "- 已完成代码改动：在 `web/src/views/PrivacyView.vue` 中引入 `PrintPageButton` "
            "组件，并在 `PageHeader` 的 `#actions` 插槽中渲染\"打印本页\"按钮，`page-title` "
            "设为\"隐私说明 - 法护 LawGuard\"，写法与 `OfficialChannelsView.vue` 完全一致。\n"
            "- 尚未执行 `npm run build`：命令被权限系统拦截，需要你手动批准后我才能继续"
            "执行验证。"
        )
        self.assertIsNone(detect_unsafe_fix_signal(claude_stdout=real_stdout, diff_text=self._PRIVACY_DIFF))


if __name__ == "__main__":
    unittest.main()
