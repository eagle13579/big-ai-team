from typing import Any

from src.shared.logging import logger


class ResultAggregator:
    """结果聚合器 - 多Agent结果合并+去重+一致性检查"""

    def aggregate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """聚合多个Agent的结果"""
        if not results:
            return {"status": "empty", "data": None}

        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") != "success"]

        if not successful:
            return {
                "status": "failed",
                "data": None,
                "errors": [r.get("error", "未知错误") for r in failed],
                "total": len(results),
                "failed": len(failed),
            }

        merged_data = self._merge_results(successful)
        consistency = self._check_consistency(successful)

        aggregated = {
            "status": "success" if consistency["consistent"] else "partial",
            "data": merged_data,
            "metadata": {
                "total_results": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "consistency_score": consistency["score"],
            },
        }

        if not consistency["consistent"]:
            aggregated["warnings"] = consistency["issues"]

        logger.info(
            f"📊 结果聚合: {len(successful)}/{len(results)} 成功, "
            f"一致性: {consistency['score']:.1%}"
        )

        return aggregated

    def _merge_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """合并成功的结果"""
        merged: dict[str, Any] = {}

        for result in results:
            data = result.get("data", result.get("result", {}))

            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in merged:
                        merged[key] = value
                    elif isinstance(merged[key], list) and isinstance(value, list):
                        merged[key].extend(value)
                    elif isinstance(merged[key], dict) and isinstance(value, dict):
                        merged[key].update(value)
                    else:
                        merged[f"{key}_{result.get('agent_id', 'unknown')}"] = value
            elif isinstance(data, str):
                if "content" not in merged:
                    merged["content"] = []
                merged["content"].append({"agent_id": result.get("agent_id"), "text": data})
            else:
                if "results" not in merged:
                    merged["results"] = []
                merged["results"].append(data)

        return merged

    def _check_consistency(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """检查结果一致性"""
        if len(results) <= 1:
            return {"consistent": True, "score": 1.0, "issues": []}

        issues = []

        data_values = []
        for r in results:
            data = r.get("data", r.get("result"))
            if isinstance(data, dict):
                data_values.append(str(sorted(data.items())))
            elif data is not None:
                data_values.append(str(data))

        unique_values = set(data_values)
        if len(unique_values) > 1:
            consistency_score = 1.0 - (len(unique_values) - 1) / len(data_values)
            issues.append(f"结果不一致: {len(unique_values)} 种不同结果")
        else:
            consistency_score = 1.0

        return {
            "consistent": consistency_score >= 0.8,
            "score": consistency_score,
            "issues": issues,
        }
