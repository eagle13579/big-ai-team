
from locust import HttpUser, between, task


class AgentReachUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_read_webpage(self):
        """测试读取网页功能"""
        payload = {
            "action": "read_webpage",
            "params": {"url": "https://example.com"}
        }
        self.client.post("/api/v1/agent-reach/execute", json=payload)
    
    @task
    def test_search_twitter(self):
        """测试搜索 Twitter 功能"""
        payload = {
            "action": "search_twitter",
            "params": {"query": "AI Agent", "limit": 5}
        }
        self.client.post("/api/v1/agent-reach/execute", json=payload)
    
    @task
    def test_get_youtube_transcript(self):
        """测试获取 YouTube 字幕功能"""
        payload = {
            "action": "get_youtube_transcript",
            "params": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        }
        self.client.post("/api/v1/agent-reach/execute", json=payload)
    
    @task
    def test_search_github_repos(self):
        """测试搜索 GitHub 仓库功能"""
        payload = {
            "action": "search_github_repos",
            "params": {"query": "AI Agent", "language": "python"}
        }
        self.client.post("/api/v1/agent-reach/execute", json=payload)
