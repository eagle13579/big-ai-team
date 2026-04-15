// 安全工具函数，用于输入验证和XSS防护

/**
 * 转义HTML特殊字符，防止XSS攻击
 * @param input 输入字符串
 * @returns 转义后的字符串
 */
export const escapeHtml = (input: string): string => {
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
};

/**
 * 验证用户名
 * @param username 用户名
 * @returns 验证结果
 */
export const validateUsername = (username: string): { isValid: boolean; message?: string } => {
  if (!username || username.trim().length < 3) {
    return { isValid: false, message: '用户名长度至少为3个字符' };
  }
  if (username.length > 20) {
    return { isValid: false, message: '用户名长度不能超过20个字符' };
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return { isValid: false, message: '用户名只能包含字母、数字和下划线' };
  }
  return { isValid: true };
};

/**
 * 验证密码强度
 * @param password 密码
 * @returns 验证结果
 */
export const validatePassword = (password: string): { isValid: boolean; message?: string } => {
  if (!password || password.length < 6) {
    return { isValid: false, message: '密码长度至少为6个字符' };
  }
  if (password.length > 50) {
    return { isValid: false, message: '密码长度不能超过50个字符' };
  }
  // 密码强度检查（至少包含一个字母和一个数字）
  if (!/^(?=.*[A-Za-z])(?=.*\d).+$/.test(password)) {
    return { isValid: false, message: '密码必须包含至少一个字母和一个数字' };
  }
  return { isValid: true };
};

/**
 * 验证任务查询
 * @param query 任务查询
 * @returns 验证结果
 */
export const validateTaskQuery = (query: string): { isValid: boolean; message?: string } => {
  if (!query || query.trim().length < 5) {
    return { isValid: false, message: '任务描述长度至少为5个字符' };
  }
  if (query.length > 1000) {
    return { isValid: false, message: '任务描述长度不能超过1000个字符' };
  }
  return { isValid: true };
};

/**
 * 清理和验证输入
 * @param input 输入字符串
 * @returns 清理后的字符串
 */
export const sanitizeInput = (input: string): string => {
  return escapeHtml(input.trim());
};
