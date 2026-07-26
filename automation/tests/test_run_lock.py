"""automation/run_lock.py 与其在 orchestrator.py 中的接入的单元测试。

覆盖场景对应本次任务要求的 20 项测试点，详见各 TestCase 的类/方法命名与注释。
不发起任何真实 OpenAI/Claude 调用；真实并发测试使用 multiprocessing 启动两个
独立进程在同一临时仓库上竞争同一把锁，不依赖测试执行顺序。
"""
from __future__ import annotations

import io
import json
import multiprocessing as mp
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from automation import orchestrator, run_lock


def _make_temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="autodev-lock-test-"))


def _write_raw_lock(lock: run_lock.RepositoryRunLock, data: dict) -> None:
    lock.lock_dir.mkdir(parents=True, exist_ok=True)
    lock.lock_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _fake_low_value_plan_result():
    """构造一个 ValueScore 明显低于门槛（2+2+0+0-0-0=4 < 15）的候选任务，
    用于验证 Planner Candidate Loop 全部候选被拒绝后（NO_HIGH_VALUE_TASK）
    仓库运行锁仍然被正常释放。
    """
    from automation.models import DevelopmentTask, TokenUsage

    task = DevelopmentTask(
        task_id="task-low-value", title="低价值候选任务", objective="不会真正执行",
        rationale="用于测试 NO_HIGH_VALUE_TASK 场景下锁是否正常释放",
        scope="", acceptance_criteria=[], files_allowed=[], files_forbidden=[],
        validation_commands=[], risk_level="LOW", requires_sot_update=False, developer_prompt="",
        task_category="用户体验重大提升",
        value_user=2, value_product=2, value_legal=0, value_tech_debt=0,
        repetition_penalty=0, maintenance_cost=0,
        why_valuable="测试用途", why_not_other_candidates="测试用途",
        why_not_duplicate="测试用途", expected_user_benefit="测试用途",
    )
    usage = TokenUsage(call_label="planner", model="test-model", prompt_tokens=1, completion_tokens=1, total_tokens=2)
    return task, [usage]


def _fake_plan_result(risk_level: str = "LOW"):
    """构造一个与 automation/tests/test_orchestrator_flow.py 中同名 helper 等价的
    最小 DevelopmentTask + usage 元组，避免真实调用 OpenAI。
    """
    from automation.models import DevelopmentTask, TokenUsage

    task = DevelopmentTask(
        task_id="task-lock-test",
        title="锁测试任务",
        objective="不会真正执行",
        rationale="用于测试运行锁是否拦截 Planner 之后的流程",
        scope="",
        acceptance_criteria=[],
        files_allowed=[],
        files_forbidden=[],
        validation_commands=[],
        risk_level=risk_level,
        requires_sot_update=False,
        developer_prompt="",
        # Value Gate 字段：给出足以通过 ValueScore >= 15 门槛的取值
        # （8+8+0+2-0-0=18），确保这批"测试运行锁行为"的用例不会被 Value Gate
        # 拦在调用 Claude 之前——它们要测试的是锁的释放时机，不是 Value Gate 本身。
        task_category="产品能力提升",
        value_user=8, value_product=8, value_legal=0, value_tech_debt=2,
        repetition_penalty=0, maintenance_cost=0,
        why_valuable="测试用途", why_not_other_candidates="测试用途",
        why_not_duplicate="测试用途", expected_user_benefit="测试用途",
    )
    usage = TokenUsage(call_label="planner", model="test-model", prompt_tokens=1, completion_tokens=1, total_tokens=2)
    return task, [usage]


