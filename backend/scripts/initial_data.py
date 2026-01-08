import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlmodel import Session

from app.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
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


def get_migration_revision_from_file(file_path: Path) -> str | None:
    """从迁移文件中提取 revision ID"""
    try:
        content = file_path.read_text(encoding="utf-8")
        match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
    except Exception as e:
        logger.warning(f"读取迁移文件 {file_path} 时出错: {e}")
    return None


def get_all_valid_revisions(versions_dir: Path) -> set[str]:
    """获取所有有效的迁移版本号"""
    revisions = set()
    if versions_dir.exists():
        for file_path in versions_dir.glob("*.py"):
            revision = get_migration_revision_from_file(file_path)
            if revision:
                revisions.add(revision)
    return revisions


def find_head_revision(versions_dir: Path) -> str | None:
    """找到迁移链的 head 版本"""
    if not versions_dir.exists():
        return None
    
    # 构建版本依赖图
    revisions = {}  # revision -> down_revision
    all_revisions = set()
    
    for file_path in versions_dir.glob("*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
            revision_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
            down_revision_match = re.search(r"down_revision\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", content)
            
            if revision_match:
                revision = revision_match.group(1)
                all_revisions.add(revision)
                if down_revision_match:
                    down_revision = down_revision_match.group(1) if down_revision_match.group(1) else None
                else:
                    down_revision = None
                revisions[revision] = down_revision
        except Exception:
            continue
    
    if not revisions:
        return None
    
    # 找到 head：没有任何其他版本的 down_revision 指向它
    head_candidates = []
    for revision, _down_revision in revisions.items():
        # 检查是否有其他版本指向这个版本
        is_referenced = any(
            rev != revision and down_rev == revision
            for rev, down_rev in revisions.items()
        )
        if not is_referenced:
            head_candidates.append(revision)
    
    # 如果有多个候选，返回第一个（实际应该通过时间戳判断，这里简化）
    if head_candidates:
        return head_candidates[0]
    
    # 如果找不到 head，返回第一个版本
    return list(all_revisions)[0] if all_revisions else None


def fix_alembic_version_if_needed() -> None:
    """修复 alembic_version 表，如果记录的版本不存在则修复为最新的有效版本"""
    try:
        with engine.connect() as conn:
            # 检查 alembic_version 表是否存在
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
            ))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("alembic_version 表不存在，无需修复")
                return
            
            # 获取数据库中记录的版本
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            db_version = result.scalar()
            
            if not db_version:
                logger.info("alembic_version 表中没有版本记录，无需修复")
                return
            
            # 获取所有有效的迁移版本
            versions_dir = Path("app/alembic/versions")
            valid_revisions = get_all_valid_revisions(versions_dir)
            
            if db_version in valid_revisions:
                logger.info(f"数据库中的版本 {db_version} 有效，无需修复")
                return
            
            # 数据库中记录的版本不存在，需要修复
            logger.warning(f"⚠️  数据库中记录的版本 {db_version} 不存在于迁移文件中，需要修复")
            
            if not valid_revisions:
                # 如果没有有效的迁移文件，删除 alembic_version 记录
                logger.info("未找到有效的迁移文件，清空 alembic_version 表")
                conn.execute(text("DELETE FROM alembic_version"))
                conn.commit()
                return
            
            # 找到 head 版本
            head_revision = find_head_revision(versions_dir)
            
            if head_revision:
                logger.info(f"修复 alembic_version: {db_version} -> {head_revision}")
                conn.execute(text("UPDATE alembic_version SET version_num = :new_version"), {"new_version": head_revision})
                conn.commit()
            else:
                # 如果找不到 head，使用第一个找到的有效版本
                latest_revision = list(valid_revisions)[0]
                logger.info(f"修复 alembic_version: {db_version} -> {latest_revision} (使用第一个有效版本)")
                conn.execute(text("UPDATE alembic_version SET version_num = :new_version"), {"new_version": latest_revision})
                conn.commit()
    except Exception as e:
        logger.warning(f"修复 alembic_version 时出错: {e}")
        # 不抛出异常，让后续流程继续


