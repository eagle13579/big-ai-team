import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

// 翻译资源
const resources = {
  en: {
    translation: {
      // 通用
      common: {
        dashboard: 'Dashboard',
        tasks: 'Tasks',
        tools: 'Tools',
        configuration: 'Configuration',
        auditLogs: 'Audit Logs',
        login: 'Login',
        logout: 'Logout',
        save: 'Save',
        cancel: 'Cancel',
        delete: 'Delete',
        edit: 'Edit',
        create: 'Create',
        back: 'Back',
        next: 'Next',
        submit: 'Submit',
        loading: 'Loading...',
        success: 'Success',
        error: 'Error',
        warning: 'Warning',
        info: 'Information'
      },
      // 登录
      login: {
        title: 'Login to Ace Agent',
        username: 'Username',
        password: 'Password',
        remember: 'Remember me',
        forgotPassword: 'Forgot password?',
        submit: 'Sign in',
        error: 'Invalid username or password'
      },
      // 仪表盘
      dashboard: {
        title: 'System Dashboard',
        systemStatus: 'System Status',
        activeTasks: 'Active Tasks',
        completedTasks: 'Completed Tasks',
        failedTasks: 'Failed Tasks',
        systemHealth: 'System Health',
        memoryUsage: 'Memory Usage',
        cpuUsage: 'CPU Usage',
        diskUsage: 'Disk Usage',
        networkTraffic: 'Network Traffic',
        recentActivities: 'Recent Activities',
        upcomingTasks: 'Upcoming Tasks'
      },
      // 任务管理
      tasks: {
        title: 'Task Management',
        createTask: 'Create Task',
        taskList: 'Task List',
        taskDetails: 'Task Details',
        taskId: 'Task ID',
        description: 'Description',
        assignee: 'Assignee',
        status: 'Status',
        priority: 'Priority',
        createdAt: 'Created At',
        updatedAt: 'Updated At',
        inputParams: 'Input Parameters',
        outputData: 'Output Data',
        dependencies: 'Dependencies',
        retryCount: 'Retry Count',
        maxRetries: 'Max Retries',
        statusOptions: {
          pending: 'Pending',
          inProgress: 'In Progress',
          completed: 'Completed',
          failed: 'Failed',
          retrying: 'Retrying'
        },
        priorityOptions: {
          low: 'Low',
          medium: 'Medium',
          high: 'High',
          critical: 'Critical'
        }
      },
      // 工具列表
      tools: {
        title: 'Available Tools',
        toolName: 'Tool Name',
        description: 'Description',
        status: 'Status',
        lastCalled: 'Last Called',
        execute: 'Execute',
        parameters: 'Parameters',
        executeTool: 'Execute Tool',
        executionResult: 'Execution Result'
      },
      // 配置
      configuration: {
        title: 'System Configuration',
        general: 'General',
        security: 'Security',
        performance: 'Performance',
        database: 'Database',
        llm: 'LLM',
        saveChanges: 'Save Changes',
        changesSaved: 'Changes saved successfully',
        apiKey: 'API Key',
        model: 'Model',
        temperature: 'Temperature',
        maxTokens: 'Max Tokens',
        timeout: 'Timeout',
        concurrentTasks: 'Concurrent Tasks',
        cacheTTL: 'Cache TTL (seconds)'
      },
      // 审计日志
      auditLogs: {
        title: 'Audit Logs',
        eventType: 'Event Type',
        user: 'User',
        action: 'Action',
        resource: 'Resource',
        status: 'Status',
        timestamp: 'Timestamp',
        details: 'Details',
        filter: 'Filter',
        clearFilter: 'Clear Filter',
        export: 'Export'
      }
    }
  },
  zh: {
    translation: {
      // 通用
      common: {
        dashboard: '仪表盘',
        tasks: '任务',
        tools: '工具',
        configuration: '配置',
        auditLogs: '审计日志',
        login: '登录',
        logout: '退出',
        save: '保存',
        cancel: '取消',
        delete: '删除',
        edit: '编辑',
        create: '创建',
        back: '返回',
        next: '下一步',
        submit: '提交',
        loading: '加载中...',
        success: '成功',
        error: '错误',
        warning: '警告',
        info: '信息'
      },
      // 登录
      login: {
        title: '登录 Ace Agent',
        username: '用户名',
        password: '密码',
        remember: '记住我',
        forgotPassword: '忘记密码？',
        submit: '登录',
        error: '用户名或密码错误'
      },
      // 仪表盘
      dashboard: {
        title: '系统仪表盘',
        systemStatus: '系统状态',
        activeTasks: '活跃任务',
        completedTasks: '已完成任务',
        failedTasks: '失败任务',
        systemHealth: '系统健康',
        memoryUsage: '内存使用',
        cpuUsage: 'CPU 使用',
        diskUsage: '磁盘使用',
        networkTraffic: '网络流量',
        recentActivities: '最近活动',
        upcomingTasks: '即将到来的任务'
      },
      // 任务管理
      tasks: {
        title: '任务管理',
        createTask: '创建任务',
        taskList: '任务列表',
        taskDetails: '任务详情',
        taskId: '任务 ID',
        description: '描述',
        assignee: '负责人',
        status: '状态',
        priority: '优先级',
        createdAt: '创建时间',
        updatedAt: '更新时间',
        inputParams: '输入参数',
        outputData: '输出数据',
        dependencies: '依赖项',
        retryCount: '重试次数',
        maxRetries: '最大重试次数',
        statusOptions: {
          pending: '待处理',
          inProgress: '进行中',
          completed: '已完成',
          failed: '失败',
          retrying: '重试中'
        },
        priorityOptions: {
          low: '低',
          medium: '中',
          high: '高',
          critical: '关键'
        }
      },
      // 工具列表
      tools: {
        title: '可用工具',
        toolName: '工具名称',
        description: '描述',
        status: '状态',
        lastCalled: '最后调用',
        execute: '执行',
        parameters: '参数',
        executeTool: '执行工具',
        executionResult: '执行结果'
      },
      // 配置
      configuration: {
        title: '系统配置',
        general: '通用',
        security: '安全',
        performance: '性能',
        database: '数据库',
        llm: 'LLM',
        saveChanges: '保存更改',
        changesSaved: '更改保存成功',
        apiKey: 'API 密钥',
        model: '模型',
        temperature: '温度',
        maxTokens: '最大 tokens',
        timeout: '超时',
        concurrentTasks: '并发任务',
        cacheTTL: '缓存 TTL (秒)'
      },
      // 审计日志
      auditLogs: {
        title: '审计日志',
        eventType: '事件类型',
        user: '用户',
        action: '操作',
        resource: '资源',
        status: '状态',
        timestamp: '时间戳',
        details: '详情',
        filter: '过滤',
        clearFilter: '清除过滤',
        export: '导出'
      }
    }
  }
};

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'cookie', 'navigator', 'htmlTag'],
      caches: ['localStorage', 'cookie']
    }
  });

export default i18n;