"""security.py 单元测试：路径越界拦截、危险命令拦截、密钥脱敏。"""
import json
import unittest

from automation.security import (
    check_files_lists,
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


if __name__ == "__main__":
    unittest.main()
