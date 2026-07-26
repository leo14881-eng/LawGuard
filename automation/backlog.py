"""Product Backlog 的机器可读镜像（2026-07-26 新增）。

背景：2026-07-26 的 Project Audit 口头识别出多个尚未开发的高价值方向，但从未
落盘为 Planner 可消费的正式文档；随后 Task #14 中 Planner 判断"当前没有满足
Value Gate 的候选任务"，根因之一就是没有一份权威的"已确认高价值缺口清单"可用，
只能在已饱和模块里打转、最终把"没有高价值任务"误报为阻塞信号。

唯一权威描述见 `LAWGUARD_SOT.md` 第 21 节；本模块只是把该章节的结构化字段
（ID/标题/状态/优先级/是否允许 Auto Dev/切片）转成 Python 数据，供
`context_loader.build_planner_context()` 注入 Planner 上下文、供
`orchestrator.py` 做"Backlog First"强制校验。修改 Backlog 内容时，必须同步
更新 `LAWGUARD_SOT.md` 第 21 节与本文件，两者保持一致。

本模块不做 ValueScore 计分、不做重复检测——那是 `automation/value_gate.py` 的
职责，两者是互补而非重叠的两层：Backlog 回答"应该做什么、优先做什么"，
Value Gate 回答"这个候选任务本身够不够格被执行"。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

BACKLOG_STATUSES = {"READY", "IN_PROGRESS", "DONE", "BLOCKED", "DEFERRED"}


@dataclass(frozen=True)
class BacklogSlice:
    """大型 Backlog 条目下的一个可独立交付、可验证的垂直切片。"""

    slice_id: str
    title: str


@dataclass(frozen=True)
class BacklogItem:
    """对应 LAWGUARD_SOT.md 第 21.2 节的一个 Backlog 条目。"""

    backlog_id: str
    title: str
    status: str  # READY / IN_PROGRESS / DONE / BLOCKED / DEFERRED
    priority: str  # P0 / P1 / P2
    allow_auto_dev: bool
    user_problem: str
    goal: str
    core_value: str
    scope: str
    non_goals: str
    risk: str
    acceptance_criteria: str
    dependencies: str
    slices: tuple[BacklogSlice, ...] = ()


BACKLOG: tuple[BacklogItem, ...] = (
    BacklogItem(
        backlog_id="BL-001", title="交互式个人处境导航工具",
        status="READY", priority="P0", allow_auto_dev=True,
        user_problem="当事人/家属不知道自己的情况大致对应哪个诉讼阶段、该看哪个权利指引",
        goal="基于已有 stages.ts/rightsGuide.ts 静态数据，提供引导式问答，映射到对应阶段/权利指引入口",
        core_value="直接提升紧急场景下的可执行性与权利理解",
        scope="纯前端状态机 + 已有数据映射，不新增法律内容",
        non_goals="不判断案件是否合法/是否构成犯罪；不生成个案化建议；不替代律师意见",
        risk="问答设计不当可能让用户误以为在获得个案诊断，需在文案中明确禁止诊断式措辞",
        acceptance_criteria="3 步内到达结果页；结果页含至少 1 个阶段入口与 1 个权利指引入口；含免责声明；npm run build 通过",
        dependencies="无",
    ),
    BacklogItem(
        backlog_id="BL-002", title="官方求助渠道省级查询入口（骨架）",
        status="READY", priority="P0", allow_auto_dev=True,
        user_problem="用户不知道所在省份具体应联系哪个司法行政机关/法律援助中心",
        goal="OfficialChannelsView 新增按省份筛选骨架，展示已核验全国性渠道，未核验省份标注待核验占位",
        core_value="直接提升官方求助能力",
        scope="前端筛选交互 + 占位数据结构，不新增任何未经核验的具体机构名称/电话",
        non_goals="不编造/推断各省具体法律援助中心联系方式；不做地理定位",
        risk="如果顺手填入未核验的具体机构信息将直接违反 P0",
        acceptance_criteria="省份选择控件可用；未核验省份统一显示待核验状态；全国性渠道内容未被误改；npm run build 通过",
        dependencies="各省具体机构名称/电话的可核验官方来源（当前不存在）",
    ),
    BacklogItem(
        backlog_id="BL-003", title="本地全文搜索",
        status="READY", priority="P1", allow_auto_dev=True,
        user_problem="用户记得某个关键词但不知道该词出现在哪个页面",
        goal="对已发布静态内容建立本地索引，提供搜索入口与结果列表，支持高亮与跳转",
        core_value="提升内容查找与可及性",
        scope="纯前端本地索引，不接入后端搜索服务",
        non_goals="不做模糊语义搜索/AI 问答式检索",
        risk="索引需保留内容原有的待法律复核等状态标注",
        acceptance_criteria="见 LAWGUARD_SOT.md 21.3 节切片验收标准",
        dependencies="无",
        slices=(
            BacklogSlice("BL-003-1", "建立内容索引"),
            BacklogSlice("BL-003-2", "提供搜索入口与结果列表"),
            BacklogSlice("BL-003-3", "支持关键词高亮与结果跳转"),
            BacklogSlice("BL-003-4", "无结果状态与测试"),
        ),
    ),
    BacklogItem(
        backlog_id="BL-004", title="简明语言 / 大字版模式",
        status="READY", priority="P1", allow_auto_dev=True,
        user_problem="部分家属（尤其年长者）对当前字号、术语密度感到阅读困难",
        goal="新增可全局切换的大字版显示模式，复用现有 Design Tokens 等比放大",
        core_value="提升可及性/易读性",
        scope="纯 CSS/Design Token 层面显示模式切换，不修改法律内容文本",
        non_goals="不重写文案为简化版法律内容",
        risk="需确保切换状态可被键盘/屏幕阅读器识别",
        acceptance_criteria="提供可发现的切换入口；切换后正文字号提升且不破坏布局；375px 无横向滚动；npm run build 通过",
        dependencies="无",
    ),
    BacklogItem(
        backlog_id="BL-005", title="PWA 离线支持",
        status="READY", priority="P1", allow_auto_dev=True,
        user_problem="用户在信号不佳场所无法访问已经看过的页面内容",
        goal="新增 Web App Manifest 与 Service Worker，缓存已发布静态页面，支持离线重新访问",
        core_value="提升离线可用性",
        scope="纯前端构建产物缓存策略",
        non_goals="不做后台推送通知；不做离线数据同步",
        risk="需明确离线状态提示，避免误以为是实时更新内容",
        acceptance_criteria="见 LAWGUARD_SOT.md 21.3 节切片验收标准",
        dependencies="无",
        slices=(
            BacklogSlice("BL-005-1", "接入 Web App Manifest"),
            BacklogSlice("BL-005-2", "接入 Service Worker 基础缓存"),
            BacklogSlice("BL-005-3", "离线状态提示"),
            BacklogSlice("BL-005-4", "离线场景测试"),
        ),
    ),
    BacklogItem(
        backlog_id="BL-006", title="Legal Sources 法律来源内容深化核验",
        status="BLOCKED", priority="P0", allow_auto_dev=False,
        user_problem="Legal Sources 页面内容层面完成度约 60%，多项来源尚未标注可核验官方出处",
        goal="为现有法律依据条目补全官方来源链接、发布日期、最后核验日期",
        core_value="直接提升权利理解的可信度",
        scope="仅补全可核验来源的条目，不推断/编造条文内容",
        non_goals="不新增法律解释性文字（除非同样有可核验来源支撑）",
        risk="无来源硬填会直接违反 P0",
        acceptance_criteria="待来源确定后另行制定",
        dependencies="人工提供官方公开文本/官方门户链接",
    ),
    BacklogItem(
        backlog_id="BL-007", title="Documents 文书核对清单内容扩充",
        status="BLOCKED", priority="P0", allow_auto_dev=False,
        user_problem="DocumentsView 目前仅有通用框架，具体清单条目不足",
        goal="在已核验的法律依据基础上扩充具体文书核对条目",
        core_value="提升程序核对的可执行性",
        scope="仅在已有法律依据可核验时新增条目",
        non_goals="不生成个案化的文书审查意见",
        risk="与 BL-006 相同的来源风险",
        acceptance_criteria="待来源确定后另行制定",
        dependencies="人工提供官方公开文本/官方门户链接",
    ),
    BacklogItem(
        backlog_id="BL-008", title="首屏性能优化技术预研",
        status="DEFERRED", priority="P2", allow_auto_dev=True,
        user_problem="Performance 约 70%，尚未系统性测量/优化",
        goal="引入构建产物体积分析、关键渲染路径测量，输出优化建议清单",
        core_value="非核心增强/技术预研",
        scope="测量与建议清单，不直接产出面向用户的新功能",
        non_goals="不在本条目内直接大改业务代码",
        risk="低",
        acceptance_criteria="待安排时另行制定",
        dependencies="无",
    ),
)


def get_completed_backlog_ids(runtime_dir: Path) -> set[str]:
    """扫描 automation/runtime/*/run_report.json，返回全部已被真实执行证明"完成"
    的 backlog_id/切片 ID 集合。

    唯一判断依据是真实运行产物：`final_status == "COMMITTED"` 且该次任务的
    `task.backlog_id` 有值——不依赖标题匹配、不依赖模型自述、不做任何推断。
    目录不存在或文件缺失/损坏时按"无证据"处理（跳过该条记录，不计入已完成），
    绝不会因为"读不到数据"就反过来猜测某条目已完成，这是本函数"不允许猜测"
    要求的具体落实：证据不足 = 保持保守，不代表可以脑补。
    """
    completed: set[str] = set()
    if not runtime_dir.exists():
        return completed
    for run_dir in runtime_dir.iterdir():
        if not run_dir.is_dir():
            continue
        report_path = run_dir / "run_report.json"
        if not report_path.exists():
            continue
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("final_status") != "COMMITTED":
            continue
        task = data.get("task")
        if not isinstance(task, dict):
            continue
        bid = task.get("backlog_id")
        if isinstance(bid, str) and bid.strip():
            completed.add(bid.strip())
    return completed


def is_item_completed(item: BacklogItem, completed_ids: set[str]) -> bool:
    """判断一个 Backlog 条目本身是否应被视为"已完成"（从而从 READY 列表中过滤）。

    - 未拆分切片的条目（如 BL-001）：其自身 ID 出现在已完成集合中即视为完成。
    - 已拆分切片的条目（如 BL-003/BL-005）：必须全部切片 ID 都出现在已完成
      集合中才视为整条完成——只完成部分切片时，条目本身应继续留在 READY 列表，
      供 Planner 挑选下一个尚未完成的切片，而不是被整体误判为"做完了"。
    """
    if item.slices:
        return all(s.slice_id in completed_ids for s in item.slices)
    return item.backlog_id in completed_ids


def get_ready_items(runtime_dir: Path | None = None) -> list[BacklogItem]:
    """返回状态为 READY、允许 Auto Dev、且尚未被真实执行记录证明已完成的条目，
    按优先级（P0>P1>P2）再按 ID 排序。

    runtime_dir 缺省时使用 automation/config.py 的 RUNTIME_DIR（延迟导入，避免
    模块加载时的循环依赖）；调用方（如 orchestrator.py）已持有自己的 RUNTIME_DIR
    时应显式传入，保持与其它模块（如 value_gate.load_recent_tasks）一致的用法，
    也便于测试注入临时目录。
    """
    if runtime_dir is None:
        from automation.config import RUNTIME_DIR as _default_runtime_dir
        runtime_dir = _default_runtime_dir
    completed_ids = get_completed_backlog_ids(runtime_dir)
    items = [
        b for b in BACKLOG
        if b.status == "READY" and b.allow_auto_dev and not is_item_completed(b, completed_ids)
    ]
    return sorted(items, key=lambda b: (PRIORITY_ORDER.get(b.priority, 99), b.backlog_id))


def has_ready_item(runtime_dir: Path | None = None) -> bool:
    """Backlog First 核心判断：是否存在可以立即规划的 READY 条目（已过滤掉已完成的）。"""
    return bool(get_ready_items(runtime_dir))


def get_item(backlog_id: str) -> BacklogItem | None:
    for item in BACKLOG:
        if item.backlog_id == backlog_id:
            return item
    return None


def all_valid_references() -> set[str]:
    """全部合法的 backlog_id 取值：条目 ID 本身 + 其下每个切片 ID。"""
    refs: set[str] = set()
    for item in BACKLOG:
        refs.add(item.backlog_id)
        for s in item.slices:
            refs.add(s.slice_id)
    return refs


def is_valid_reference(backlog_id: str) -> bool:
    return backlog_id in all_valid_references()


def build_planner_backlog_context(runtime_dir: Path | None = None) -> str:
    """生成供 Planner 上下文使用的 Backlog 文本：Backlog First 规则说明 + 全部条目。"""
    if runtime_dir is None:
        from automation.config import RUNTIME_DIR as _default_runtime_dir
        runtime_dir = _default_runtime_dir
    completed_ids = get_completed_backlog_ids(runtime_dir)
    ready = get_ready_items(runtime_dir)
    lines = [
        "## Product Backlog First 规则（权威来源：LAWGUARD_SOT.md 第 21 节）",
        "存在下方 READY 且允许 Auto Dev 的条目时，必须优先从中选择优先级最高者规划",
        "第一个可交付切片，不得返回 risk_level=NO_HIGH_VALUE_TASK 或 BLOCKED，不得绕过",
        "Backlog 临时制造低价值任务；生成任务时必须在 backlog_id 字段填写来源条目 ID",
        "（大型条目下的某个切片，写成如 'BL-003-1' 的切片编号）。只有当下方不存在任何",
        "READY 条目时，才可以考虑 risk_level=NO_HIGH_VALUE_TASK。",
        "",
    ]
    if ready:
        lines.append("### 当前 READY（按优先级排序，必须优先从此列表选择）")
        for item in ready:
            slice_text = "；".join(f"{s.slice_id}：{s.title}" for s in item.slices) or "（无需拆分，单一切片）"
            lines.append(
                f"- {item.backlog_id}（{item.priority}）：{item.title}\n"
                f"  用户问题：{item.user_problem}\n"
                f"  目标：{item.goal}\n"
                f"  非目标：{item.non_goals}\n"
                f"  建议切片：{slice_text}"
            )
    else:
        lines.append("### 当前 READY 条目：无")

    others = [b for b in BACKLOG if b.backlog_id not in {r.backlog_id for r in ready}]
    if others:
        lines.append("\n### 其它条目（非 READY，仅供参考，不得选择）")
        for item in others:
            # 条目在 BACKLOG 静态数据里状态字段仍是 READY，但已被真实运行记录
            # （automation/runtime/*/run_report.json 中 final_status=COMMITTED）
            # 证明完成——显式标注"已完成"，不要让 Planner 误以为原始 READY 标签
            # 仍然有效、可以重新选择同一个条目。
            display_status = (
                "已完成（有真实执行记录，不得再次选择）"
                if item.status == "READY" and is_item_completed(item, completed_ids)
                else item.status
            )
            lines.append(f"- {item.backlog_id}（状态：{display_status}，优先级：{item.priority}）：{item.title}")

    return "\n".join(lines)