# ----------------------------------------------------------------------
# multiprocessing 目标函数必须在模块顶层才能在 Windows（spawn）下被正确 pickle。
# ----------------------------------------------------------------------
def _mp_acquire_worker(repo_root_str: str, ready_event, go_event, result_queue) -> None:
    from automation.run_lock import LockBusyError, LockUndeterminedError, RepositoryRunLock

    ready_event.set()
    go_event.wait(timeout=10)
    lock = RepositoryRunLock(Path(repo_root_str), command="race-test-worker")
    try:
        lock.acquire()
        result_queue.put("ACQUIRED")
    except LockBusyError:
        result_queue.put("BUSY")
    except LockUndeterminedError:
        result_queue.put("UNDETERMINED")
    except Exception as exc:  # noqa: BLE001 - 需要把子进程异常带回主进程用于断言失败原因
        result_queue.put(f"ERROR:{exc}")


class LockTestCaseBase(unittest.TestCase):
    def setUp(self):
        self.tmp_dirs: list[Path] = []

    def tearDown(self):
        for d in self.tmp_dirs:
            shutil.rmtree(d, ignore_errors=True)

    def make_repo(self) -> Path:
        d = _make_temp_dir()
        self.tmp_dirs.append(d)
        return d


class TestBasicAcquireRelease(LockTestCaseBase):
    """场景 1-3：首个实例获取成功、第二实例同仓库获取失败、不同仓库互不影响。"""

    def test_first_instance_acquires_lock_successfully(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo, command="pytest")
        info = lock.acquire()
        self.assertTrue(lock.lock_path.exists())
        self.assertEqual(info.pid, os.getpid())
        self.assertTrue(lock.is_owned())
        lock.release()
        self.assertFalse(lock.lock_path.exists())

    def test_second_instance_same_repo_fails_with_active_lock(self):
        repo = self.make_repo()
        first = run_lock.RepositoryRunLock(repo, command="pytest-first")
        first.acquire()

        second = run_lock.RepositoryRunLock(repo, command="pytest-second")
        with self.assertRaises(run_lock.LockBusyError) as ctx:
            second.acquire()
        self.assertEqual(ctx.exception.lock_info.run_id, first.run_id)
        first.release()

    def test_different_repos_can_acquire_independently(self):
        repo_a = self.make_repo()
        repo_b = self.make_repo()
        lock_a = run_lock.RepositoryRunLock(repo_a, command="pytest-a")
        lock_b = run_lock.RepositoryRunLock(repo_b, command="pytest-b")
        lock_a.acquire()
        lock_b.acquire()  # 不应因 repo_a 已被占用而失败
        self.assertTrue(lock_a.lock_path.exists())
        self.assertTrue(lock_b.lock_path.exists())
        lock_a.release()
        lock_b.release()


class TestActiveLockBlocksOrchestrator(LockTestCaseBase):
    """场景 4：活跃锁存在时，orchestrator.main() 必须在调用 Planner 之前就停止，
    Claude/Build/Commit 更不会被调用。
    """

    def test_active_lock_blocks_planner_claude_build_commit(self):
        repo = self.make_repo()
        holder = run_lock.RepositoryRunLock(repo, command="holder")
        holder.acquire()  # 模拟另一个仍在运行的 Auto Dev 实例

        with mock.patch.object(run_lock, "resolve_repo_root", return_value=repo), \
             mock.patch("automation.openai_client.plan_next_task") as mock_plan, \
             mock.patch("automation.claude_runner.run_claude") as mock_run_claude, \
             mock.patch("automation.validator.run_validation") as mock_validate, \
             mock.patch("automation.git_service.GitService.commit") as mock_commit:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main([])

        self.assertEqual(exit_code, orchestrator.EXIT_LOCK_BUSY)
        mock_plan.assert_not_called()
        mock_run_claude.assert_not_called()
        mock_validate.assert_not_called()
        mock_commit.assert_not_called()
        self.assertIn("BUSY", stdout.getvalue())
        holder.release()


