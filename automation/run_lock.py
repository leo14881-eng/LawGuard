"""仓库级 Auto Dev 运行锁：保证同一个 Git 仓库同一时间只有一个 LawGuard Auto Dev
主流程在运行。

背景：`automation/` 目录下发现过被其他进程同时修改的文件，怀疑存在两个 Auto Dev
进程同时操作同一个 Git 工作区，导致并发写入、Diff 污染、任务互相覆盖的风险。
现有 dirty-file 保护（运行前检查 `git status` 是否干净）只能防止"覆盖用户已有的
未提交改动"，无法防止"两个 Auto Dev 进程同时通过该检查后并发写入"，因此需要一把
独立于 dirty-file 保护之外的仓库级互斥锁，两者都必须保留，互不替代。

设计要点：
- 锁作用域绑定到仓库根目录（`git rev-parse --show-toplevel` 规范化后的绝对路径），
  不同仓库互不影响，不使用仅基于项目名的全局锁。
- 锁文件路径：`<repo-root>/.autodev/autodev.lock`，不进入 Git（见根目录
  `.gitignore` 新增的 `.autodev/`）。
- 原子获取：`os.open(path, O_CREAT | O_EXCL | O_WRONLY)`，Windows/Linux 通用，
  避免"先判断文件不存在、再写文件"这种两步操作之间的竞态窗口。
- 活跃/陈旧/损坏锁判定：读取锁文件中的 pid + process_start_time，用 psutil 同时
  核对"进程是否存在"与"进程创建时间是否匹配"，防止 PID 被系统复用后被误判为
  活跃。标准库没有跨平台、可靠的进程创建时间获取方式（Linux 需要解析
  `/proc/<pid>/stat`，Windows 需要 ctypes 调用 `GetProcessTimes`），自行实现
  容易出错且难以测试；psutil 是这个领域的事实标准、维护良好、体积很小，因此
  新增为依赖（见 `requirements-automation.txt`），而不是拼一堆不可靠的最小实现
  去凑及格线。若 psutil 不可用，一律返回"无法确认"，按保守策略处理（不清理、
  不抢占，交由人工用 `lock-status` / `unlock-stale` 排查）。
- 默认不抢占活跃锁：只有确认锁"陈旧"（进程已不存在，或 PID 被复用/创建时间不
  匹配）时，才会把旧锁归档为 `autodev.lock.stale.<timestamp>` 并原子获取新锁；
  损坏锁（JSON 解析失败/缺关键字段/仓库路径不一致）默认停止，不做任何清理。
- 不提供强制抢锁/强制终止其它进程的能力（本次任务范围明确排除）。
"""
from __future__ import annotations

import contextlib
import dataclasses
import datetime
import json
import os
import socket
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - 已在 requirements-automation.txt 声明依赖
    psutil = None  # type: ignore[assignment]

LOCK_DIR_NAME = ".autodev"
LOCK_FILE_NAME = "autodev.lock"
LOCK_VERSION = 1

# 判断"进程创建时间是否匹配"时允许的误差（秒）：不同操作系统/文件系统对时间
# 精度处理不同，过于严格的比较会把同一个进程误判为"PID 已被复用"。
_START_TIME_TOLERANCE_SECONDS = 2.0


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


class RunLockError(Exception):
    """运行锁相关的通用错误基类。"""


class RepoNotFoundError(RunLockError):
    """无法解析仓库根目录（当前目录不是 Git 仓库，或 git 不可用）。"""


class LockBusyError(RunLockError):
    """仓库已被另一个确认存活的 Auto Dev 运行占用。"""

    def __init__(self, lock_info: "LockInfo"):
        self.lock_info = lock_info
        super().__init__(
            f"仓库已被另一个 Auto Dev 运行占用：PID={lock_info.pid}，"
            f"Run ID={lock_info.run_id}，Host={lock_info.hostname}"
        )


