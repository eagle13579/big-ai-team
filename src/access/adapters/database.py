from abc import abstractmethod
from typing import Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base import AdapterContext, BaseAdapter
from .registry import adapter_registry


class DatabaseAdapter(BaseAdapter[dict[str, Any]]):
    """数据库适配器基类"""

    async def execute(
        self, operation: str, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行数据库操作"""
        if operation == "query":
            return await self.query(params, context)
        elif operation == "execute":
            return await self.execute_statement(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    @abstractmethod
    async def query(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行查询"""
        pass

    @abstractmethod
    async def execute_statement(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行语句"""
        pass

    async def _health_check(self, context: Optional[AdapterContext] = None) -> dict[str, Any]:
        """健康检查"""
        try:
            await self.query({"query": "SELECT 1"}, context)
            return {
                "status": "healthy",
                "platform": self.platform,
                "timestamp": context.timestamp.isoformat() if context else None,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "error": str(e),
                "timestamp": context.timestamp.isoformat() if context else None,
            }


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL 适配器"""

    def __init__(self, config):
        super().__init__(config)
        self.connection_string = self.config.config.get("connection_string")
        self.engine = None
        self.SessionLocal = None

    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        if not self.connection_string:
            raise ValueError("Connection string is required")

        try:
            self.engine = create_engine(self.connection_string)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            # 测试连接
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            self._set_initialized(True)
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize PostgreSQL adapter: {str(e)}")

    async def query(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行查询"""
        if not self.engine:
            await self.initialize(context)

        query = params.get("query")
        if not query:
            raise ValueError("Query is required")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(query)
                rows = result.fetchall()
                columns = result.keys()

                return {
                    "rows": [dict(zip(columns, row)) for row in rows],
                    "row_count": len(rows),
                    "columns": list(columns),
                }
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    async def execute_statement(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行语句"""
        if not self.engine:
            await self.initialize(context)

        statement = params.get("statement")
        if not statement:
            raise ValueError("Statement is required")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(statement)
                connection.commit()

                return {"row_count": result.rowcount}
        except Exception as e:
            raise Exception(f"Statement execution failed: {str(e)}")

    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
        self._set_initialized(False)
        return True

    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "connection_string_set": bool(self.connection_string),
        }


class SQLiteAdapter(DatabaseAdapter):
    """SQLite 适配器"""

    def __init__(self, config):
        super().__init__(config)
        self.connection_string = self.config.config.get("connection_string", "sqlite:///./test.db")
        self.engine = None
        self.SessionLocal = None

    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        try:
            self.engine = create_engine(
                self.connection_string, connect_args={"check_same_thread": False}
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            # 测试连接
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            self._set_initialized(True)
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize SQLite adapter: {str(e)}")

    async def query(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行查询"""
        if not self.engine:
            await self.initialize(context)

        query = params.get("query")
        if not query:
            raise ValueError("Query is required")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(query)
                rows = result.fetchall()
                columns = result.keys()

                return {
                    "rows": [dict(zip(columns, row)) for row in rows],
                    "row_count": len(rows),
                    "columns": list(columns),
                }
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    async def execute_statement(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行语句"""
        if not self.engine:
            await self.initialize(context)

        statement = params.get("statement")
        if not statement:
            raise ValueError("Statement is required")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(statement)
                connection.commit()

                return {"row_count": result.rowcount}
        except Exception as e:
            raise Exception(f"Statement execution failed: {str(e)}")

    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
        self._set_initialized(False)
        return True

    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "connection_string": self.connection_string,
        }


# 注册数据库适配器
adapter_registry.register("postgresql", PostgreSQLAdapter)
adapter_registry.register("sqlite", SQLiteAdapter)
