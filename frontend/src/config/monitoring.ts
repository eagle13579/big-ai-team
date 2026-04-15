// 监控配置文件

// 系统指标配置
export const systemMetrics = {
  // API响应时间
  apiResponseTime: {
    name: 'API Response Time',
    description: '平均API响应时间（毫秒）',
    threshold: {
      warning: 200,
      critical: 500
    }
  },
  // 错误率
  errorRate: {
    name: 'Error Rate',
    description: 'API错误率（%）',
    threshold: {
      warning: 5,
      critical: 10
    }
  },
  // 活跃用户数
  activeUsers: {
    name: 'Active Users',
    description: '当前活跃用户数',
    threshold: {
      warning: 100,
      critical: 500
    }
  },
  // 请求数
  requestCount: {
    name: 'Request Count',
    description: '总请求数',
    threshold: {
      warning: 10000,
      critical: 50000
    }
  },
  // CPU使用率
  cpuUsage: {
    name: 'CPU Usage',
    description: 'CPU使用率（%）',
    threshold: {
      warning: 70,
      critical: 90
    }
  },
  // 内存使用率
  memoryUsage: {
    name: 'Memory Usage',
    description: '内存使用率（%）',
    threshold: {
      warning: 70,
      critical: 90
    }
  },
  // 磁盘使用率
  diskUsage: {
    name: 'Disk Usage',
    description: '磁盘使用率（%）',
    threshold: {
      warning: 70,
      critical: 90
    }
  }
};

// 仪表板配置
export const dashboardConfig = {
  // 仪表板布局
  layout: {
    rows: [
      {
        id: 'row-1',
        height: '250px',
        panels: [
          {
            id: 'panel-system-status',
            title: 'System Status',
            type: 'status',
            metrics: ['system.status', 'system.version', 'system.server_time']
          },
          {
            id: 'panel-task-stats',
            title: 'Task Statistics',
            type: 'pie',
            metrics: ['tasks.completed', 'tasks.pending', 'tasks.failed']
          },
          {
            id: 'panel-system-metrics',
            title: 'System Metrics',
            type: 'cards',
            metrics: ['api.response_time', 'api.error_rate', 'users.active', 'requests.count', 'system.cpu_usage', 'system.memory_usage', 'system.disk_usage']
          }
        ]
      },
      {
        id: 'row-2',
        height: '300px',
        panels: [
          {
            id: 'panel-executor-status',
            title: 'Executor Status',
            type: 'table',
            metrics: ['executor.status', 'executor.tool_count', 'executor.cache_hit_rate', 'executor.cache_hits', 'executor.cache_misses']
          },
          {
            id: 'panel-workflow-status',
            title: 'Workflow Status',
            type: 'table',
            metrics: ['workflow.history_count', 'workflow.memory_usage', 'workflow.short_term_memory', 'workflow.long_term_memory']
          }
        ]
      },
      {
        id: 'row-3',
        height: '300px',
        panels: [
          {
            id: 'panel-user-activity',
            title: 'User Activity',
            type: 'line',
            metrics: ['users.activity']
          },
          {
            id: 'panel-api-performance',
            title: 'API Performance',
            type: 'bar',
            metrics: ['api.performance']
          }
        ]
      }
    ]
  },
  // 刷新间隔（秒）
  refreshInterval: 30,
  // 主题
  theme: 'light'
};

// 告警配置
export const alertConfig = {
  // 告警级别
  levels: {
    info: {
      color: '#2196F3',
      icon: 'info'
    },
    warning: {
      color: '#FF9800',
      icon: 'warning'
    },
    error: {
      color: '#F44336',
      icon: 'error'
    }
  },
  // 告警规则
  rules: [
    {
      id: 'rule-api-response-time',
      metric: 'api.response_time',
      operator: '>',
      threshold: systemMetrics.apiResponseTime.threshold.warning,
      level: 'warning',
      message: 'API响应时间超过阈值'
    },
    {
      id: 'rule-api-error-rate',
      metric: 'api.error_rate',
      operator: '>',
      threshold: systemMetrics.errorRate.threshold.warning,
      level: 'warning',
      message: 'API错误率超过阈值'
    },
    {
      id: 'rule-cpu-usage',
      metric: 'system.cpu_usage',
      operator: '>',
      threshold: systemMetrics.cpuUsage.threshold.warning,
      level: 'warning',
      message: 'CPU使用率超过阈值'
    },
    {
      id: 'rule-memory-usage',
      metric: 'system.memory_usage',
      operator: '>',
      threshold: systemMetrics.memoryUsage.threshold.warning,
      level: 'warning',
      message: '内存使用率超过阈值'
    }
  ]
};