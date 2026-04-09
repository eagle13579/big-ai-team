import { FileExplorerTool } from './FileExplorerTool';
import fs from 'fs/promises';
import path from 'path';
import { performance } from 'perf_hooks';

// 测试配置
const TEST_CONFIG = {
  workspaceRoot: path.join(__dirname, 'test_workspace'),
  testFilesCount: 1000,
  smallFileSize: 1024, // 1KB
  mediumFileSize: 1024 * 50, // 50KB
  largeFileSize: 1024 * 500, // 500KB
  concurrentOperations: 50,
  searchPatterns: ['function', 'class', 'import', 'export', 'const'],
  testDirectories: 10,
  filesPerDirectory: 100
};

// 生成随机字符串
function generateRandomString(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// 生成测试文件内容
function generateFileContent(size: number): string {
  const baseContent = `// Test file\n${generateRandomString(size - 10)}`;
  return baseContent.substring(0, size);
}

// 准备测试环境
async function setupTestEnvironment(): Promise<void> {
  console.log('Setting up test environment...');
  
  // 清理旧的测试目录
  try {
    await fs.rm(TEST_CONFIG.workspaceRoot, { recursive: true, force: true });
  } catch (error) {
    // 忽略错误
  }
  
  // 创建测试目录结构
  await fs.mkdir(TEST_CONFIG.workspaceRoot, { recursive: true });
  
  // 创建子目录
  for (let i = 0; i < TEST_CONFIG.testDirectories; i++) {
    const dirPath = path.join(TEST_CONFIG.workspaceRoot, `dir_${i}`);
    await fs.mkdir(dirPath, { recursive: true });
    
    // 在每个目录中创建文件
    for (let j = 0; j < TEST_CONFIG.filesPerDirectory; j++) {
      const fileSize = j % 3 === 0 ? TEST_CONFIG.smallFileSize : 
                      j % 3 === 1 ? TEST_CONFIG.mediumFileSize : 
                      TEST_CONFIG.largeFileSize;
      
      const filePath = path.join(dirPath, `file_${j}.txt`);
      const content = generateFileContent(fileSize);
      await fs.writeFile(filePath, content);
    }
  }
  
  console.log('Test environment setup complete!');
}

// 运行单个测试
async function runTest<T>(name: string, testFn: () => Promise<T>): Promise<{ result: T; duration: number }> {
  console.log(`\nRunning test: ${name}`);
  const startTime = performance.now();
  const result = await testFn();
  const duration = performance.now() - startTime;
  console.log(`Test ${name} completed in ${duration.toFixed(2)}ms`);
  return { result, duration };
}

// 压力测试
async function runStressTest() {
  // 准备测试环境
  await setupTestEnvironment();
  
  // 创建FileExplorerTool实例
  const tool = new FileExplorerTool({
    workspaceRoot: TEST_CONFIG.workspaceRoot,
    maxFileSize: 1024 * 1024, // 1MB
    enableCache: true,
    cacheSize: 200
  });
  
  const results: Record<string, number> = {};
  
  // 1. 测试列出文件（非递归）
  const { duration: listFilesDuration } = await runTest('List files (non-recursive)', async () => {
    await tool.listFiles(TEST_CONFIG.workspaceRoot, false);
  });
  results['List files (non-recursive)'] = listFilesDuration;
  
  // 2. 测试列出文件（递归）
  const { duration: listFilesRecursiveDuration } = await runTest('List files (recursive)', async () => {
    await tool.listFiles(TEST_CONFIG.workspaceRoot, true);
  });
  results['List files (recursive)'] = listFilesRecursiveDuration;
  
  // 3. 测试读取小文件
  const smallFilePath = path.join(TEST_CONFIG.workspaceRoot, 'dir_0', 'file_0.txt');
  const { duration: readSmallFileDuration } = await runTest('Read small file', async () => {
    await tool.readFile(smallFilePath);
  });
  results['Read small file'] = readSmallFileDuration;
  
  // 4. 测试读取大文件
  const largeFilePath = path.join(TEST_CONFIG.workspaceRoot, 'dir_0', 'file_2.txt');
  const { duration: readLargeFileDuration } = await runTest('Read large file', async () => {
    await tool.readFile(largeFilePath);
  });
  results['Read large file'] = readLargeFileDuration;
  
  // 5. 测试写入文件
  const writeFilePath = path.join(TEST_CONFIG.workspaceRoot, 'test_write.txt');
  const { duration: writeFileDuration } = await runTest('Write file', async () => {
    await tool.writeFile(writeFilePath, generateFileContent(TEST_CONFIG.mediumFileSize));
  });
  results['Write file'] = writeFileDuration;
  
  // 6. 测试搜索内容
  const { duration: searchContentDuration } = await runTest('Search content', async () => {
    await tool.searchContent('function', TEST_CONFIG.workspaceRoot);
  });
  results['Search content'] = searchContentDuration;
  
  // 7. 测试并发操作
  const { duration: concurrentDuration } = await runTest('Concurrent operations', async () => {
    const operations = [];
    for (let i = 0; i < TEST_CONFIG.concurrentOperations; i++) {
      const operationType = i % 4;
      
      if (operationType === 0) {
        // 读取文件
        const fileIndex = i % (TEST_CONFIG.testDirectories * TEST_CONFIG.filesPerDirectory);
        const dirIndex = Math.floor(fileIndex / TEST_CONFIG.filesPerDirectory);
        const fileIndexInDir = fileIndex % TEST_CONFIG.filesPerDirectory;
        const filePath = path.join(TEST_CONFIG.workspaceRoot, `dir_${dirIndex}`, `file_${fileIndexInDir}.txt`);
        operations.push(tool.readFile(filePath));
      } else if (operationType === 1) {
        // 写入文件
        const writePath = path.join(TEST_CONFIG.workspaceRoot, `concurrent_write_${i}.txt`);
        operations.push(tool.writeFile(writePath, generateFileContent(1024)));
      } else if (operationType === 2) {
        // 列出文件
        operations.push(tool.listFiles(TEST_CONFIG.workspaceRoot, false));
      } else {
        // 搜索内容
        const pattern = TEST_CONFIG.searchPatterns[i % TEST_CONFIG.searchPatterns.length];
        operations.push(tool.searchContent(pattern, TEST_CONFIG.workspaceRoot));
      }
    }
    
    await Promise.all(operations);
  });
  results['Concurrent operations'] = concurrentDuration;
  
  // 8. 测试缓存性能
  const { duration: cachedReadDuration } = await runTest('Cached read', async () => {
    await tool.readFile(smallFilePath);
  });
  results['Cached read'] = cachedReadDuration;
  
  // 输出测试结果
  console.log('\n=== Stress Test Results ===');
  console.log('Operation\t\tDuration (ms)');
  console.log('====================================');
  Object.entries(results).forEach(([operation, duration]) => {
    console.log(`${operation.padEnd(20)}	${duration.toFixed(2)}`);
  });
  
  // 计算性能指标
  const totalOperations = Object.keys(results).length;
  const totalDuration = Object.values(results).reduce((sum, duration) => sum + duration, 0);
  const averageDuration = totalDuration / totalOperations;
  
  console.log('====================================');
  console.log(`Total operations: ${totalOperations}`);
  console.log(`Total duration: ${totalDuration.toFixed(2)}ms`);
  console.log(`Average duration: ${averageDuration.toFixed(2)}ms`);
  
  // 清理测试环境
  console.log('\nCleaning up test environment...');
  await fs.rm(TEST_CONFIG.workspaceRoot, { recursive: true, force: true });
  console.log('Test environment cleaned up!');
}

// 运行测试
runStressTest().catch((error) => {
  console.error('Error running stress test:', error);
  process.exit(1);
});