class LockUndeterminedError(RunLockError):
    """锁文件损坏，或无法安全判断是否仍然存活（含 psutil 不可用的情况）。

    两种情况都不允许自动清理或抢占，统一归为一类"必须停止、要求人工检查"的错误，
    与 `LockBusyError`（已明确判定为活跃锁）区分开，便于上层输出不同的提示文案
    与退出码。
    """


@dataclass
class LockInfo:
    """锁文件内容的结构化表示。"""

    pid: int
    process_start_time: float | None
    autodev_start_time: str
    hostname: str
    repo_root: str
    run_id: str
    task_id: str
    command: str
    version: int = LOCK_VERSION

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LockInfo":
        required = ["pid", "autodev_start_time", "hostname", "repo_root", "run_id"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"锁文件缺少必需字段：{missing}")
        return LockInfo(
            pid=int(data["pid"]),
            process_start_time=data.get("process_start_time"),
            autodev_start_time=str(data["autodev_start_time"]),
            hostname=str(data["hostname"]),
            repo_root=str(data["repo_root"]),
            run_id=str(data["run_id"]),
            task_id=str(data.get("task_id", "")),
            command=str(data.get("command", "")),
            version=int(data.get("version", LOCK_VERSION)),
        )


@dataclass
class LockInspection:
    """`RepositoryRunLock.inspect()` 的结果：不修改锁文件，只读判断。"""

    status: str  # "free" | "active" | "stale" | "corrupted" | "unknown"
    lock_info: LockInfo | None
    detail: str = ""


def resolve_repo_root(start_path: Path | None = None) -> Path:
    """用 `git rev-parse --show-toplevel` 解析仓库根目录，锁的作用域必须绑定到
    这里返回的规范化绝对路径，而不是调用方所在的 shell 当前目录。
    """
    cwd = start_path or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RepoNotFoundError(f"无法执行 git rev-parse --show-toplevel：{exc}") from exc
    if result.returncode != 0:
        raise RepoNotFoundError(
            f"当前目录不是 Git 仓库，或 git 不可用：{(result.stderr or '').strip()}"
        )
    top = result.stdout.strip()
    if not top:
        raise RepoNotFoundError("git rev-parse --show-toplevel 返回了空路径")
    return Path(top).resolve()


def _get_process_start_time(pid: int) -> float | None:
    """返回进程创建时间（Unix 时间戳）；psutil 不可用或查询失败时返回 None。"""
    if psutil is None:
        return None
    try:
        return psutil.Process(pid).create_time()
    except Exception:  # noqa: BLE001 - psutil 可能抛出多种平台相关异常
        return None


def _process_liveness(pid: int, recorded_start_time: float | None) -> bool | None:
    """判断锁文件记录的 PID 是否仍是"同一个"仍在运行的进程。

    返回 True：确认是同一个仍在运行的进程（活跃锁）。
    返回 False：确认进程已不存在，或 PID 已被系统复用给另一个进程（陈旧锁）。
    返回 None：psutil 不可用，或无法可靠获取创建时间，无法确认——保守起见不视为
    陈旧，也不视为活跃，由上层归入"unknown"，停止并要求人工检查。
    """
    if psutil is None:
        return None
    try:
        exists = psutil.pid_exists(pid)
    except Exception:  # noqa: BLE001
        return None
    if not exists:
        return False
    if recorded_start_time is None:
        # 锁文件里没有创建时间可供比对，只能确认"这个 PID 当前存在"，无法排除
        # 它已被系统复用给另一个无关进程的可能，因此不能判定为活跃。
        return None
    current_start_time = _get_process_start_time(pid)
    if current_start_time is None:
        return None
    return abs(current_start_time - recorded_start_time) <= _START_TIME_TOLERANCE_SECONDS


