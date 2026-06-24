/**
 * 剪贴板工具函数
 * 兼容 HTTP 和 HTTPS 环境
 */

/**
 * 复制文本到剪贴板（兼容 HTTP/HTTPS）
 * @param text 要复制的文本
 * @returns Promise<boolean> 是否复制成功
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (!text) {
    return false
  }

  // 优先使用现代 Clipboard API（需要 HTTPS）
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (err) {
      console.warn('Clipboard API 失败，尝试降级方案:', err)
    }
  }

  // 降级方案：使用 execCommand（兼容 HTTP）
  return fallbackCopyToClipboard(text)
}

/**
 * 降级复制方案（使用 textarea + execCommand）
 * @param text 要复制的文本
 * @returns boolean 是否复制成功
 */
function fallbackCopyToClipboard(text: string): boolean {
  const textarea = document.createElement('textarea')
  textarea.value = text
  
  // 防止页面滚动
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  textarea.style.top = '-9999px'
  textarea.style.opacity = '0'
  
  document.body.appendChild(textarea)
  
  try {
    // 选中文本
    textarea.focus()
    textarea.select()
    textarea.setSelectionRange(0, textarea.value.length)
    
    // 执行复制命令
    const success = document.execCommand('copy')
    return success
  } catch (err) {
    console.error('降级复制方案失败:', err)
    return false
  } finally {
    // 清理
    document.body.removeChild(textarea)
  }
}

/**
 * 检查当前环境是否支持安全剪贴板 API
 * @returns boolean
 */
export function isClipboardApiSupported(): boolean {
  return !!(navigator.clipboard && window.isSecureContext)
}
