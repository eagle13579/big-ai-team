/**
 * Memory management module
 */

class MemoryManager {
  /**
   * 初始化内存管理器
   * 创建一个空的内存存储对象。
   */
  constructor() {
    this.memoryStore = {};
  }

  /**
   * 存储内存数据
   * 将数据存储到内存中。
   * 
   * @param {string} key - 存储键
   * @param {any} value - 存储值
   * @returns {boolean} 存储是否成功
   */
  store(key, value) {
    this.memoryStore[key] = value;
    return true;
  }

  /**
   * 检索内存数据
   * 从内存中检索数据。
   * 
   * @param {string} key - 检索键
   * @returns {any} 检索到的数据，若不存在则返回undefined
   */
  retrieve(key) {
    return this.memoryStore[key];
  }

  /**
   * 删除内存数据
   * 从内存中删除数据。
   * 
   * @param {string} key - 要删除的键
   * @returns {boolean} 删除是否成功
   */
  delete(key) {
    if (key in this.memoryStore) {
      delete this.memoryStore[key];
      return true;
    }
    return false;
  }

  /**
   * 清空所有内存数据
   * 清空内存中的所有数据。
   * 
   * @returns {boolean} 清空是否成功
   */
  clear() {
    this.memoryStore = {};
    return true;
  }

  /**
   * 获取所有内存数据
   * 获取内存中存储的所有数据的副本。
   * 
   * @returns {object} 内存数据的副本
   */
  getAll() {
    return { ...this.memoryStore };
  }
}

module.exports = MemoryManager;