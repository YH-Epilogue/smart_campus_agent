/**
 * JWT Token 工具函数
 *
 * 提供前端 JWT token 解码功能（不进行签名验证，仅用于客户端解析）
 * 解码 payload 中的用户信息（username、role）和过期时间
 *
 * 安全说明：此函数不做签名验证，仅用于前端读取用户信息
 * 真正的 token 验证由后端 API 完成
 */
export function decodeToken(token) {
  try {
    // JWT 格式：header.payload.signature，取中间的 payload 部分
    const payload = token.split(".")[1];
    if (!payload) return null;
    // Base64URL 解码：将 URL 安全的字符还原为标准 Base64，再 JSON 解析
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    // 检查 token 是否已过期（exp 是秒级时间戳，乘1000转毫秒比较）
    if (decoded.exp && decoded.exp * 1000 < Date.now()) {
      return null; // token 已过期，返回 null 触发重新登录
    }
    return decoded;
  } catch {
    return null; // token 格式错误或解码失败
  }
}