class TestReleaseOnVariousExitPaths(LockTestCaseBase):
    """场景 5-9：正常成功、Planner/Claude 异常、Validation/Review 失败、
    KeyboardInterrupt，锁都必须被释放。
    """

    def setUp(self):
        super().setUp()
        # run_task_cycle() 内部使用 GitService(PROJECT_ROOT) 做工作区检查/提交，
        # 这与本测试文件用于验证"锁"的临时仓库是两回事——真实项目仓库当前可能
        # 处于任意（含"不干净"）状态，不应影响这里对锁释放行为的验证，因此复用
        # 既有 test_orchestrator_flow.py 的做法：把 GitService 整体替换为 Mock，
        # 并伪造一份 load_config()，避免依赖真实 .env.local / OPENAI_API_KEY。
        from automation.config import Config

        # ignore_cleanup_errors=True：KeyboardInterrupt 场景下 run_task_cycle()
        # 提前中止，日志文件句柄不会经过 finalize() 里的 handler.close()（这是
        # run_task_cycle 自身既有的、与运行锁无关的行为），Windows 上会导致临时
        # 目录清理时报 PermissionError；这里只影响测试自身的临时目录删除，不影响
        # 对锁是否正确释放的断言（锁释放发生在 main() 的 try/finally，独立于
        # run_task_cycle 的日志句柄）。
        self._tmp_runtime = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        runtime_path = Path(self._tmp_runtime.name)
        self.addCleanup(self._tmp_runtime.cleanup)

        fake_config = Config(
            openai_api_key="sk-test-not-real", openai_model="gpt-test", auto_commit=True,
            claude_timeout_seconds=10, openai_timeout_seconds=10,
        )
        patches = [
            mock.patch.object(orchestrator, "RUNTIME_DIR", runtime_path / "runtime"),
            mock.patch.object(orchestrator, "REPORTS_DIR", runtime_path / "reports"),
            mock.patch.object(orchestrator, "PROGRESS_FILE", runtime_path / "docs" / "project" / "AUTODEV_PROGRESS.md"),
            mock.patch.object(orchestrator, "load_config", return_value=fake_config),
            # 本文件测的是运行锁的获取/释放时机，与 Backlog First 无关，默认模拟
            # Backlog 为空，避免真实 Backlog 存在 READY 条目时拦截 DONE/低分场景。
            # 必须放在 GitService 之前——下方 `started[-1]` 依赖 GitService 是
            # patches 列表的最后一个元素。
            mock.patch.object(orchestrator.backlog, "get_ready_items", return_value=[]),
            mock.patch.object(orchestrator, "GitService"),
        ]
        for p in patches:
            self.addCleanup(p.stop)
        started = [p.start() for p in patches]
        self.mock_git_service_cls = started[-1]
        self.mock_git = mock.Mock()
        self.mock_git.is_git_repo.return_value = True
        self.mock_git.is_clean.return_value = True
        self.mock_git.get_status_short.return_value = ""
        self.mock_git.get_changed_files.return_value = ["web/src/x.ts"]
        self.mock_git.get_diff.return_value = ""
        self.mock_git.find_forbidden_violations.return_value = []
        diff_check_result = mock.Mock()
        diff_check_result.returncode = 0
        self.mock_git.diff_check.return_value = diff_check_result
        self.mock_git.commit.return_value = "abc1234"
        self.mock_git_service_cls.return_value = self.mock_git

    def test_release_after_planner_done_success(self):
        repo = self.make_repo()
        with mock.patch("automation.context_loader.build_planner_context", return_value="ctx"), \
             mock.patch("automation.openai_client.create_client"), \
             mock.patch("automation.openai_client.plan_next_task", return_value=_fake_plan_result(risk_level="DONE")), \
             mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main([])
        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertFalse((repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME).exists())

    def test_release_after_planner_exception(self):
        repo = self.make_repo()
        with mock.patch("automation.context_loader.build_planner_context", return_value="ctx"), \
             mock.patch("automation.openai_client.create_client"), \
             mock.patch("automation.openai_client.plan_next_task", side_effect=RuntimeError("boom")), \
             mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main([])
        self.assertEqual(exit_code, orchestrator.EXIT_GENERAL_FAILURE)
        self.assertFalse((repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME).exists())

    def test_release_after_claude_failure(self):
        from automation.models import CommandResult

        repo = self.make_repo()
        failed_result = CommandResult(
            command="claude", cwd=str(repo), exit_code=1, stdout="", stderr="claude 崩了",
            duration_seconds=0.1, timed_out=False,
        )
        with mock.patch("automation.context_loader.build_planner_context", return_value="ctx"), \
             mock.patch("automation.openai_client.create_client"), \
             mock.patch("automation.openai_client.plan_next_task", return_value=_fake_plan_result()), \
             mock.patch("automation.claude_runner.run_claude", return_value=failed_result), \
             mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main([])
        self.assertEqual(exit_code, orchestrator.EXIT_CLAUDE_FAILURE)
        self.assertFalse((repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME).exists())

    def test_release_after_validation_failure_medium_risk_no_retry(self):
        from automation.models import CommandResult

        repo = self.make_repo()
        ok_claude = CommandResult(
            command="claude", cwd=str(repo), exit_code=0, stdout="", stderr="",
            duration_seconds=0.1, timed_out=False,
        )
        failed_validation = CommandResult(
            command="npm run build", cwd=str(repo), exit_code=1, stdout="", stderr="build 失败",
            duration_seconds=0.1, timed_out=False,
        )
        with mock.patch("automation.context_loader.build_planner_context", return_value="ctx"), \
             mock.patch("automation.openai_client.create_client"), \
             mock.patch(
                 "automation.openai_client.plan_next_task",
                 return_value=_fake_plan_result(risk_level="MEDIUM"),
             ), \
             mock.patch("automation.claude_runner.run_claude", return_value=ok_claude), \
             mock.patch("automation.security.detect_unsafe_fix_signal", return_value=None), \
             mock.patch("automation.validator.run_validation", return_value=([failed_validation], False)), \
             mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main([])
        self.assertEqual(exit_code, orchestrator.EXIT_VALIDATION_FAILURE)
        self.assertFalse((repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME).exists())

    def test_release_after_keyboard_interrupt(self):
        repo = self.make_repo()
        with mock.patch("automation.context_loader.build_planner_context", side_effect=KeyboardInterrupt), \
             mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            with self.assertRaises(KeyboardInterrupt):
                orchestrator.main([])
        # main() 内部用 try/finally 释放锁，KeyboardInterrupt 会继续向外传播
        # （与 __main__ 顶层的 except KeyboardInterrupt 一致），但锁必须已释放。
        self.assertFalse((repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME).exists())

    def test_release_after_no_high_value_task(self):
        """场景 10（Value Gate Candidate Loop）：3 个候选全部被 Value Gate 拒绝，
        最终状态 NO_HIGH_VALUE_TASK，进程必须正常结束并释放仓库运行锁（不是错误、
        不是 BLOCKED，属于正常退出路径）。
        """
        repo = self.make_repo()
        with mock.patch("automation.context_loader.build_planner_context", return_value="ctx"), \
             mock.patch("automation.openai_client.create_client"), \
             mock.patch(
                 "automation.openai_client.plan_next_task",
                 side_effect=[_fake_low_value_plan_result() for _ in range(3)],
             ), \
             mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main([])
        output = stdout.getvalue()
        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertIn("当前没有符合 Value Gate 的高价值任务", output)
        self.assertFalse((repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME).exists())


