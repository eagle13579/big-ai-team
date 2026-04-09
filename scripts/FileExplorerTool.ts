import fs from 'fs/promises';
import * as fsSync from 'fs';
import path from 'path';
import { performance } from 'perf_hooks';
import { createLogger, format, transports } from 'winston';
import { Worker } from 'worker_threads';
import { EventEmitter } from 'events';

// 配置接口
export interface FileExplorerConfig {
  workspaceRoot: string;
  maxFileSize: number;
  ignoredPatterns: string[];
  enableCache: boolean;
  cacheSize: number;
  maxConcurrentSearches: number;
  enableFileWatcher: boolean;
  searchIndexEnabled: boolean;
}

// 错误类型
export class FileExplorerError extends Error {
  public code: string;
  
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = 'FileExplorerError';
  }
}

// 搜索结果接口
export interface SearchResult {
  file: string;
  line: number;
  content: string;
}

// 搜索索引项
interface SearchIndexItem {
  file: string;
  lines: string[];
  lastModified: number;
}

// 任务队列项
interface QueueItem {
  id: string;
  type: 'search' | 'read' | 'write' | 'list' | 'delete' | 'create';
  params: any;
  resolve: (result: any) => void;
  reject: (error: Error) => void;
  timestamp: number;
}

// LRU缓存实现
class LRUCache<K, V> {
  private cache: Map<K, V>;
  private capacity: number;

  constructor(capacity: number) {
    this.cache = new Map();
    this.capacity = capacity;
  }

  get(key: K): V | undefined {
    if (!this.cache.has(key)) return undefined;
    
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value!);
    return value;
  }

  set(key: K, value: V): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.capacity) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey !== undefined) {
        this.cache.delete(firstKey);
      }
    }
    this.cache.set(key, value);
  }

  delete(key: K): boolean {
    return this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }
}

// 任务队列
class TaskQueue {
  private queue: QueueItem[] = [];
  private running: number = 0;
  private maxConcurrent: number;

  constructor(maxConcurrent: number = 10) {
    this.maxConcurrent = maxConcurrent;
  }