class RepositoryRunLock:
    """仓库级运行锁。典型用法：

        with RepositoryRunLock(repo_root, command="python -m automation.orchestrator") as lock:
            lock.update_task("task-001")
            run_autodev()

    `acquire()` 失败时抛出 `LockBusyError`（已确认被其他活跃进程占用）或
    `LockUndeterminedError`（锁文件损坏，或无法确认是否仍然存活），调用方据此
    立即停止，不得调用 Planner/Claude/Build/Review/Commit。
    """

    def __init__(self, repo_root: Path, *, command: str = "", run_id: str | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.lock_dir = self.repo_root / LOCK_DIR_NAME
        self.lock_path = self.lock_dir / LOCK_FILE_NAME
        self.run_id = run_id or uuid.uuid4().hex[:12]
        self.command = command
        self._owned = False
        self._archived_stale_path: Path | None = None

    @property
    def archived_stale_path(self) -> Path | None:
        """本次 acquire() 过程中归档的陈旧锁路径；未发生陈旧锁清理时为 None。"""
        return self._archived_stale_path

    # ------------------------------------------------------------------
    # 只读查询
    # ------------------------------------------------------------------
    def inspect(self) -> LockInspection:
        """只读检查当前锁状态，不修改锁文件。"""
        if not self.lock_path.exists():
            return LockInspection(status="free", lock_info=None)

        try:
            raw = self.lock_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            info = LockInfo.from_dict(data)
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            return LockInspection(status="corrupted", lock_info=None, detail=f"锁文件无法解析：{exc}")

        if info.repo_root != str(self.repo_root):
            # 记录的仓库路径和当前不一致，属于异常状态：不能贸然当作"别的仓库
            # 留下的无关锁"直接忽略，按损坏锁处理，要求人工核实。
            return LockInspection(
                status="corrupted",
                lock_info=info,
                detail=f"锁文件记录的 repo_root（{info.repo_root}）与当前仓库（{self.repo_root}）不一致",
            )

        alive = _process_liveness(info.pid, info.process_start_time)
        if alive is True:
            return LockInspection(status="active", lock_info=info)
        if alive is False:
            return LockInspection(status="stale", lock_info=info, detail="进程已不存在，或 PID 已被系统复用")
        reason = "psutil 不可用" if psutil is None else "无法可靠获取/比对进程创建时间"
        return LockInspection(status="unknown", lock_info=info, detail=f"无法确认进程是否仍在运行（{reason}）")

    def is_owned(self) -> bool:
        """检查磁盘上的锁文件是否仍然是"本次 acquire() 成功创建的那把锁"。

        故意不复用 inspect() 的 active/stale/unknown 存活判定——那一套是为了
        判断"别的进程留下的锁是否还活着"，需要 psutil 核对 PID/创建时间；而这里
        判断的是"当前正在执行这段代码的进程自己创建的锁"，进程是否存活是显然的
        （就是我们自己），不需要、也不应该依赖 psutil 是否可用。只需直接读取锁
        文件内容，比对 run_id/pid/repo_root 是否与本次持有的一致即可；否则在
        psutil 缺失的环境下会出现"进程释放不了自己刚创建的锁"的连锁故障。
        """
        if not self._owned:
            return False
        if not self.lock_path.exists():
            return False
        try:
            raw = self.lock_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            info = LockInfo.from_dict(data)
        except (json.JSONDecodeError, ValueError, OSError):
            return False
        return info.run_id == self.run_id and info.pid == os.getpid() and info.repo_root == str(self.repo_root)

    # ------------------------------------------------------------------
    # 写操作
    # ------------------------------------------------------------------
    def _write_new_lock_atomic(self, info: LockInfo) -> None:
        """原子创建锁文件：O_CREAT|O_EXCL 保证同一时刻只有一个进程能创建成功，
        Windows 与 Linux 上语义一致，不依赖额外的第三方文件锁库。
        """
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(info.to_dict(), ensure_ascii=False, indent=2)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                self.lock_path.unlink()
            raise

    def _archive_stale_file(self) -> Path:
        """把当前锁文件原子重命名归档，保留排查证据，不做静默删除。"""
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
        archive_path = self.lock_dir / f"{LOCK_FILE_NAME}.stale.{stamp}"
        suffix = 0
        while archive_path.exists():
            suffix += 1
            archive_path = self.lock_dir / f"{LOCK_FILE_NAME}.stale.{stamp}.{suffix}"
        os.replace(self.lock_path, archive_path)
        return archive_path

    def acquire(self) -> LockInfo:
        """获取仓库运行锁。

        成功返回本次锁信息；失败抛出 `LockBusyError`（活跃锁）或
        `LockUndeterminedError`（损坏锁 / 无法确认是否存活）。默认不会自动抢占
        活跃锁，只有确认锁"陈旧"时才会归档旧锁后重新获取。
        """
        new_info = LockInfo(
            pid=os.getpid(),
            process_start_time=_get_process_start_time(os.getpid()),
            autodev_start_time=_now_iso(),
            hostname=socket.gethostname(),
            repo_root=str(self.repo_root),
            run_id=self.run_id,
            task_id="",
            command=self.command,
        )

        try:
            self._write_new_lock_atomic(new_info)
            self._owned = True
            return new_info
        except FileExistsError:
            pass  # 锁文件已存在，继续走下面的陈旧/活跃/损坏判定

        existing = self.inspect()

        if existing.status == "active":
            raise LockBusyError(existing.lock_info)  # type: ignore[arg-type]
        if existing.status in ("corrupted", "unknown"):
            raise LockUndeterminedError(
                f"{existing.detail}；为避免误判活跃运行，已停止获取锁，请用 "
                "`python -m automation.orchestrator lock-status` 排查，"
                "确认确实陈旧后再用 `unlock-stale` 清理。"
            )

        # status == "free"：说明刚才 O_CREAT|O_EXCL 失败是被别的进程"抢先创建又
        # 几乎同时删除"的极小概率竞态，直接重试一次原子创建。
        if existing.status == "free":
            self._write_new_lock_atomic(new_info)
            self._owned = True
            return new_info

        # status == "stale"：归档旧锁后原子获取新锁。
        self._archived_stale_path = self._archive_stale_file()
        self._write_new_lock_atomic(new_info)
        self._owned = True
        return new_info

    def update_task(self, task_id: str) -> None:
        """更新锁文件里的 task_id：写临时文件 + flush + fsync + 原子替换，避免
        写到一半被读到"半个 JSON"；只有确认锁仍属于本次 run 才会更新。
        """
        if not self.is_owned():
            return
        inspection = self.inspect()
        if inspection.lock_info is None:
            return
        info = inspection.lock_info
        info.task_id = task_id
        self._atomic_replace(info)

    def _atomic_replace(self, info: LockInfo) -> None:
        payload = json.dumps(info.to_dict(), ensure_ascii=False, indent=2)
        tmp_fd, tmp_path_str = tempfile.mkstemp(dir=str(self.lock_dir), prefix="autodev.lock.tmp-")
        tmp_path = Path(tmp_path_str)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.lock_path)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                tmp_path.unlink()
            raise

    def release(self) -> bool:
        """释放锁。只有确认锁文件仍属于本次 run_id/PID/repo_root 时才删除，
        避免删掉已被其他进程覆盖过的锁；返回是否实际执行了删除。
        """
        if not self._owned:
            return False
        if not self.is_owned():
            # 磁盘上的锁已经不是本次持有的那一把（例如被人工用 unlock-stale
            # 清理并被另一个进程重新获取），拒绝删除别人的锁。
            self._owned = False
            return False
        with contextlib.suppress(FileNotFoundError):
            self.lock_path.unlink()
        self._owned = False
        return True

    def __enter__(self) -> "RepositoryRunLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def unlock_stale(repo_root: Path) -> tuple[LockInspection, Path | None]:
    """`unlock-stale` 命令的核心逻辑：只清理已确认陈旧的锁。

    活跃锁、损坏锁、无法确认的锁都不会被修改，原样返回 `(inspect() 结果, None)`，
    由调用方负责打印相应的提示信息。清理成功时返回清理前的 inspect() 结果与
    实际归档路径。
    """
    lock = RepositoryRunLock(repo_root)
    inspection = lock.inspect()
    if inspection.status != "stale":
        return inspection, None
    archived_path = lock._archive_stale_file()  # noqa: SLF001 - 模块内部协作
    return inspection, archived_path