class TestStaleLockHandling(LockTestCaseBase):
    """场景 10-12：陈旧 PID 归档后新锁成功获取；PID 复用但创建时间不匹配识别为
    陈旧；活跃 PID 且创建时间匹配时不得抢锁。
    """

    def test_stale_pid_is_archived_and_new_lock_acquired(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        _write_raw_lock(lock, {
            "pid": 999999999,  # 几乎不可能真实存在的 PID
            "process_start_time": 1.0,
            "autodev_start_time": "2020-01-01T00:00:00",
            "hostname": "old-host",
            "repo_root": str(repo),
            "run_id": "old-run",
            "task_id": "task-001",
            "command": "old command",
            "version": 1,
        })

        new_lock = run_lock.RepositoryRunLock(repo, command="new")
        info = new_lock.acquire()
        self.assertIsNotNone(new_lock.archived_stale_path)
        self.assertTrue(new_lock.archived_stale_path.exists())
        self.assertEqual(info.run_id, new_lock.run_id)
        new_lock.release()

    def test_pid_reused_with_mismatched_start_time_is_stale(self):
        if run_lock.psutil is None:
            self.skipTest("psutil 不可用，无法验证创建时间比对逻辑")
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        # 用当前测试进程自己的 PID，但故意写一个明显错误的 process_start_time，
        # 模拟"这个 PID 现在活着，但已经不是记录里的那个进程"（PID 被复用）。
        _write_raw_lock(lock, {
            "pid": os.getpid(),
            "process_start_time": 1.0,  # 1970 年附近，几乎不可能是真实创建时间
            "autodev_start_time": "2020-01-01T00:00:00",
            "hostname": "old-host",
            "repo_root": str(repo),
            "run_id": "old-run",
            "task_id": "",
            "command": "old",
            "version": 1,
        })
        inspection = lock.inspect()
        self.assertEqual(inspection.status, "stale")

    def test_active_pid_with_matching_start_time_is_not_stolen(self):
        if run_lock.psutil is None:
            self.skipTest("psutil 不可用，无法验证创建时间比对逻辑")
        repo = self.make_repo()
        holder = run_lock.RepositoryRunLock(repo, command="holder")
        holder.acquire()  # 使用当前测试进程真实的 pid + create_time

        challenger = run_lock.RepositoryRunLock(repo, command="challenger")
        with self.assertRaises(run_lock.LockBusyError):
            challenger.acquire()
        # 锁文件必须还是 holder 那一份，没有被覆盖
        raw = json.loads(holder.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(raw["run_id"], holder.run_id)
        holder.release()


class TestCorruptedLock(LockTestCaseBase):
    """场景 13-14：损坏的 JSON / 缺少必需字段，都必须安全停止，不覆盖。"""

    def test_invalid_json_stops_safely_without_overwrite(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        lock.lock_dir.mkdir(parents=True, exist_ok=True)
        lock.lock_path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaises(run_lock.LockUndeterminedError):
            lock.acquire()
        # 原始（损坏的）内容必须原样保留，不能被静默覆盖
        self.assertEqual(lock.lock_path.read_text(encoding="utf-8"), "{not valid json")

    def test_missing_required_fields_treated_as_corrupted(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        _write_raw_lock(lock, {"pid": 123})  # 缺 run_id/hostname/repo_root 等必需字段

        inspection = lock.inspect()
        self.assertEqual(inspection.status, "corrupted")
        with self.assertRaises(run_lock.LockUndeterminedError):
            lock.acquire()


class TestReleaseOwnership(LockTestCaseBase):
    """场景 15：release() 时磁盘上的锁已不属于本次 run_id，不得删除。"""

    def test_release_does_not_delete_lock_owned_by_someone_else(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo, command="mine")
        lock.acquire()

        # 模拟锁在中途被替换成了别的 run（例如人工用 unlock-stale 清理后被
        # 另一个进程重新获取）。
        _write_raw_lock(lock, {
            "pid": os.getpid(),
            "process_start_time": run_lock._get_process_start_time(os.getpid()),
            "autodev_start_time": "2020-01-01T00:00:00",
            "hostname": "someone-else-host",
            "repo_root": str(repo),
            "run_id": "someone-else-run",
            "task_id": "",
            "command": "someone-else",
            "version": 1,
        })

        released = lock.release()
        self.assertFalse(released)
        self.assertTrue(lock.lock_path.exists())
        raw = json.loads(lock.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(raw["run_id"], "someone-else-run")


class TestUpdateTask(LockTestCaseBase):
    """场景 16：update_task 原子更新成功，且不产出半个 JSON。"""

    def test_update_task_writes_valid_json_atomically(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo, command="pytest")
        lock.acquire()
        lock.update_task("task-007")

        raw = json.loads(lock.lock_path.read_text(encoding="utf-8"))
        self.assertEqual(raw["task_id"], "task-007")
        self.assertEqual(raw["run_id"], lock.run_id)
        lock.release()

    def test_update_task_noop_when_not_owned(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo, command="pytest")
        # 从未 acquire，直接调用 update_task 不应抛异常、也不应创建锁文件
        lock.update_task("task-should-not-exist")
        self.assertFalse(lock.lock_path.exists())


class TestLockStatusClassification(LockTestCaseBase):
    """场景 17：lock-status 对 FREE/ACTIVE/STALE/CORRUPTED 的判断正确。"""

    def test_free_when_no_lock_file(self):
        repo = self.make_repo()
        inspection = run_lock.RepositoryRunLock(repo).inspect()
        self.assertEqual(inspection.status, "free")

    def test_active_when_current_process_holds_lock(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo, command="pytest")
        lock.acquire()
        inspection = run_lock.RepositoryRunLock(repo).inspect()
        self.assertEqual(inspection.status, "active")
        lock.release()

    def test_stale_when_pid_does_not_exist(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        _write_raw_lock(lock, {
            "pid": 999999999, "process_start_time": 1.0,
            "autodev_start_time": "2020-01-01T00:00:00", "hostname": "h",
            "repo_root": str(repo), "run_id": "r", "task_id": "", "command": "c", "version": 1,
        })
        self.assertEqual(lock.inspect().status, "stale")

    def test_corrupted_when_repo_root_mismatch(self):
        repo = self.make_repo()
        other_repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        _write_raw_lock(lock, {
            "pid": os.getpid(), "process_start_time": None,
            "autodev_start_time": "2020-01-01T00:00:00", "hostname": "h",
            "repo_root": str(other_repo), "run_id": "r", "task_id": "", "command": "c", "version": 1,
        })
        self.assertEqual(lock.inspect().status, "corrupted")

    def test_lock_status_cli_exit_codes(self):
        repo = self.make_repo()
        with mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main(["--lock-status"])
            self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
            self.assertIn("FREE", stdout.getvalue())

            lock = run_lock.RepositoryRunLock(repo, command="pytest")
            lock.acquire()
            stdout2 = io.StringIO()
            with redirect_stdout(stdout2):
                exit_code2 = orchestrator.main(["--lock-status"])
            self.assertEqual(exit_code2, orchestrator.EXIT_LOCK_BUSY)
            self.assertIn("ACTIVE", stdout2.getvalue())
            lock.release()


class TestUnlockStaleCLI(LockTestCaseBase):
    def test_unlock_stale_archives_only_stale_lock(self):
        repo = self.make_repo()
        lock = run_lock.RepositoryRunLock(repo)
        _write_raw_lock(lock, {
            "pid": 999999999, "process_start_time": 1.0,
            "autodev_start_time": "2020-01-01T00:00:00", "hostname": "h",
            "repo_root": str(repo), "run_id": "r", "task_id": "", "command": "c", "version": 1,
        })
        with mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main(["--unlock-stale"])
        self.assertEqual(exit_code, orchestrator.EXIT_SUCCESS)
        self.assertFalse(lock.lock_path.exists())
        archived = list(lock.lock_dir.glob("autodev.lock.stale.*"))
        self.assertEqual(len(archived), 1)

    def test_unlock_stale_refuses_active_lock(self):
        repo = self.make_repo()
        holder = run_lock.RepositoryRunLock(repo, command="holder")
        holder.acquire()
        with mock.patch.object(run_lock, "resolve_repo_root", return_value=repo):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = orchestrator.main(["--unlock-stale"])
        self.assertEqual(exit_code, orchestrator.EXIT_UNLOCK_STALE_FAILED)
        self.assertTrue(holder.lock_path.exists())
        holder.release()


class TestGitignoreAndEntrypoints(unittest.TestCase):
    """场景 18-19：.autodev/ 不进入 Git；所有正式 Auto Dev 入口均经过锁。"""

    def test_autodev_dir_is_gitignored(self):
        project_root = Path(__file__).resolve().parents[2]
        gitignore_text = (project_root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".autodev/", gitignore_text)

    def test_orchestrator_is_the_only_entrypoint_with_main_guard(self):
        """automation/ 目录下只有 orchestrator.py 定义了 `if __name__ == "__main__"`
        入口，确认不存在绕开运行锁的第二个正式启动脚本。CLI 子命令
        （--lock-status/--unlock-stale）也复用同一个 argparse 入口，不是独立脚本。
        """
        automation_dir = Path(__file__).resolve().parents[1]
        entrypoints = []
        for py_file in automation_dir.glob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            if '__name__ == "__main__"' in text:
                entrypoints.append(py_file.name)
        self.assertEqual(entrypoints, ["orchestrator.py"])


class TestRepoRootResolution(unittest.TestCase):
    """resolve_repo_root() 必须绑定到仓库根目录，而不是调用方的当前目录。"""

    def test_resolves_actual_repo_root(self):
        project_root = Path(__file__).resolve().parents[2]
        resolved = run_lock.resolve_repo_root(project_root / "automation" / "tests")
        self.assertEqual(resolved, project_root.resolve())

    def test_raises_when_not_a_git_repo(self):
        tmp = Path(tempfile.mkdtemp(prefix="autodev-not-a-repo-"))
        try:
            with self.assertRaises(run_lock.RepoNotFoundError):
                run_lock.resolve_repo_root(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


@unittest.skipIf(os.name == "nt" and os.environ.get("CI") == "true", "CI 环境的 Windows 进程创建较慢，避免超时")
class TestRealConcurrency(LockTestCaseBase):
    """场景 20：两个真实进程真正同时竞争同一把锁，只有一个成功，不依赖执行顺序。"""

    def test_two_processes_race_only_one_wins(self):
        repo = self.make_repo()
        ctx = mp.get_context("spawn")
        ready1, ready2 = ctx.Event(), ctx.Event()
        go = ctx.Event()
        result_queue = ctx.Queue()

        p1 = ctx.Process(target=_mp_acquire_worker, args=(str(repo), ready1, go, result_queue))
        p2 = ctx.Process(target=_mp_acquire_worker, args=(str(repo), ready2, go, result_queue))
        p1.start()
        p2.start()
        self.assertTrue(ready1.wait(10), "worker 1 未能在超时前就绪")
        self.assertTrue(ready2.wait(10), "worker 2 未能在超时前就绪")
        go.set()  # 两个进程此时都已就绪、都在等待，几乎同时开始竞争同一把锁
        p1.join(20)
        p2.join(20)

        results = sorted(result_queue.get(timeout=10) for _ in range(2))
        self.assertEqual(results, ["ACQUIRED", "BUSY"], f"并发竞争结果异常：{results}")

        # 清理：胜出的子进程退出后未释放锁（子进程只 acquire 不 release，
        # 模拟真实场景中一个 Auto Dev 实例仍在运行），这里手动清理测试产物。
        lock_path = repo / run_lock.LOCK_DIR_NAME / run_lock.LOCK_FILE_NAME
        if lock_path.exists():
            lock_path.unlink()


if __name__ == "__main__":
    unittest.main()
