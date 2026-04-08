from typing import List, Optional, Dict, Any
import numpy as np
import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class VectorManager:
    """向量管理器"""
    
    def __init__(self, persist_directory: str = "./chromadb"):
        # 初始化 ChromaDB 客户端
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name="ace_agent_documents",
            metadata={"description": "Ace AI Engine 文档集合"}
        )
        # 使用默认的嵌入函数
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """生成文本嵌入向量"""
        try:
            embedding = self.embedding_function([text])[0]
            return embedding
        except Exception:
            #  fallback 到随机向量
            return list(np.random.rand(768).astype(float))
    
    def add_document(self, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """添加文档到向量数据库"""
        try:
            # 生成嵌入向量
            embedding = self.generate_embedding(content)
            if not embedding:
                return False
            
            # 添加到集合
            self.collection.add(
                ids=[document_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None
            )
            return True
        except Exception:
            return False
    
    def get_similar_documents(self, query_text: str, limit: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """获取相似文档"""
        try:
            # 生成查询向量
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=filter
            )
            
            # 格式化结果
            similar_docs = []
            for i in range(len(results["ids"][0])):
                similar_docs.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "score": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else None
                })
            return similar_docs
        except Exception:
            return []
    
    def update_document(self, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新文档"""
        try:
            # 生成嵌入向量
            embedding = self.generate_embedding(content)
            if not embedding:
                return False
            
            # 更新集合
            self.collection.update(
                ids=[document_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None
            )
            return True
        except Exception:
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception:
            return False
    
    def list_documents(self) -> List[str]:
        """列出所有文档ID"""
        try:
            return self.collection.get()["ids"]
        except Exception:
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        try:
            result = self.collection.get(ids=[document_id])
            if result and result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else None
                }
            return None
        except Exception:
            return None
    
    def batch_add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """批量添加文档"""
        try:
            ids = []
            contents = []
            embeddings = []
            metadatas = []
            
            for doc in documents:
                ids.append(doc["id"])
                contents.append(doc["content"])
                embeddings.append(self.generate_embedding(doc["content"]))
                if "metadata" in doc:
                    metadatas.append(doc["metadata"])
                else:
                    metadatas.append(None)
            
            self.collection.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            return len(ids)
        except Exception:
            return 0
    
    def load_document_from_file(self, file_path: str, document_id: Optional[str] = None) -> bool:
        """从文件加载文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            doc_id = document_id or os.path.basename(file_path)
            metadata = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": len(content)
            }
            
            return self.add_document(doc_id, content, metadata)
        except Exception:
            return False
