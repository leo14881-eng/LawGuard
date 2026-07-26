"""Git 服务模块：封装本次自动化流程中允许使用的 Git 操作。

所有命令均以参数数组通过 subprocess 执行，禁止 shell=True，
且不提供 push / reset --hard / clean / checkout . 等破坏性操作。
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from automation.security import is_safe_relative_path

# 简短 Conventional Commit 格式：type: 中文描述（首行不超过 80 字符）。
# 额外允许 AutoDev(task-NNN): 前缀，供 Auto Dev 全自动循环生成统一格式的提交信息。
_COMMIT_MESSAGE_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|AutoDev)(\([^)]+\))?: .{1,72}$"
)


class GitError(Exception):
    """Git 操作失败。"""


class GitService:
    """封装项目仓库的只读查询与受限提交操作。"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def _run(self, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def is_git_repo(self) -> bool:
        try:
            result = self._run(["rev-parse", "--is-inside-work-tree"])
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and result.stdout.strip() == "true"

    def get_status_short(self) -> str:
        return self._run(["status", "--short"]).stdout

    def is_clean(self) -> bool:
        return self.get_status_short().strip() == ""

    def get_diff(self, unified: int = 3) -> str:
        """获取当前任务未提交改动的 Diff（`git diff --no-ext-diff --unified=N HEAD`）。

        使用 `--no-ext-diff` 避免用户本地配置的外部 diff 工具影响输出格式；
        任务开始前已强制要求工作区干净（见 run_task_cycle 的安全检查），因此本方法
        在正常 Auto Loop 中天然只包含本任务尚未提交的改动，不包含历史已提交内容。
        """
        return self._run(["diff", "--no-ext-diff", f"--unified={unified}", "HEAD"]).stdout

    def get_diff_stat(self) -> str:
        return self._run(["diff", "HEAD", "--stat"]).stdout

    def get_recent_log(self, count: int = 5) -> str:
        return self._run(["log", f"-{count}", "--pretty=format:%h %ad %s", "--date=short"]).stdout

    def get_changed_files(self) -> list[str]:
        """解析 git status --short 输出，返回相对路径列表（正斜杠）。"""
        files: list[str] = []
        for line in self.get_status_short().splitlines():
            if not line.strip():
                continue
            path_part = line[3:].strip()
            if "->" in path_part:
                path_part = path_part.split("->", 1)[1].strip()
            path_part = path_part.strip('"')
            files.append(path_part.replace("\\", "/"))
        return files

    def find_forbidden_violations(self, files_forbidden: list[str]) -> list[str]:
        """检查已修改文件是否触碰任务禁止修改的文件/目录，返回违规文件列表。"""
        changed = self.get_changed_files()
        forbidden_norm = [f.strip().replace("\\", "/").rstrip("/") for f in (files_forbidden or [])]
        violations = []
        for f in changed:
            for forbidden in forbidden_norm:
                if not forbidden:
                    continue
                if f == forbidden or f.startswith(forbidden + "/"):
                    violations.append(f)
                    break
        return violations

    def diff_check(self) -> subprocess.CompletedProcess:
        return self._run(["diff", "--check"])

    def commit(self, files: list[str], message: str) -> str:
        """安全提交：仅接受具体文件列表与合法 Conventional Commit 信息，返回 commit hash。"""
        if not files:
            raise GitError("没有可提交的文件")
        for f in files:
            if not is_safe_relative_path(f):
                raise GitError(f"拒绝提交非法路径：{f}")
        if not self.validate_commit_message(message):
            raise GitError(f"提交信息不符合规范：{message}")

        add_result = self._run(["add", "--", *files])
        if add_result.returncode != 0:
            raise GitError(f"git add 失败：{add_result.stderr}")

        commit_result = self._run(["commit", "-m", message])
        if commit_result.returncode != 0:
            raise GitError(f"git commit 失败：{commit_result.stderr}")

        rev_result = self._run(["rev-parse", "HEAD"])
        return rev_result.stdout.strip()

    @staticmethod
    def validate_commit_message(message: str) -> bool:
        """校验提交信息是否为简短中文 Conventional Commit 格式。"""
        if not message or not message.strip():
            return False
        first_line = message.strip().splitlines()[0]
        if len(first_line) > 80:
            return False
        return bool(_COMMIT_MESSAGE_PATTERN.match(first_line))
