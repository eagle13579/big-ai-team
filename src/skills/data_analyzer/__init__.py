import asyncio
import csv
import json
import os
from typing import Any, Dict, List, Optional

from src.shared.logging import logger
from src.skills.registry import register_skill


class DataAnalyzerSkill:
    """数据分析技能，用于分析各种格式的数据"""
    
    def __init__(self):
        self.skill_name = "data_analyzer"
        self.description = "分析数据文件并生成统计信息和可视化"
        self.logger = logger.bind(skill=self.skill_name)
    
    async def execute(self, action: str, **kwargs):
        """
        执行数据分析操作
        
        Args:
            action: 操作类型 (read, analyze, visualize, export)
            **kwargs: 额外参数
                - file_path: 文件路径
                - data: 数据内容
                - analysis_type: 分析类型
                - export_format: 导出格式
            
        Returns:
            dict: 执行结果
        """
        try:
            self.logger.info(f"执行数据分析操作: {action}")
            
            if action == "read":
                return await self._read_data(**kwargs)
            elif action == "analyze":
                return await self._analyze_data(**kwargs)
            elif action == "visualize":
                return await self._visualize_data(**kwargs)
            elif action == "export":
                return await self._export_data(**kwargs)
            else:
                return {
                    "status": "error",
                    "error": f"不支持的操作类型: {action}"
                }
            
        except Exception as e:
            self.logger.error(f"执行数据分析时发生错误: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _read_data(self, file_path: str, **kwargs) -> dict:
        """
        读取数据文件
        
        Args:
            file_path: 文件路径
            **kwargs: 额外参数
                - encoding: 编码方式
                - delimiter: 分隔符（CSV）
            
        Returns:
            dict: 读取结果
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == ".csv":
                return self._read_csv(file_path, **kwargs)
            elif file_ext == ".json":
                return self._read_json(file_path, **kwargs)
            elif file_ext in [".xlsx", ".xls"]:
                return self._read_excel(file_path, **kwargs)
            else:
                return {
                    "status": "error",
                    "error": f"不支持的文件格式: {file_ext}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"读取文件失败: {str(e)}"
            }
    
    def _read_csv(self, file_path: str, **kwargs) -> dict:
        """
        读取 CSV 文件
        
        Args:
            file_path: 文件路径
            **kwargs: 额外参数
                - encoding: 编码方式
                - delimiter: 分隔符
            
        Returns:
            dict: 读取结果
        """
        encoding = kwargs.get("encoding", "utf-8")
        delimiter = kwargs.get("delimiter", ",")
        
        data = []
        with open(file_path, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                data.append(row)
        
        return {
            "status": "success",
            "data": data,
            "message": f"成功读取 CSV 文件: {file_path}",
            "row_count": len(data)
        }
    
    def _read_json(self, file_path: str, **kwargs) -> dict:
        """
        读取 JSON 文件
        
        Args:
            file_path: 文件路径
            **kwargs: 额外参数
                - encoding: 编码方式
            
        Returns:
            dict: 读取结果
        """
        encoding = kwargs.get("encoding", "utf-8")
        
        with open(file_path, encoding=encoding) as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "data": data,
            "message": f"成功读取 JSON 文件: {file_path}"
        }
    
    def _read_excel(self, file_path: str, **kwargs) -> dict:
        """
        读取 Excel 文件
        
        Args:
            file_path: 文件路径
            **kwargs: 额外参数
                - sheet_name: 工作表名称
            
        Returns:
            dict: 读取结果
        """
        try:
            import pandas as pd
            
            sheet_name = kwargs.get("sheet_name", 0)
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            data = df.to_dict(orient="records")
            
            return {
                "status": "success",
                "data": data,
                "message": f"成功读取 Excel 文件: {file_path}",
                "row_count": len(data)
            }
        except ImportError:
            return {
                "status": "error",
                "error": "需要 pandas 库来读取 Excel 文件"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"读取 Excel 文件失败: {str(e)}"
            }
    
    async def _analyze_data(self, data: list[dict[str, Any]], analysis_type: str, **kwargs) -> dict:
        """
        分析数据
        
        Args:
            data: 要分析的数据
            analysis_type: 分析类型 (basic, correlation, trend)
            **kwargs: 额外参数
                - columns: 要分析的列
            
        Returns:
            dict: 分析结果
        """
        try:
            if analysis_type == "basic":
                return self._basic_analysis(data, **kwargs)
            elif analysis_type == "correlation":
                return self._correlation_analysis(data, **kwargs)
            elif analysis_type == "trend":
                return self._trend_analysis(data, **kwargs)
            else:
                return {
                    "status": "error",
                    "error": f"不支持的分析类型: {analysis_type}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"分析数据失败: {str(e)}"
            }
    
    def _basic_analysis(self, data: list[dict[str, Any]], **kwargs) -> dict:
        """
        基本统计分析
        
        Args:
            data: 要分析的数据
            **kwargs: 额外参数
                - columns: 要分析的列
            
        Returns:
            dict: 分析结果
        """
        columns = kwargs.get("columns", [])
        analysis = {}
        
        # 分析每一列
        for column in columns:
            values = []
            for row in data:
                if column in row:
                    try:
                        values.append(float(row[column]))
                    except (ValueError, TypeError):
                        pass
            
            if values:
                analysis[column] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "sum": sum(values)
                }
        
        return {
            "status": "success",
            "analysis": analysis,
            "message": "基本统计分析完成"
        }
    
    def _correlation_analysis(self, data: list[dict[str, Any]], **kwargs) -> dict:
        """
        相关性分析
        
        Args:
            data: 要分析的数据
            **kwargs: 额外参数
                - columns: 要分析的列
            
        Returns:
            dict: 分析结果
        """
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            columns = kwargs.get("columns", df.select_dtypes(include=["number"]).columns.tolist())
            
            correlation = df[columns].corr().to_dict()
            
            return {
                "status": "success",
                "correlation": correlation,
                "message": "相关性分析完成"
            }
        except ImportError:
            return {
                "status": "error",
                "error": "需要 pandas 库来进行相关性分析"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"相关性分析失败: {str(e)}"
            }
    
    def _trend_analysis(self, data: list[dict[str, Any]], **kwargs) -> dict:
        """
        趋势分析
        
        Args:
            data: 要分析的数据
            **kwargs: 额外参数
                - x_column: X轴列
                - y_column: Y轴列
            
        Returns:
            dict: 分析结果
        """
        try:
            x_column = kwargs.get("x_column")
            y_column = kwargs.get("y_column")
            
            if not x_column or not y_column:
                return {
                    "status": "error",
                    "error": "需要指定 x_column 和 y_column"
                }
            
            # 提取数据
            x_values = []
            y_values = []
            
            for row in data:
                if x_column in row and y_column in row:
                    try:
                        x_values.append(row[x_column])
                        y_values.append(float(row[y_column]))
                    except (ValueError, TypeError):
                        pass
            
            # 简单的趋势分析
            if len(y_values) >= 2:
                # 计算变化率
                changes = []
                for i in range(1, len(y_values)):
                    if y_values[i-1] != 0:
                        change = (y_values[i] - y_values[i-1]) / abs(y_values[i-1]) * 100
                        changes.append(change)
                
                trend = "stable"
                if changes:
                    avg_change = sum(changes) / len(changes)
                    if avg_change > 5:
                        trend = "increasing"
                    elif avg_change < -5:
                        trend = "decreasing"
                
                return {
                    "status": "success",
                    "trend": trend,
                    "data_points": len(y_values),
                    "message": "趋势分析完成"
                }
            else:
                return {
                    "status": "error",
                    "error": "数据点不足，无法进行趋势分析"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"趋势分析失败: {str(e)}"
            }
    
    async def _visualize_data(self, data: list[dict[str, Any]], **kwargs) -> dict:
        """
        数据可视化
        
        Args:
            data: 要可视化的数据
            **kwargs: 额外参数
                - chart_type: 图表类型 (bar, line, pie)
                - x_column: X轴列
                - y_column: Y轴列
                - title: 图表标题
            
        Returns:
            dict: 可视化结果
        """
        try:
            chart_type = kwargs.get("chart_type", "bar")
            x_column = kwargs.get("x_column")
            y_column = kwargs.get("y_column")
            title = kwargs.get("title", "数据可视化")
            
            if not x_column or not y_column:
                return {
                    "status": "error",
                    "error": "需要指定 x_column 和 y_column"
                }
            
            # 提取数据
            x_values = []
            y_values = []
            
            for row in data:
                if x_column in row and y_column in row:
                    try:
                        x_values.append(row[x_column])
                        y_values.append(float(row[y_column]))
                    except (ValueError, TypeError):
                        pass
            
            # 生成图表配置
            visualization = {
                "chart_type": chart_type,
                "title": title,
                "x_axis": x_column,
                "y_axis": y_column,
                "data": {
                    "x": x_values,
                    "y": y_values
                }
            }
            
            return {
                "status": "success",
                "visualization": visualization,
                "message": "数据可视化完成"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"数据可视化失败: {str(e)}"
            }
    
    async def _export_data(self, data: list[dict[str, Any]], export_format: str, **kwargs) -> dict:
        """
        导出数据
        
        Args:
            data: 要导出的数据
            export_format: 导出格式 (csv, json, excel)
            **kwargs: 额外参数
                - output_path: 输出路径
            
        Returns:
            dict: 导出结果
        """
        try:
            output_path = kwargs.get("output_path", f"output.{export_format}")
            
            if export_format == "csv":
                return self._export_csv(data, output_path)
            elif export_format == "json":
                return self._export_json(data, output_path)
            elif export_format == "excel":
                return self._export_excel(data, output_path)
            else:
                return {
                    "status": "error",
                    "error": f"不支持的导出格式: {export_format}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"导出数据失败: {str(e)}"
            }
    
    def _export_csv(self, data: list[dict[str, Any]], output_path: str) -> dict:
        """
        导出为 CSV 文件
        
        Args:
            data: 要导出的数据
            output_path: 输出路径
            
        Returns:
            dict: 导出结果
        """
        if not data:
            return {
                "status": "error",
                "error": "没有数据可导出"
            }
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return {
            "status": "success",
            "output_path": output_path,
            "message": f"成功导出为 CSV 文件: {output_path}"
        }
    
    def _export_json(self, data: list[dict[str, Any]], output_path: str) -> dict:
        """
        导出为 JSON 文件
        
        Args:
            data: 要导出的数据
            output_path: 输出路径
            
        Returns:
            dict: 导出结果
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "output_path": output_path,
            "message": f"成功导出为 JSON 文件: {output_path}"
        }
    
    def _export_excel(self, data: list[dict[str, Any]], output_path: str) -> dict:
        """
        导出为 Excel 文件
        
        Args:
            data: 要导出的数据
            output_path: 输出路径
            
        Returns:
            dict: 导出结果
        """
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False)
            
            return {
                "status": "success",
                "output_path": output_path,
                "message": f"成功导出为 Excel 文件: {output_path}"
            }
        except ImportError:
            return {
                "status": "error",
                "error": "需要 pandas 库来导出 Excel 文件"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"导出 Excel 文件失败: {str(e)}"
            }
    
    def get_info(self):
        """
        获取技能信息
        
        Returns:
            dict: 技能信息
        """
        return {
            "name": self.skill_name,
            "description": self.description,
            "parameters": {
                "action": "string, 操作类型 (read, analyze, visualize, export)",
                "file_path": "string, 文件路径（read操作）",
                "data": "array, 要分析的数据（analyze/visualize/export操作）",
                "analysis_type": "string, 分析类型（analyze操作）",
                "export_format": "string, 导出格式（export操作）"
            }
        }


# 注册技能
register_skill("data_analyzer", DataAnalyzerSkill())