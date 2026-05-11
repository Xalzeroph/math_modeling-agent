#!/usr/bin/env python3
"""
创建题目文件夹

用法:
  python tools/workspace_setup.py "2026-数维杯-A-磁悬浮"
  python tools/workspace_setup.py "2026-数维杯-A-磁悬浮" --description "抱轨式磁浮列车故障检测"
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "tools" / "workspace_setup.py").exists():
            return d
        d = d.parent
    return Path.cwd()


SESSION_DIRS = [
    "data", "solvers", "verifications", "figures",
    "paper", "notes", "output",
]


def create_session(root: Path, name: str, description: str = "") -> Path:
    session_dir = root / "sessions" / name
    session_dir.mkdir(parents=True, exist_ok=True)

    for d in SESSION_DIRS:
        (session_dir / d).mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # progress.md — 对话推进日志
    (session_dir / "progress.md").write_text(
        f"# {name}\n\n"
        f"- **创建时间**: {now}\n"
        f"- **当前阶段**: init\n\n"
        f"## 题目描述\n{description}\n\n"
        f"## 阶段记录\n\n",
        encoding="utf-8"
    )

    # README.md — 最终总结（进化后自动填充）
    (session_dir / "README.md").write_text(
        f"# {name}\n\n"
        f"- **日期**: {now}\n\n"
        f"## 模型\n\n*(建模完成后进化引擎自动填充)*\n\n"
        f"## 算法\n\n*(建模完成后进化引擎自动填充)*\n\n"
        f"## 结果\n\n*(建模完成后进化引擎自动填充)*\n\n"
        f"## 教训\n\n*(建模完成后进化引擎自动填充)*\n",
        encoding="utf-8"
    )

    print(json.dumps({
        "status": "ok",
        "session": name,
        "目录": str(session_dir),
        "提示": "把题目PDF和数据放进去，然后对Claude Code说'帮我做这道题'",
    }, ensure_ascii=False))
    return session_dir


def main():
    parser = argparse.ArgumentParser(description="创建题目文件夹")
    parser.add_argument("name", help="题目名称，如 '2026-数维杯-A-磁悬浮'")
    parser.add_argument("--description", default="", help="题目简述（可选）")
    args = parser.parse_args()

    root = _resolve_root()
    create_session(root, args.name, args.description)


if __name__ == "__main__":
    main()
