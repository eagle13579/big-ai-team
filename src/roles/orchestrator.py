from typing import Dict, Any, List, Optional
from .role_factory import RoleFactory
from src.shared.logging import logger


class PlanningOrchestrator:
    """规划编排器"""
    
    def __init__(self):
        self.role_factory = RoleFactory()
    
    def orchestrate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """编排任务执行"""
        try:
            # 1. 分析任务
            analysis_result = self._analyze_task(task)
            if analysis_result["status"] != "success":
                return analysis_result
            
            # 2. 分解任务
            subtasks = self._decompose_task(task, analysis_result["data"])
            
            # 3. 分配任务
            assigned_tasks = self._assign_tasks(subtasks)
            
            # 4. 执行任务
            execution_results = self._execute_tasks(assigned_tasks)
            
            # 5. 审查任务
            review_results = self._review_tasks(execution_results)
            
            # 6. 整合结果
            final_result = self._integrate_results(review_results)
            
            return {
                "status": "success",
                "data": {
                    "analysis": analysis_result["data"],
                    "subtasks": subtasks,
                    "assigned_tasks": assigned_tasks,
                    "execution_results": execution_results,
                    "review_results": review_results,
                    "final_result": final_result
                }
            }
        except Exception as e:
            logger.error(f"编排任务失败: {str(e)}")
            return {
                "status": "error",
                "message": f"编排任务失败: {str(e)}"
            }
    
    def _analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分析任务"""
        analyst = self.role_factory.create_role("analyst")
        if not analyst:
            return {
                "status": "error",
                "message": "无法创建分析专家角色"
            }
        return analyst.process_task(task)
    
    def _decompose_task(self, task: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分解任务"""
        subtasks = []
        task_description = task.get("description", "")
        
        # 根据任务类型分解
        task_type = analysis.get("task_type", "general")
        
        if task_type == "coding":
            subtasks = [
                {
                    "id": "1",
                    "description": "分析代码需求",
                    "type": "analysis",
                    "priority": "high"
                },
                {
                    "id": "2",
                    "description": "编写代码",
                    "type": "coding",
                    "priority": "high"
                },
                {
                    "id": "3",
                    "description": "测试代码",
                    "type": "testing",
                    "priority": "medium"
                },
                {
                    "id": "4",
                    "description": "提交代码",
                    "type": "git",
                    "priority": "medium"
                }
            ]
        elif task_type == "analysis":
            subtasks = [
                {
                    "id": "1",
                    "description": "收集信息",
                    "type": "research",
                    "priority": "high"
                },
                {
                    "id": "2",
                    "description": "分析数据",
                    "type": "analysis",
                    "priority": "high"
                },
                {
                    "id": "3",
                    "description": "生成报告",
                    "type": "documentation",
                    "priority": "medium"
                }
            ]
        elif task_type == "documentation":
            subtasks = [
                {
                    "id": "1",
                    "description": "收集文档需求",
                    "type": "analysis",
                    "priority": "high"
                },
                {
                    "id": "2",
                    "description": "编写文档",
                    "type": "documentation",
                    "priority": "high"
                },
                {
                    "id": "3",
                    "description": "审查文档",
                    "type": "review",
                    "priority": "medium"
                }
            ]
        else:
            # 通用任务
            subtasks = [
                {
                    "id": "1",
                    "description": "执行任务",
                    "type": "general",
                    "priority": "high"
                },
                {
                    "id": "2",
                    "description": "验证结果",
                    "type": "review",
                    "priority": "medium"
                }
            ]
        
        return subtasks
    
    def _assign_tasks(self, subtasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分配任务"""
        assigned_tasks = []
        
        for subtask in subtasks:
            # 根据任务类型分配角色
            task_type = subtask.get("type", "general")
            
            if task_type in ["analysis", "research"]:
                role_type = "analyst"
            elif task_type in ["coding", "testing", "git"]:
                role_type = "executor"
            elif task_type in ["review"]:
                role_type = "reviewer"
            else:
                role_type = "executor"
            
            assigned_task = {
                **subtask,
                "assigned_role": role_type
            }
            assigned_tasks.append(assigned_task)
        
        return assigned_tasks
    
    def _execute_tasks(self, assigned_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行任务"""
        execution_results = []
        
        for task in assigned_tasks:
            role_type = task.get("assigned_role", "executor")
            role = self.role_factory.create_role(role_type)
            
            if not role:
                execution_results.append({
                    "task": task,
                    "result": {
                        "status": "error",
                        "message": f"无法创建角色: {role_type}"
                    }
                })
                continue
            
            result = role.process_task(task)
            execution_results.append({
                "task": task,
                "result": result
            })
        
        return execution_results
    
    def _review_tasks(self, execution_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """审查任务"""
        review_results = []
        reviewer = self.role_factory.create_role("reviewer")
        
        if not reviewer:
            return execution_results
        
        for execution in execution_results:
            if execution["result"]["status"] == "success":
                review_result = reviewer.process_task({
                    "description": execution["task"]["description"],
                    "execution_result": execution["result"]["data"]
                })
                review_results.append({
                    "task": execution["task"],
                    "execution_result": execution["result"],
                    "review_result": review_result
                })
            else:
                review_results.append({
                    "task": execution["task"],
                    "execution_result": execution["result"],
                    "review_result": {
                        "status": "error",
                        "message": "执行失败，无需审查"
                    }
                })
        
        return review_results
    
    def _integrate_results(self, review_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """整合结果"""
        success_count = 0
        error_count = 0
        
        for result in review_results:
            if result["execution_result"]["status"] == "success":
                success_count += 1
            else:
                error_count += 1
        
        overall_status = "success" if error_count == 0 else "partial_success"
        
        return {
            "overall_status": overall_status,
            "success_count": success_count,
            "error_count": error_count,
            "total_tasks": len(review_results),
            "message": f"任务执行完成，成功 {success_count} 个，失败 {error_count} 个"
        }
