#!/usr/bin/env python3
"""
数据库更新脚本
用于在修改数据模型后自动更新数据库结构
"""

import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """运行命令并记录日志"""
    logger.info("+ %s", " ".join(cmd))
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def is_empty_migration(file_path: Path) -> bool:
    """检查迁移文件是否为空（只有 pass）"""
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # 检查是否包含实际的迁移操作（如 op.create_table, op.add_column 等）
        # 如果没有任何迁移操作，就是空迁移
        migration_operations = [
            "op.create_table",
            "op.drop_table",
            "op.add_column",
            "op.drop_column",
            "op.alter_column",
            "op.create_index",
            "op.drop_index",
            "op.create_unique_constraint",
            "op.drop_constraint",
            "op.execute",
        ]
        
        # 检查是否包含任何迁移操作
        has_operations = any(op in content for op in migration_operations)
        
        # 如果没有迁移操作，检查 upgrade() 函数是否只有 pass
        if not has_operations:
            # 提取 upgrade() 函数的内容
            upgrade_match = re.search(r"def upgrade\(\):.*?(?=def downgrade|$)", content, re.DOTALL)
            if upgrade_match:
                upgrade_body = upgrade_match.group(0)
                # 移除注释和空行，检查是否只有 pass
                upgrade_lines = [
                    line.strip() 
                    for line in upgrade_body.splitlines() 
                    if line.strip() and not line.strip().startswith("#")
                ]
                # 过滤掉 def upgrade(): 这一行
                upgrade_lines = [line for line in upgrade_lines if "def upgrade():" not in line]
                # 如果只有 pass，说明是空迁移
                if len(upgrade_lines) == 1 and "pass" in upgrade_lines[0]:
                    return True
        
        return False
    except Exception as e:
        logger.warning(f"检查迁移文件时出错: {e}")
        return False


def update_database() -> None:
    """更新数据库结构"""
    logger.info("开始更新数据库结构")
    
    # 记录生成迁移前的文件列表
    versions_dir = Path("app/alembic/versions")
    if versions_dir.exists():
        files_before = set(versions_dir.glob("*.py"))
    else:
        files_before = set()
    
    # 生成新的迁移文件（不使用check=True，因为即使没有变更也可能生成空文件）
    ts = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", f"model_changes_{ts}"],
            capture_output=True,
            text=True
        )
        logger.info("+ %s", " ".join(["alembic", "revision", "--autogenerate", "-m", f"model_changes_{ts}"]))
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
    except Exception as e:
        logger.warning(f"运行alembic revision命令时出错（可能没有变更）: {e}")
    
    # 无论命令成功与否，都检查是否生成了新文件
    if versions_dir.exists():
        files_after = set(versions_dir.glob("*.py"))
        new_files = files_after - files_before
        
        if new_files:
            # 检查新生成的迁移文件是否为空
            valid_migrations = []
            for migration_file in new_files:
                if is_empty_migration(migration_file):
                    logger.info(f"⚠️  检测到空迁移文件（无模型变更），已删除: {migration_file.name}")
                    migration_file.unlink()  # 删除空迁移文件
                else:
                    valid_migrations.append(migration_file)
                    logger.info(f"✅ 已生成新的迁移文件: {migration_file.name}")
            
            if valid_migrations:
                # 如果有有效的迁移，应用它们
                try:
                    run_cmd(["alembic", "upgrade", "head"])
                    logger.info("✅ 数据库结构更新完成")
                except Exception as e:
                    logger.error(f"❌ 应用迁移失败: {e}")
                    raise
            else:
                logger.info("ℹ️  未检测到模型变更，数据库已是最新状态")
        else:
            logger.info("ℹ️  未生成新的迁移文件，数据库已是最新状态")
    else:
        logger.info("ℹ️  未生成新的迁移文件，数据库已是最新状态")


def main() -> None:
    """主函数"""
    logger.info("🚀 数据库更新工具")
    logger.info("=" * 50)
    
    try:
        update_database()
        logger.info("=" * 50)
        logger.info("🎉 数据库更新成功完成！")
    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"💥 数据库更新失败: {e}")
        exit(1)


if __name__ == "__main__":
    main()
