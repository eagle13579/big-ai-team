import asyncio
import csv
import json
import os
import tempfile
import unittest

from src.skills.data_analyzer import DataAnalyzerSkill


class TestDataAnalyzerSkill(unittest.IsolatedAsyncioTestCase):
    """测试数据分析技能"""
    
    def setUp(self):
        """设置测试环境"""
        self.skill = DataAnalyzerSkill()
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_read_json(self):
        """测试读取 JSON 文件"""
        # 创建测试 JSON 文件
        json_path = os.path.join(self.temp_dir, "test.json")
        test_data = [{"name": "test", "value": 10}]
        with open(json_path, "w") as f:
            json.dump(test_data, f)
        
        result = await self.skill.execute("read", file_path=json_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], test_data)
    
    async def test_read_csv(self):
        """测试读取 CSV 文件"""
        # 创建测试 CSV 文件
        csv_path = os.path.join(self.temp_dir, "test.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "value"])
            writer.writerow(["test1", "10"])
            writer.writerow(["test2", "20"])
        
        result = await self.skill.execute("read", file_path=csv_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["data"][0]["name"], "test1")
        self.assertEqual(result["data"][0]["value"], "10")
    
    async def test_basic_analysis(self):
        """测试基本统计分析"""
        test_data = [
            {"name": "test1", "value": "10"},
            {"name": "test2", "value": "20"},
            {"name": "test3", "value": "30"}
        ]
        
        result = await self.skill.execute("analyze", data=test_data, analysis_type="basic", columns=["value"])
        self.assertEqual(result["status"], "success")
        self.assertIn("analysis", result)
        self.assertIn("value", result["analysis"])
    
    async def test_trend_analysis(self):
        """测试趋势分析"""
        test_data = [
            {"date": "2023-01-01", "value": "10"},
            {"date": "2023-01-02", "value": "20"},
            {"date": "2023-01-03", "value": "30"}
        ]
        
        result = await self.skill.execute("analyze", data=test_data, analysis_type="trend", x_column="date", y_column="value")
        self.assertEqual(result["status"], "success")
        self.assertIn("trend", result)
    
    async def test_visualize_data(self):
        """测试数据可视化"""
        test_data = [
            {"name": "test1", "value": "10"},
            {"name": "test2", "value": "20"}
        ]
        
        result = await self.skill.execute("visualize", data=test_data, chart_type="bar", x_column="name", y_column="value", title="Test Chart")
        self.assertEqual(result["status"], "success")
        self.assertIn("visualization", result)
        self.assertEqual(result["visualization"]["chart_type"], "bar")
        self.assertEqual(result["visualization"]["title"], "Test Chart")
    
    async def test_export_json(self):
        """测试导出为 JSON 文件"""
        test_data = [{"name": "test", "value": 10}]
        output_path = os.path.join(self.temp_dir, "output.json")
        
        result = await self.skill.execute("export", data=test_data, export_format="json", output_path=output_path)
        self.assertEqual(result["status"], "success")
        
        # 验证文件已创建并包含正确内容
        self.assertTrue(os.path.exists(output_path))
        with open(output_path) as f:
            exported_data = json.load(f)
        self.assertEqual(exported_data, test_data)
    
    async def test_export_csv(self):
        """测试导出为 CSV 文件"""
        test_data = [{"name": "test1", "value": 10}, {"name": "test2", "value": 20}]
        output_path = os.path.join(self.temp_dir, "output.csv")
        
        result = await self.skill.execute("export", data=test_data, export_format="csv", output_path=output_path)
        self.assertEqual(result["status"], "success")
        
        # 验证文件已创建
        self.assertTrue(os.path.exists(output_path))
    
    async def test_invalid_file_format(self):
        """测试无效文件格式"""
        # 创建测试文件
        invalid_path = os.path.join(self.temp_dir, "test.txt")
        with open(invalid_path, "w") as f:
            f.write("test content")
        
        result = await self.skill.execute("read", file_path=invalid_path)
        self.assertEqual(result["status"], "error")
        self.assertIn("不支持的文件格式", result["error"])
    
    async def test_invalid_analysis_type(self):
        """测试无效分析类型"""
        test_data = [{"name": "test", "value": 10}]
        
        result = await self.skill.execute("analyze", data=test_data, analysis_type="invalid")
        self.assertEqual(result["status"], "error")
        self.assertIn("不支持的分析类型", result["error"])
    
    async def test_invalid_export_format(self):
        """测试无效导出格式"""
        test_data = [{"name": "test", "value": 10}]
        
        result = await self.skill.execute("export", data=test_data, export_format="invalid")
        self.assertEqual(result["status"], "error")
        self.assertIn("不支持的导出格式", result["error"])
    
    def test_get_info(self):
        """测试获取技能信息"""
        info = self.skill.get_info()
        self.assertEqual(info["name"], "data_analyzer")
        self.assertEqual(info["description"], "分析数据文件并生成统计信息和可视化")
        self.assertIn("action", info["parameters"])
        self.assertIn("file_path", info["parameters"])
        self.assertIn("data", info["parameters"])
    
    def test_sync(self):
        """同步测试入口"""
        asyncio.run(self.test_read_json())
        asyncio.run(self.test_read_csv())
        asyncio.run(self.test_basic_analysis())
        asyncio.run(self.test_trend_analysis())
        asyncio.run(self.test_visualize_data())
        asyncio.run(self.test_export_json())
        asyncio.run(self.test_export_csv())
        asyncio.run(self.test_invalid_file_format())
        asyncio.run(self.test_invalid_analysis_type())
        asyncio.run(self.test_invalid_export_format())
        self.test_get_info()


if __name__ == "__main__":
    unittest.main()