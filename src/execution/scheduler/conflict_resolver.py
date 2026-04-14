from typing import Any

from src.shared.logging import logger


class ConflictResolver:
    """冲突解决器 - 基于置信度+权威度+时效性的冲突消解"""

    def resolve(self, conflicting_results: list[dict[str, Any]]) -> dict[str, Any]:
        """解决冲突的结果"""
        if not conflicting_results:
            return {"status": "no_data", "data": None}

        if len(conflicting_results) == 1:
            return conflicting_results[0]

        scored_results = []
        for result in conflicting_results:
            score = self._calculate_resolution_score(result)
            scored_results.append((score, result))

        scored_results.sort(key=lambda x: x[0], reverse=True)

        winner_score, winner = scored_results[0]

        resolution = {
            "status": "resolved",
            "data": winner.get("data", winner.get("result")),
            "resolution_method": "score_based",
            "winner_agent": winner.get("agent_id", "unknown"),
            "winner_score": winner_score,
            "conflict_count": len(conflicting_results),
            "alternatives": [
                {
                    "agent_id": r.get("agent_id", "unknown"),
                    "score": s,
                    "data_preview": str(r.get("data", r.get("result", "")))[:100],
                }
                for s, r in scored_results[1:3]
            ],
        }

        logger.info(
            f"⚖️ 冲突解决: {len(conflicting_results)} 个冲突结果, "
            f"胜出: {winner.get('agent_id', 'unknown')} (分数: {winner_score:.2f})"
        )

        return resolution

    def _calculate_resolution_score(self, result: dict[str, Any]) -> float:
        """计算结果的可信度评分"""
        score = 0.0

        confidence = result.get("confidence", 0.5)
        score += confidence * 0.4

        authority = result.get("authority", 0.5)
        score += authority * 0.3

        recency = result.get("recency", 0.5)
        score += recency * 0.2

        verification = result.get("verified", False)
        if verification:
            score += 0.1

        return min(score, 1.0)
