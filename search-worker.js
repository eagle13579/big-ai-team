const fs = require('fs/promises');
const path = require('path');
const { parentPort, workerData } = require('worker_threads');

async function searchInDir(dir, pattern, ignoredPatterns, maxFileSize, results) {
  try {
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
        await searchInDir(entryPath, pattern, ignoredPatterns, maxFileSize, results);
      } else {
        try {
          // 检查文件大小
          const stats = await fs.stat(entryPath);
          if (stats.size > maxFileSize) {
            continue; // 跳过大文件
          }

          // 读取文件内容
          const content = await fs.readFile(entryPath, 'utf8');
          
          // 搜索匹配
          const lines = content.split('\n');
          const regex = new RegExp(pattern);
          for (let i = 0; i < lines.length; i++) {
            if (regex.test(lines[i])) {
              results.push({
                file: entryPath,
                line: i + 1,
                content: lines[i]
              });
            }
          }
        } catch (error) {
          // 忽略读取错误
        }
      }
    }
  } catch (error) {
    // 忽略目录读取错误
  }
}

async function workerSearch() {
  const { pattern, rootDir, ignoredPatterns, maxFileSize } = workerData;
  const results = [];
  
  await searchInDir(rootDir, pattern, ignoredPatterns, maxFileSize, results);
  
  if (parentPort) {
    parentPort.postMessage(results);
  }
}

workerSearch();
