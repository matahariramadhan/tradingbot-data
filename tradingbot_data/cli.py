"""Command-line entry point for the installable data workflow."""

from __future__ import annotations

import sys
from collections.abc import Callable

from scripts.audit_binance_klines import main as day_audit_main
from scripts.build_archive_manifest import main as manifest_main
from scripts.build_binance_feature_view import main as feature_view_main
from scripts.build_binance_proxy_targets import main as proxy_targets_main
from scripts.apply_proxy_boundary_recovery import main as proxy_recovery_main
from scripts.build_proxy_join import main as proxy_join_main
from scripts.build_chronological_proxy_split import main as proxy_split_main
from scripts.review_proxy_model_view import main as proxy_review_main
from scripts.build_decision_snapshot import main as snapshot_main
from scripts.inspect_binance_klines import main as inspect_main
from scripts.run_archive_audit import main as audit_main
from scripts.run_archive_batch import main as batch_main


COMMANDS: dict[str, tuple[str, Callable[[], int]]] = {
    "manifest": ("create a checksum-bearing input manifest", manifest_main),
    "audit": ("audit one input group and update its manifest", audit_main),
    "batch": ("run resumable audits for manifest groups", batch_main),
    "feature-view": ("build gap-aware Binance feature rows", feature_view_main),
    "day-audit": ("audit one input's Binance day coverage", day_audit_main),
    "proxy-targets": ("build Binance proxy targets", proxy_targets_main),
    "proxy-recover": ("apply verified proxy boundary recovery", proxy_recovery_main),
    "proxy-join": ("join features to proxy targets safely", proxy_join_main),
    "proxy-split": ("build a chronological proxy split report", proxy_split_main),
    "proxy-review": ("review proxy model-view quality", proxy_review_main),
    "snapshot": ("build one as-of feature snapshot", snapshot_main),
    "inspect": ("inspect closed one-second klines", inspect_main),
}


def print_help() -> None:
    print("Usage: tradingbot-data <command> [command options]")
    print("\nCommands:")
    for name, (description, _) in COMMANDS.items():
        print(f"  {name:14} {description}")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print_help()
        return 0

    command = sys.argv[1]
    selected = COMMANDS.get(command)
    if selected is None:
        print(f"Unknown command: {command}\n")
        print_help()
        return 2

    sys.argv = [f"tradingbot-data {command}", *sys.argv[2:]]
    return selected[1]()