def ensure_migrations_and_upgrade() -> None:
    """确保迁移与数据库状态一致：
    - 若迁移目录为空：创建初始自生成迁移并升级到 head；
    - 若已有迁移：检查是否有新的模型变更，如有则生成新迁移并升级。
    """
    versions_dir_str = os.path.join("app", "alembic", "versions")
    versions_dir = Path(versions_dir_str)
    os.makedirs(versions_dir_str, exist_ok=True)

    has_migrations = False
    try:
        files = [f for f in os.listdir(versions_dir_str) if f.endswith(".py")]
        has_migrations = len(files) > 0
    except Exception:
        has_migrations = False

    if not has_migrations:
        # 没有任何迁移文件：清理数据库中的迁移记录并重新开始
        logger.info("未找到迁移文件，清理数据库迁移记录")
        try:
            # 尝试删除 alembic_version 表（如果存在）
            with engine.connect() as conn:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                conn.commit()
            logger.info("已清理 alembic_version 表")
        except Exception as e:
            logger.warning(f"无法清理 alembic_version 表: {e}")

        # 生成初始迁移并升级
        ts = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
        run_cmd(["alembic", "revision", "--autogenerate", "-m", f"initial_migration_{ts}"])
        run_cmd(["alembic", "upgrade", "head"])
        return

    # 已有迁移：先检查并修复 alembic_version 表（如果记录了不存在的版本）
    logger.info("检查 alembic_version 表状态")
    fix_alembic_version_if_needed()
    
    # 先确保数据库已应用所有现有迁移（重要：必须在 autogenerate 之前）
    # 如果数据库是空的，这会创建 alembic_version 表并应用所有迁移
    logger.info("确保数据库已应用所有现有迁移")
    try:
        run_cmd(["alembic", "upgrade", "head"])
    except Exception as e:
        logger.warning(f"应用现有迁移时出错（可能数据库是空的）: {e}")
        # 如果失败，可能是数据库完全为空，继续尝试 autogenerate
    
    # 检查是否有新的模型变更
    logger.info("检查是否有新的模型变更")
    
    # 注意：Alembic 没有直接的方法在不生成文件的情况下检查是否有变更
    # 即使模型没有变更，Alembic 的 --autogenerate 也会生成一个空迁移文件（只有 pass）
    # 所以我们采用：先生成迁移文件，然后检查是否为空，如果为空则删除
    # 这是目前最实用的方法，因为 Alembic 的 Python API 配置复杂且不够稳定
    
    # 记录生成迁移前的文件列表
    files_before = set(versions_dir.glob("*.py")) if versions_dir.exists() else set()
    
    # 生成新的迁移文件
    ts = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
    migration_message = f"model_changes_{ts}"
    
    logger.info(f"+ alembic revision --autogenerate -m {migration_message}")
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", migration_message],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        logger.info(result.stdout)
    if result.stderr:
        logger.warning(result.stderr)
    
    # 检查是否生成了新文件
    if versions_dir.exists():
        files_after = set(versions_dir.glob("*.py"))
        new_files = files_after - files_before
        
        if new_files:
            # 检查新生成的迁移文件是否为空，如果为空则删除
            valid_migrations = []
            for migration_file in new_files:
                if is_empty_migration(migration_file):
                    logger.info(f"⚠️  检测到空迁移文件（无模型变更），已删除: {migration_file.name}")
                    migration_file.unlink()  # 删除空迁移文件
                else:
                    valid_migrations.append(migration_file)
                    logger.info(f"✅ 检测到模型变更，已生成新迁移: {migration_file.name}")
            
            if valid_migrations:
                # 如果有新的有效迁移，应用它们
                logger.info("应用新生成的迁移")
                run_cmd(["alembic", "upgrade", "head"])
            else:
                logger.info("未检测到模型变更")
        else:
            logger.info("未检测到模型变更")


def init() -> None:
    with Session(engine) as session:
        init_db(session)


def main() -> None:
    logger.info("准备数据库迁移")
    ensure_migrations_and_upgrade()
    logger.info("创建初始数据")
    init()
    logger.info("初始数据创建完成")


if __name__ == "__main__":
    main()
