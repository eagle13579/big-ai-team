from typing import Dict, Any, Optional
from abc import abstractmethod
import pika
from kafka import KafkaProducer, KafkaConsumer
from .base import BaseAdapter, AdapterContext
from .registry import adapter_registry


class MessagingAdapter(BaseAdapter[Dict[str, Any]]):
    """消息队列适配器基类"""
    
    async def execute(self, operation: str, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """执行消息队列操作"""
        if operation == "send":
            return await self.send(params, context)
        elif operation == "receive":
            return await self.receive(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    @abstractmethod
    async def send(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """发送消息"""
        pass
    
    @abstractmethod
    async def receive(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """接收消息"""
        pass
    
    async def _health_check(self, context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 尝试发送一个测试消息
            test_message = "health check"
            result = await self.send({"queue": "health_check", "message": test_message}, context)
            if result.get("success"):
                return {
                    "status": "healthy",
                    "platform": self.platform,
                    "timestamp": context.timestamp.isoformat() if context else None
                }
            else:
                return {
                    "status": "unhealthy",
                    "platform": self.platform,
                    "error": "Health check failed",
                    "timestamp": context.timestamp.isoformat() if context else None
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "error": str(e),
                "timestamp": context.timestamp.isoformat() if context else None
            }


class RabbitMQAdapter(MessagingAdapter):
    """RabbitMQ 消息队列适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.host = self.config.config.get("host", "localhost")
        self.port = self.config.config.get("port", 5672)
        self.username = self.config.config.get("username", "guest")
        self.password = self.config.config.get("password", "guest")
        self.connection = None
        self.channel = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        try:
            # 创建连接
            credentials = pika.PlainCredentials(self.username, self.password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials
                )
            )
            # 创建通道
            self.channel = self.connection.channel()
            self._set_initialized(True)
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize RabbitMQ adapter: {str(e)}")
    
    async def send(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """发送消息"""
        if not self.channel:
            await self.initialize(context)
        
        queue = params.get("queue")
        message = params.get("message")
        
        if not queue or not message:
            raise ValueError("Queue and message are required")
        
        try:
            # 声明队列
            self.channel.queue_declare(queue=queue, durable=True)
            # 发送消息
            self.channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 持久化消息
                )
            )
            return {
                "success": True
            }
        except Exception as e:
            raise Exception(f"Send operation failed: {str(e)}")
    
    async def receive(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """接收消息"""
        if not self.channel:
            await self.initialize(context)
        
        queue = params.get("queue")
        if not queue:
            raise ValueError("Queue is required")
        
        try:
            # 声明队列
            self.channel.queue_declare(queue=queue, durable=True)
            
            # 接收消息
            method_frame, header_frame, body = self.channel.basic_get(queue=queue, auto_ack=True)
            if method_frame:
                return {
                    "message": body.decode(),
                    "delivery_tag": method_frame.delivery_tag
                }
            else:
                return {
                    "message": None
                }
        except Exception as e:
            raise Exception(f"Receive operation failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()
        self.channel = None
        self.connection = None
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "host": self.host,
            "port": self.port
        }


class KafkaAdapter(MessagingAdapter):
    """Kafka 消息队列适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.bootstrap_servers = self.config.config.get("bootstrap_servers", "localhost:9092")
        self.producer = None
        self.consumer = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        try:
            # 创建生产者
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: x.encode('utf-8')
            )
            self._set_initialized(True)
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize Kafka adapter: {str(e)}")
    
    async def send(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """发送消息"""
        if not self.producer:
            await self.initialize(context)
        
        topic = params.get("queue")  # Kafka 使用 topic 而不是 queue
        message = params.get("message")
        
        if not topic or not message:
            raise ValueError("Topic and message are required")
        
        try:
            # 发送消息
            future = self.producer.send(topic, message)
            # 等待发送完成
            future.get(timeout=10)
            return {
                "success": True
            }
        except Exception as e:
            raise Exception(f"Send operation failed: {str(e)}")
    
    async def receive(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """接收消息"""
        topic = params.get("queue")  # Kafka 使用 topic 而不是 queue
        if not topic:
            raise ValueError("Topic is required")
        
        try:
            # 创建消费者
            if not self.consumer:
                self.consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    auto_offset_reset='earliest',
                    group_id='big-ai-team-group'
                )
            
            # 接收消息
            for message in self.consumer:
                return {
                    "message": message.value.decode(),
                    "offset": message.offset
                }
        except Exception as e:
            raise Exception(f"Receive operation failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()
        self.producer = None
        self.consumer = None
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "bootstrap_servers": self.bootstrap_servers
        }


# 注册消息队列适配器
adapter_registry.register("rabbitmq", RabbitMQAdapter)
adapter_registry.register("kafka", KafkaAdapter)
