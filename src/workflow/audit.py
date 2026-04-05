from typing import Dict, Any, List


class ParityAudit:
    """多语言一致性审计"""
    
    def __init__(self):
        pass
    
    def audit(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行审计"""
        # 检查多语言一致性
        languages = self._detect_languages(content)
        consistency_score = self._calculate_consistency(content, languages)
        
        return {
            "languages": languages,
            "consistency_score": consistency_score,
            "issues": self._identify_issues(content, languages),
            "status": "completed" if consistency_score > 0.8 else "needs_attention"
        }
    
    def _detect_languages(self, content: Dict[str, Any]) -> List[str]:
        """检测内容中的语言"""
        # 简单的语言检测逻辑
        languages = set()
        
        def traverse(data):
            if isinstance(data, str):
                # 简单的中文字符检测
                if any("\u4e00" <= char <= "\u9fff" for char in data):
                    languages.add("Chinese")
                # 简单的英文字符检测
                if any("a" <= char.lower() <= "z" for char in data):
                    languages.add("English")
            elif isinstance(data, dict):
                for value in data.values():
                    traverse(value)
            elif isinstance(data, list):
                for item in data:
                    traverse(item)
        
        traverse(content)
        return list(languages)
    
    def _calculate_consistency(self, content: Dict[str, Any], languages: List[str]) -> float:
        """计算一致性得分"""
        if len(languages) <= 1:
            return 1.0
        
        # 简单的一致性计算逻辑
        # 实际项目中可以使用更复杂的算法
        return 0.9  # 暂时返回一个默认值
    
    def _identify_issues(self, content: Dict[str, Any], languages: List[str]) -> List[Dict[str, Any]]:
        """识别问题"""
        issues = []
        
        # 检查混合语言使用
        if len(languages) > 1:
            issues.append({
                "type": "mixed_languages",
                "message": "Content contains multiple languages",
                "severity": "warning"
            })
        
        return issues
    
    def generate_report(self, audit_result: Dict[str, Any]) -> str:
        """生成审计报告"""
        report = f"Audit Report\n"
        report += f"Languages detected: {', '.join(audit_result['languages'])}\n"
        report += f"Consistency score: {audit_result['consistency_score']}\n"
        report += f"Status: {audit_result['status']}\n"
        
        if audit_result['issues']:
            report += "\nIssues found:\n"
            for issue in audit_result['issues']:
                report += f"- {issue['type']}: {issue['message']} ({issue['severity']})\n"
        
        return report