  add(type: QueueItem['type'], params: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const item: QueueItem = {
        id: Date.now().toString(36) + Math.random().toString(36).substr(2),
        type,
        params,
        resolve,
        reject,
        timestamp: Date.now()
      };

      this.queue.push(item);
      this.process();
    });
  }

  private async process(): Promise<void> {
    if (this.running >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    const item = this.queue.shift();
    if (!item) return;

    this.running++;

    try {
      let result;
      switch (item.type) {
        case 'search':
          // 搜索操作由专门的搜索服务处理
          result = await item.params.execute();
          break;
        case 'read':
          result = await item.params.execute();
          break;
        case 'write':
          result = await item.params.execute();
          break;
        case 'list':
          result = await item.params.execute();
          break;
        case 'delete':
          result = await item.params.execute();
          break;
        case 'create':
          result = await item.params.execute();
          break;
        default:
          throw new Error(`Unknown task type: ${item.type}`);
      }
      item.resolve(result);
    } catch (error) {
      item.reject(error as Error);
    } finally {
      this.running--;
      this.process();
    }
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  getRunningCount(): number {
    return this.running;
  }
}

// 搜索服务
class SearchService {
  private index: Map<string, SearchIndexItem> = new Map();
  private indexEnabled: boolean;
  private logger;

  constructor(indexEnabled: boolean, logger: any) {
    this.indexEnabled = indexEnabled;
    this.logger = logger;
  }

  // 构建搜索索引
  async buildIndex(rootDir: string, ignoredPatterns: string[]): Promise<void> {
    if (!this.indexEnabled) return;

    const startTime = performance.now();
    this.index.clear();

    const traverse = async (dir: string) => {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      for (const entry of entries) {
        const entryPath = path.join(dir, entry.name);
        
        // 检查是否应被忽略
        if (ignoredPatterns.some(pattern => 
          entryPath.includes(path.sep + pattern + path.sep) ||
          entryPath.endsWith(path.sep + pattern)
        )) {
          continue;
        }

        if (entry.isDirectory()) {
          await traverse(entryPath);
        } else {
          try {
            const stats = await fs.stat(entryPath);
            if (stats.size > 1024 * 1024) { // 跳过大于1MB的文件
              continue;
            }
            const content = await fs.readFile(entryPath, 'utf8');
            const lines = content.split('\n');
            this.index.set(entryPath, {
              file: entryPath,
              lines,
              lastModified: stats.mtimeMs
            });
          } catch (error) {
            // 忽略读取错误
          }
        }
      }
    }

    await traverse(rootDir);
    const duration = performance.now() - startTime;
    this.logger.info('Search index built', {
      filesIndexed: this.index.size,
      duration: `${duration.toFixed(2)}ms`
    });
  }

  // 更新索引
  async updateIndex(filePath: string): Promise<void> {
    if (!this.indexEnabled) return;

    try {
      const stats = await fs.stat(filePath);
      if (stats.size > 1024 * 1024) { // 跳过大于1MB的文件
        this.index.delete(filePath);
        return;
      }
      const content = await fs.readFile(filePath, 'utf8');
      const lines = content.split('\n');
      this.index.set(filePath, {
        file: filePath,
        lines,
        lastModified: stats.mtimeMs
      });
    } catch (error) {
      this.index.delete(filePath);
    }
  }

  // 从索引中删除
  removeFromIndex(filePath: string): void {
    if (!this.indexEnabled) return;
    this.index.delete(filePath);
  }

  // 使用索引搜索
  search(pattern: string): SearchResult[] {
    if (!this.indexEnabled) return [];

    const regex = new RegExp(pattern);
    const results: SearchResult[] = [];

    for (const [file, item] of this.index.entries()) {
      for (let i = 0; i < item.lines.length; i++) {
        if (regex.test(item.lines[i])) {
          results.push({
            file,
            line: i + 1,
            content: item.lines[i]
          });
        }
      }
    }

    return results;
  }

  // 检查文件是否需要更新索引
  async shouldUpdateIndex(filePath: string): Promise<boolean> {
    if (!this.indexEnabled) return false;

    const item = this.index.get(filePath);
    if (!item) return true;

    try {
      const stats = await fs.stat(filePath);
      return stats.mtimeMs > item.lastModified;
    } catch (error) {
      return false;
    }
  }

  // 获取索引大小
  getIndexSize(): number {
    return this.index.size;
  }
}



// 主类
export class FileExplorerTool extends EventEmitter {
  private readonly config: FileExplorerConfig;
  private readonly logger;
  private readonly pathCache: LRUCache<string, string>;
  private readonly contentCache: LRUCache<string, string>;
  private readonly taskQueue: TaskQueue;
  private readonly searchService: SearchService;
  private fileWatcher: fsSync.FSWatcher | null = null;

  /**
   * 创建FileExplorerTool实例
   * @param config 配置选项
   */
  constructor(config?: Partial<FileExplorerConfig>) {
    super();
    
    this.config = {
      workspaceRoot: config?.workspaceRoot || 'D:/workspace',
      maxFileSize: config?.maxFileSize || 1024 * 1024, // 1MB
      ignoredPatterns: config?.ignoredPatterns || [
        'node_modules', '.git', 'dist', 'build', 'coverage',
        '.env', '.next', '.nuxt', 'vendor', '.vscode', '.idea'
      ],
      enableCache: config?.enableCache ?? true,
      cacheSize: config?.cacheSize || 500, // 增加缓存大小
      maxConcurrentSearches: config?.maxConcurrentSearches || 5,
      enableFileWatcher: config?.enableFileWatcher ?? true,
      searchIndexEnabled: config?.searchIndexEnabled ?? true
    };

    // 初始化日志
    this.logger = createLogger({
      level: 'info',
      format: format.combine(
        format.timestamp(),
        format.json()
      ),
      transports: [
        new transports.Console(),
        new transports.File({ filename: 'file-explorer.log' })
      ]
    });

    // 初始化缓存
    this.pathCache = new LRUCache<string, string>(this.config.cacheSize);
    this.contentCache = new LRUCache<string, string>(this.config.cacheSize);

    // 初始化任务队列
    this.taskQueue = new TaskQueue(this.config.maxConcurrentSearches);

    // 初始化搜索服务
    this.searchService = new SearchService(this.config.searchIndexEnabled, this.logger);

    // 初始化文件监听器
    if (this.config.enableFileWatcher) {
      this.initializeFileWatcher();
    }

    // 缓存预热
    this.prewarmCache();

    this.logger.info('FileExplorerTool initialized', {
      workspaceRoot: this.config.workspaceRoot,
      maxFileSize: this.config.maxFileSize,
      ignoredPatterns: this.config.ignoredPatterns.length,
      maxConcurrentSearches: this.config.maxConcurrentSearches,
      enableFileWatcher: this.config.enableFileWatcher,
      searchIndexEnabled: this.config.searchIndexEnabled
    });
  }

  /**
   * 初始化文件监听器
   */
  private initializeFileWatcher(): void {
    try {
      this.fileWatcher = fsSync.watch(this.config.workspaceRoot, {
        recursive: true,
        encoding: 'utf8'
      }, async (eventType, filename) => {
        if (!filename) return;

        const filePath = path.join(this.config.workspaceRoot, filename);
        
        if (eventType === 'change') {
          // 文件修改，更新缓存和索引
          this.contentCache.delete(filePath);
          await this.searchService.updateIndex(filePath);
          this.emit('fileChanged', filePath);
        } else if (eventType === 'rename') {
          // 文件重命名或删除，清理缓存和索引
          this.contentCache.delete(filePath);
          this.searchService.removeFromIndex(filePath);
          this.emit('fileRenamed', filePath);
        }
      });

      this.logger.info('File watcher initialized');
    } catch (error) {
      this.logger.warn('Failed to initialize file watcher', { error: (error as Error).message });
    }
  }

  /**
   * 缓存预热
   */
  private async prewarmCache(): Promise<void> {
    try {
      const startTime = performance.now();
      
      // 预热路径缓存
      const rootEntries = await fs.readdir(this.config.workspaceRoot, { withFileTypes: true });
      for (const entry of rootEntries) {
        const entryPath = path.join(this.config.workspaceRoot, entry.name);
        if (!this.shouldIgnore(entryPath)) {
          const cacheKey = `validate:${entryPath}`;
          this.pathCache.set(cacheKey, entryPath);
        }
      }

      // 构建搜索索引
      if (this.config.searchIndexEnabled) {
        await this.searchService.buildIndex(this.config.workspaceRoot, this.config.ignoredPatterns);
      }

      const duration = performance.now() - startTime;
      this.logger.info('Cache prewarmed', {
        duration: `${duration.toFixed(2)}ms`,
        pathCacheSize: this.pathCache.size(),
        searchIndexSize: this.searchService.getIndexSize()
      });
    } catch (error) {
      this.logger.warn('Cache prewarming failed', { error: (error as Error).message });
    }
  }

  /**
   * 验证路径是否在工作空间内
   * @param filePath 要验证的路径
   * @returns 解析后的绝对路径
   * @throws FileExplorerError 如果路径在工作空间外
   */
  private validatePath(filePath: string): string {
    if (!filePath) {
      throw new FileExplorerError('INVALID_PATH', 'File path cannot be empty');
    }

    // 尝试从缓存获取
    const cacheKey = `validate:${filePath}`;
    if (this.config.enableCache) {
      const cached = this.pathCache.get(cacheKey);
      if (cached) {
        return cached;
      }
    }

    const resolvedPath = path.resolve(filePath);
    const normalizedRoot = path.normalize(this.config.workspaceRoot);
    const normalizedPath = path.normalize(resolvedPath);

    // 确保路径完全在工作空间内
    if (!normalizedPath.startsWith(normalizedRoot)) {
      throw new FileExplorerError(
        'PATH_OUTSIDE_WORKSPACE',
        `Path ${filePath} is outside the workspace root`
      );
    }

    // 缓存结果
    if (this.config.enableCache) {
      this.pathCache.set(cacheKey, resolvedPath);
    }

    return resolvedPath;
  }

  /**
   * 检查文件是否应被忽略
   * @param filePath 文件路径
   * @returns 是否应被忽略
   */
  private shouldIgnore(filePath: string): boolean {
    return this.config.ignoredPatterns.some(pattern => 
      filePath.includes(path.sep + pattern + path.sep) ||
      filePath.endsWith(path.sep + pattern)
    );
  }

  /**
   * 列出目录中的文件和文件夹
   * @param dirPath 目录路径
   * @param recursive 是否递归列出
   * @returns 文件/文件夹路径数组
   */
  async listFiles(dirPath: string, recursive: boolean = false): Promise<string[]> {
    return this.taskQueue.add('list', {
      execute: async () => {
        const startTime = performance.now();
        const operationId = `list:${dirPath}:${recursive}`;

        try {
          const resolvedDir = this.validatePath(dirPath);
          const entries = await fs.readdir(resolvedDir, { withFileTypes: true });
          const result: string[] = [];

          for (const entry of entries) {
            const entryPath = path.join(resolvedDir, entry.name);

            // 检查是否应被忽略
            if (this.shouldIgnore(entryPath)) {
              continue;
            }

            result.push(entryPath);

            if (entry.isDirectory() && recursive) {
              try {
                const subEntries = await this.listFiles(entryPath, recursive);
                result.push(...subEntries);
              } catch (error: any) {
                this.logger.warn('Error listing subdirectory', {
                  path: entryPath,
                  error: error.message
                });
              }
            }
          }

          const duration = performance.now() - startTime;
          this.logger.info('List files completed', {
            path: dirPath,
            recursive,
            count: result.length,
            duration: `${duration.toFixed(2)}ms`,
            operationId
          });

          return result;
        } catch (error: any) {
          if (error.code === 'ENOENT') {
            throw new FileExplorerError('DIRECTORY_NOT_FOUND', `Directory not found: ${dirPath}`);
          } else if (error.code === 'EPERM') {
            throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${dirPath}`);
          } else if (error instanceof FileExplorerError) {
            throw error;
          }
          throw new FileExplorerError('UNKNOWN_ERROR', `Error listing files: ${error.message}`);
        }
      }
    });
  }

  /**
   * 读取文件内容
   * @param filePath 文件路径
   * @returns 文件内容
   */
  async readFile(filePath: string): Promise<string> {
    return this.taskQueue.add('read', {
      execute: async () => {
        const startTime = performance.now();

        try {
          const resolvedPath = this.validatePath(filePath);

          // 尝试从缓存获取
          if (this.config.enableCache) {
            const cached = this.contentCache.get(resolvedPath);
            if (cached) {
              this.logger.info('File read from cache', { path: filePath });
              return cached;
            }
          }

          // 检查文件大小
          const stats = await fs.stat(resolvedPath);
          if (stats.size > this.config.maxFileSize) {
            throw new FileExplorerError(
              'FILE_TOO_LARGE',
              `File size exceeds limit (${this.config.maxFileSize} bytes): ${filePath}`
            );
          }

          // 读取文件内容
          const content = await fs.readFile(resolvedPath, 'utf8');

          // 缓存内容
          if (this.config.enableCache) {
            this.contentCache.set(resolvedPath, content);
          }

          const duration = performance.now() - startTime;
          this.logger.info('File read completed', {
            path: filePath,
            size: content.length,
            duration: `${duration.toFixed(2)}ms`
          });

          return content;
        } catch (error: any) {
          if (error.code === 'ENOENT') {
            throw new FileExplorerError('FILE_NOT_FOUND', `File not found: ${filePath}`);
          } else if (error.code === 'EPERM') {
            throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${filePath}`);
          } else if (error instanceof FileExplorerError) {
            throw error;
          }
          throw new FileExplorerError('UNKNOWN_ERROR', `Error reading file: ${error.message}`);
        }
      }
    });
  }

  /**
   * 写入文件内容
   * @param filePath 文件路径
   * @param content 文件内容
   */
  async writeFile(filePath: string, content: string): Promise<void> {
    return this.taskQueue.add('write', {
      execute: async () => {
        const startTime = performance.now();

        try {
          const resolvedPath = this.validatePath(filePath);

          // 确保父目录存在
          const parentDir = path.dirname(resolvedPath);
          await fs.mkdir(parentDir, { recursive: true });

          // 写入文件
          await fs.writeFile(resolvedPath, content, 'utf8');

          // 更新缓存
          if (this.config.enableCache) {
            this.contentCache.set(resolvedPath, content);
          }

          // 更新搜索索引
          await this.searchService.updateIndex(resolvedPath);

          const duration = performance.now() - startTime;
          this.logger.info('File written', {
            path: filePath,
            size: content.length,
            duration: `${duration.toFixed(2)}ms`
          });
        } catch (error: any) {
          if (error.code === 'EPERM') {
            throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${filePath}`);
          } else if (error instanceof FileExplorerError) {
            throw error;
          }
          throw new FileExplorerError('UNKNOWN_ERROR', `Error writing file: ${error.message}`);
        }
      }
    });
  }

  /**
   * 搜索文件内容
   * @param pattern 搜索模式
   * @param rootDir 根目录
   * @returns 搜索结果数组
   */
  async searchContent(pattern: string, rootDir: string): Promise<SearchResult[]> {
    return this.taskQueue.add('search', {
      execute: async () => {
        const startTime = performance.now();
        const operationId = `search:${pattern}:${rootDir}`;

        try {
          if (!pattern) {
            throw new FileExplorerError('INVALID_PATTERN', 'Search pattern cannot be empty');
          }

          const resolvedRoot = this.validatePath(rootDir);

          // 尝试使用搜索索引
          if (this.config.searchIndexEnabled) {
            const indexResults = this.searchService.search(pattern);
            if (indexResults.length > 0) {
              const duration = performance.now() - startTime;
              this.logger.info('Search completed using index', {
                pattern,
                rootDir,
                results: indexResults.length,
                duration: `${duration.toFixed(2)}ms`,
                operationId
              });
              return indexResults;
            }
          }

          // 使用工作线程进行并行搜索
          return new Promise((resolve, reject) => {
            const worker = new Worker('./search-worker.js', {
              workerData: {
                pattern,
                rootDir: resolvedRoot,
                ignoredPatterns: this.config.ignoredPatterns,
                maxFileSize: this.config.maxFileSize
              }
            });

            worker.on('message', (results: SearchResult[]) => {
              const duration = performance.now() - startTime;
              this.logger.info('Search completed using worker', {
                pattern,
                rootDir,
                results: results.length,
                duration: `${duration.toFixed(2)}ms`,
                operationId
              });
              resolve(results);
            });

            worker.on('error', (error) => {
              reject(new FileExplorerError('SEARCH_ERROR', `Search failed: ${(error as Error).message}`));
            });

            worker.on('exit', (code) => {
              if (code !== 0) {
                reject(new FileExplorerError('SEARCH_ERROR', `Worker exited with code ${code}`));
              }
            });
          });
        } catch (error: any) {
          if (error.code === 'ENOENT') {
            throw new FileExplorerError('DIRECTORY_NOT_FOUND', `Directory not found: ${rootDir}`);
          } else if (error.code === 'EPERM') {
            throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${rootDir}`);
          } else if (error instanceof FileExplorerError) {
            throw error;
          }
          throw new FileExplorerError('UNKNOWN_ERROR', `Error searching content: ${error.message}`);
        }
      }
    });
  }

  /**
   * 删除文件
   * @param filePath 文件路径
   */
  async deleteFile(filePath: string): Promise<void> {
    return this.taskQueue.add('delete', {
      execute: async () => {
        const startTime = performance.now();

        try {
          const resolvedPath = this.validatePath(filePath);

          await fs.unlink(resolvedPath);

          // 从缓存中移除
          if (this.config.enableCache) {
            this.contentCache.delete(resolvedPath);
          }

          // 从搜索索引中移除
          this.searchService.removeFromIndex(resolvedPath);

          const duration = performance.now() - startTime;
          this.logger.info('File deleted', {
            path: filePath,
            duration: `${duration.toFixed(2)}ms`
          });
        } catch (error: any) {
          if (error.code === 'ENOENT') {
            throw new FileExplorerError('FILE_NOT_FOUND', `File not found: ${filePath}`);
          } else if (error.code === 'EPERM') {
            throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${filePath}`);
          } else if (error instanceof FileExplorerError) {
            throw error;
          }
          throw new FileExplorerError('UNKNOWN_ERROR', `Error deleting file: ${error.message}`);
        }
      }
    });
  }

  /**
   * 创建目录
   * @param dirPath 目录路径
   * @param recursive 是否递归创建
   */
  async createDirectory(dirPath: string, recursive: boolean = true): Promise<void> {
    return this.taskQueue.add('create', {
      execute: async () => {
        const startTime = performance.now();

        try {
          const resolvedPath = this.validatePath(dirPath);

          await fs.mkdir(resolvedPath, { recursive });

          // 从缓存中移除
          if (this.config.enableCache) {
            this.pathCache.clear();
          }

          const duration = performance.now() - startTime;
          this.logger.info('Directory created', {
            path: dirPath,
            recursive,
            duration: `${duration.toFixed(2)}ms`
          });
        } catch (error: any) {
          if (error.code === 'EPERM') {
            throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${dirPath}`);
          } else if (error instanceof FileExplorerError) {
            throw error;
          }
          throw new FileExplorerError('UNKNOWN_ERROR', `Error creating directory: ${error.message}`);
        }
      }
    });
  }

  /**
   * 获取文件信息
   * @param filePath 文件路径
   * @returns 文件信息
   */
  async getFileInfo(filePath: string): Promise<fsSync.Stats> {
    try {
      const resolvedPath = this.validatePath(filePath);
      return await fs.stat(resolvedPath);
    } catch (error: any) {
      if (error.code === 'ENOENT') {
        throw new FileExplorerError('FILE_NOT_FOUND', `File not found: ${filePath}`);
      } else if (error.code === 'EPERM') {
        throw new FileExplorerError('PERMISSION_DENIED', `Permission denied: ${filePath}`);
      } else if (error instanceof FileExplorerError) {
        throw error;
      }
      throw new FileExplorerError('UNKNOWN_ERROR', `Error getting file info: ${error.message}`);
    }
  }

  /**
   * 清理缓存
   */
  clearCache(): void {
    this.pathCache.clear();
    this.contentCache.clear();
    this.logger.info('Cache cleared');
  }

  /**
   * 获取缓存状态
   * @returns 缓存状态
   */
  getCacheStatus(): {
    pathCacheSize: number;
    contentCacheSize: number;
    searchIndexSize: number;
    queueSize: number;
    runningTasks: number;
  } {
    return {
      pathCacheSize: this.pathCache.size(),
      contentCacheSize: this.contentCache.size(),
      searchIndexSize: this.searchService.getIndexSize(),
      queueSize: this.taskQueue.getQueueSize(),
      runningTasks: this.taskQueue.getRunningCount()
    };
  }

  /**
   * 关闭文件监听器
   */
  close(): void {
    if (this.fileWatcher) {
      this.fileWatcher.close();
      this.logger.info('File watcher closed');
    }
  }
}


