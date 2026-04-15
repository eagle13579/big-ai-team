import log from 'loglevel';

// 配置日志级别
log.setLevel(process.env.NODE_ENV === 'production' ? 'info' : 'debug');

// 扩展loglevel类型，添加结构化日志方法
declare module 'loglevel' {
  interface Logger {
    infoWithMeta(message: string, meta?: Record<string, any>): void;
    errorWithMeta(message: string, meta?: Record<string, any>): void;
    warnWithMeta(message: string, meta?: Record<string, any>): void;
    debugWithMeta(message: string, meta?: Record<string, any>): void;
  }
}

// 日志队列，用于聚合日志
const logQueue: Array<{
  level: string;
  message: string;
  meta: Record<string, any>;
  timestamp: string;
}> = [];

// 最大日志队列长度
const MAX_QUEUE_SIZE = 1000;

// 日志聚合间隔（毫秒）
const AGGREGATION_INTERVAL = 5000;

// 结构化日志方法
log.infoWithMeta = (message: string, meta: Record<string, any> = {}) => {
  const logEntry = {
    level: 'info',
    message,
    meta: {
      ...meta,
      userId: meta.userId || 'anonymous',
      component: meta.component || 'unknown',
      action: meta.action || 'unknown'
    },
    timestamp: new Date().toISOString()
  };
  
  // 添加到日志队列
  if (logQueue.length >= MAX_QUEUE_SIZE) {
    logQueue.shift();
  }
  logQueue.push(logEntry);
  
  // 输出结构化日志
  log.info(JSON.stringify(logEntry));
};

log.errorWithMeta = (message: string, meta: Record<string, any> = {}) => {
  const logEntry = {
    level: 'error',
    message,
    meta: {
      ...meta,
      userId: meta.userId || 'anonymous',
      component: meta.component || 'unknown',
      action: meta.action || 'unknown',
      error: meta.error?.message || meta.error || 'unknown error'
    },
    timestamp: new Date().toISOString()
  };
  
  // 添加到日志队列
  if (logQueue.length >= MAX_QUEUE_SIZE) {
    logQueue.shift();
  }
  logQueue.push(logEntry);
  
  // 输出结构化日志
  log.error(JSON.stringify(logEntry));
};

log.warnWithMeta = (message: string, meta: Record<string, any> = {}) => {
  const logEntry = {
    level: 'warn',
    message,
    meta: {
      ...meta,
      userId: meta.userId || 'anonymous',
      component: meta.component || 'unknown',
      action: meta.action || 'unknown'
    },
    timestamp: new Date().toISOString()
  };
  
  // 添加到日志队列
  if (logQueue.length >= MAX_QUEUE_SIZE) {
    logQueue.shift();
  }
  logQueue.push(logEntry);
  
  // 输出结构化日志
  log.warn(JSON.stringify(logEntry));
};

log.debugWithMeta = (message: string, meta: Record<string, any> = {}) => {
  const logEntry = {
    level: 'debug',
    message,
    meta: {
      ...meta,
      userId: meta.userId || 'anonymous',
      component: meta.component || 'unknown',
      action: meta.action || 'unknown'
    },
    timestamp: new Date().toISOString()
  };
  
  // 添加到日志队列
  if (logQueue.length >= MAX_QUEUE_SIZE) {
    logQueue.shift();
  }
  logQueue.push(logEntry);
  
  // 输出结构化日志
  log.debug(JSON.stringify(logEntry));
};

// 定期聚合日志（实际项目中可以发送到日志服务器）
setInterval(() => {
  if (logQueue.length > 0) {
    // 这里可以实现日志聚合逻辑，例如发送到日志服务器
    console.log('Aggregating logs:', logQueue.length, 'entries');
    
    // 清空日志队列
    logQueue.length = 0;
  }
}, AGGREGATION_INTERVAL);

export default log;