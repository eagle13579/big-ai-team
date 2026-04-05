import pytest
import os
from pathlib import Path
from src.shared.config import Settings, ConfigManager


class TestSettings:
    """测试配置类"""
    
    def test_settings_creation(self):
        """测试配置对象创建"""
        # 临时设置环境变量
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["SECRET_KEY"] = "test_secret_key_123456789012345678901234567890"
        
        settings = Settings()
        assert settings.DATABASE_URL == "sqlite:///./test.db"
        assert settings.REDIS_URL == "redis://localhost:6379/0"
        assert settings.SECRET_KEY == "test_secret_key_123456789012345678901234567890"
        assert settings.CONFIG_VERSION == "2.0.0"
    
    def test_settings_validation(self):
        """测试配置验证"""
        # 测试缺少必要配置
        with pytest.raises(Exception):
            # 清除必要的环境变量
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            Settings()


class TestConfigManager:
    """测试配置管理器"""
    
    def test_config_manager_creation(self):
        """测试配置管理器创建"""
        # 临时设置环境变量
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["SECRET_KEY"] = "test_secret_key_123456789012345678901234567890"
        
        config_manager = ConfigManager()
        assert config_manager.get_config_version() == "2.0.0"
    
    def test_config_export_import(self, tmp_path):
        """测试配置导出和导入"""
        # 临时设置环境变量
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["SECRET_KEY"] = "test_secret_key_123456789012345678901234567890"
        
        config_manager = ConfigManager()
        export_path = tmp_path / "config.json"
        
        # 导出配置
        config_manager.export_config(str(export_path))
        assert export_path.exists()
        
        # 修改环境变量
        os.environ["DATABASE_URL"] = "sqlite:///./new_test.db"
        
        # 导入配置
        config_manager.import_config(str(export_path))
        settings = config_manager.get_settings()
        assert settings.DATABASE_URL == "sqlite:///./test.db"
