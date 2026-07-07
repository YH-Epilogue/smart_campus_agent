/**
 * 知识库管理 API 接口
 *
 * 提供与后端 /api/v1/kb 端点交互的函数：
 * - listKBs: 获取知识库列表（支持分页参数）
 * - createKB: 创建新知识库（需提供名称、描述、所属部门）
 * - deleteKB: 删除知识库（会级联删除其下所有文档和向量）
 * - updateKB: 更新知识库名称和描述
 * - cloneKB: 克隆知识库（复制知识库及其文档，不复制向量）
 *
 * 权限说明：
 * - 老师只能看到/操作自己创建的知识库
 * - 管理员可以看到/操作所有知识库
 */
import http from "./http";

/**
 * 获取知识库列表
 * @param {object} params - 查询参数（可选，如分页、筛选等）
 * @returns {Array} 知识库数组
 */
export async function listKBs(params = {}) {
  const { data } = await http.get("/kb/", { params });
  return data;
}

/**
 * 创建新知识库
 * @param {string} name - 知识库名称
 * @param {string} description - 知识库描述
 * @param {string} department - 所属部门（用于分类管理）
 * @returns {object} 创建的知识库信息，包含自动生成的 ID
 */
export async function createKB(name, description, department) {
  const { data } = await http.post("/kb/", { name, description, department });
  return data;
}

/**
 * 删除指定知识库
 * @param {string} kbId - 知识库 ID
 * 注意：删除会级联删除其下所有文档和向量数据
 */
export async function deleteKB(kbId) {
  const { data } = await http.delete(`/kb/${kbId}`);
  return data;
}

/**
 * 更新知识库信息
 * @param {string} kbId - 知识库 ID
 * @param {string} name - 新名称
 * @param {string} description - 新描述
 */
export async function updateKB(kbId, name, description) {
  const { data } = await http.put(`/kb/${kbId}`, { name, description });
  return data;
}

/**
 * 克隆知识库（复制知识库及其文档结构）
 * @param {string} kbId - 要克隆的知识库 ID
 * @returns {object} 克隆后的新知识库信息
 */
export async function cloneKB(kbId) {
  const { data } = await http.post(`/kb/${kbId}/clone`);
  return data;
}
