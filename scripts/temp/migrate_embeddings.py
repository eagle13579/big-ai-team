#!/usr/bin/env python3
"""
迁移嵌入向量到统一的128维
"""

import json
import os
import sys
from pathlib import Path

import numpy as np

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def migrate_embeddings():
    """迁移嵌入向量"""
    print("=== 嵌入向量迁移工具 ===\n")

    palace_path = os.path.expanduser("~/.mempalace/palace")
    embeddings_file = Path(palace_path) / "embeddings.json"

    if not embeddings_file.exists():
        print("✗ 嵌入向量文件不存在")
        return

    # 加载现有嵌入
    with open(embeddings_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"✓ 加载了 {len(data)} 个嵌入向量")

    # 统计维度
    dim_stats = {}
    for memory_id, embedding in data.items():
        dim = len(embedding)
        dim_stats[dim] = dim_stats.get(dim, 0) + 1

    print(f"✓ 维度分布: {dim_stats}")

    # 迁移到128维
    migrated_data = {}
    for memory_id, embedding in data.items():
        old_dim = len(embedding)

        if old_dim == 128:
            # 已经是128维，直接保留
            migrated_data[memory_id] = embedding
        elif old_dim == 256:
            # 从256维降到128维（取前128维）
            migrated_data[memory_id] = embedding[:128]
        else:
            # 其他维度，需要重新生成或填充
            new_embedding = np.zeros(128)
            min_dim = min(old_dim, 128)
            new_embedding[:min_dim] = embedding[:min_dim]

            # 归一化
            norm = np.linalg.norm(new_embedding)
            if norm > 0:
                new_embedding = new_embedding / norm

            migrated_data[memory_id] = new_embedding.tolist()

    # 备份原文件
    backup_file = embeddings_file.with_suffix(".json.backup")
    embeddings_file.rename(backup_file)
    print(f"✓ 原文件已备份到: {backup_file}")

    # 保存迁移后的数据
    with open(embeddings_file, "w", encoding="utf-8") as f:
        json.dump(migrated_data, f, indent=2, ensure_ascii=False)

    print(f"✓ 迁移完成，保存了 {len(migrated_data)} 个嵌入向量")
    print("✓ 所有嵌入向量已统一为128维")


if __name__ == "__main__":
    migrate_embeddings()
