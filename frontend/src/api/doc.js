/**
 * 文档管理 API 接口
 *
 * 提供与后端 /api/v1/doc 端点交互的函数：
 * - 文档上传（单文件/批量）、删除、预览、编辑
 * - 文档版本管理（查看版本列表、回滚到指定版本）
 * - 向量管理（查看向量、去重、分块预览）
 *
 * 所有文档操作都需要先选择知识库（kbId），文档归属于知识库
 */
import http from "./http";

/**
 * 上传单个文档到指定知识库
 * @param {string} kbId - 目标知识库 ID
 * @param {File} file - 文件对象（浏览器 File API）
 * @returns {object} 上传结果，包含文档 ID 和元数据
 */
export async function uploadDoc(kbId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await http.post(`/doc/upload?kb_id=${kbId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * 获取指定知识库下的所有文档列表
 * @param {string} kbId - 知识库 ID
 * @returns {Array} 文档数组
 */
export async function listDocs(kbId) {
  const { data } = await http.get(`/doc/${kbId}`);
  return data;
}

/**
 * 删除指定文档
 * @param {string} docId - 文档 ID
 */
export async function deleteDoc(docId) {
  const { data } = await http.delete(`/doc/${docId}`);
  return data;
}

/**
 * 预览文档内容（获取文档纯文本或摘要）
 * @param {string} docId - 文档 ID
 * @returns {object} 文档预览内容
 */
export async function previewDoc(docId) {
  const { data } = await http.get(`/doc/${docId}/preview`);
  return data;
}

/**
 * 获取文档的版本历史列表
 * @param {string} docId - 文档 ID
 * @returns {Array} 版本列表，包含版本号和创建时间
 */
export async function getVersions(docId) {
  const { data } = await http.get(`/doc/${docId}/versions`);
  return data;
}

/**
 * 将文档回滚到指定版本
 * @param {string} docId - 文档 ID
 * @param {string} version - 目标版本号
 */
export async function rollbackDoc(docId, version) {
  const { data } = await http.post(`/doc/${docId}/rollback?version=${version}`);
  return data;
}

/**
 * 获取文档的向量分块信息（调试/查看用）
 * @param {string} docId - 文档 ID
 * @returns {Array} 向量分块列表，每块包含文本内容和向量维度
 */
export async function getVectors(docId) {
  const { data } = await http.get(`/doc/${docId}/vectors`);
  return data;
}

/**
 * 编辑文档内容（更新后端存储的文档文本）
 * @param {string} docId - 文档 ID
 * @param {string} content - 新的文档内容
 */
export async function editDoc(docId, content) {
  const { data } = await http.put(`/doc/${docId}/edit`, { content });
  return data;
}

/**
 * 批量上传多个文档到指定知识库
 * @param {string} kbId - 目标知识库 ID
 * @param {File[]} files - 文件对象数组
 * @returns {object} 批量上传结果，包含成功/失败计数
 */
export async function batchUpload(kbId, files) {
  const formData = new FormData();
  // 将所有文件追加到同一个 FormData（后端用 files 字段接收多文件）
  for (const file of files) {
    formData.append("files", file);
  }
  const { data } = await http.post(`/doc/batch_upload?kb_id=${kbId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * 对指定知识库的文档进行向量去重（清理重复的向量分块）
 * @param {string} kbId - 知识库 ID
 * @returns {object} 去重结果，包含移除的重复数量
 */
export async function dedupVectors(kbId) {
  const { data } = await http.post(`/doc/${kbId}/dedup`);
  return data;
}

/**
 * 分块预览：查看文档按指定参数切分后的效果
 * @param {string} docId - 文档 ID
 * @param {number} chunkSize - 分块大小（字符数）
 * @param {number} overlap - 相邻分块的重叠字符数
 * @returns {Array} 分块结果预览
 */
export async function splitPreview(docId, chunkSize, overlap) {
  const { data } = await http.post(`/doc/${docId}/split_preview`, {
    chunk_size: chunkSize,
    chunk_overlap: overlap,
  });
  return data;
}
