/**
 * EdgeOne Pages 边缘函数：将 /api/* 反向代理到后端服务。
 *
 * 部署说明：
 * - 文件必须放在仓库根目录的 /functions/api/[[default]].js
 * - [[default]] 是 EdgeOne 的全匹配（catch-all）路由，可匹配 /api/v1/auth/login 等多级路径
 * - 浏览器始终与 EdgeOne(HTTPS) 同源通信，由边缘节点以服务端身份请求后端(HTTP)，
 *   因此不存在混合内容(Mixed Content)问题，也无需配置 CORS。
 *
 * 后端地址通过 EdgeOne 项目环境变量 BACKEND_API_ORIGIN 配置（必填，例如 http://111.230.94.186:8000），
 * 不在此处硬编码。
 */
export async function onRequest(context) {
  const { request, env } = context
  const backendOrigin = env && env.BACKEND_API_ORIGIN

  if (!backendOrigin) {
    return new Response(
      'Missing environment variable BACKEND_API_ORIGIN. Configure it in the EdgeOne project settings.',
      { status: 500, headers: { 'content-type': 'text/plain; charset=UTF-8' } }
    )
  }

  const url = new URL(request.url)
  // 保留原始 pathname（如 /api/v1/auth/login）与查询参数
  const target = backendOrigin + url.pathname + url.search

  // 复制请求头，但去掉 host（由运行时重新设置），避免后端按错误 host 处理
  const headers = new Headers(request.headers)
  headers.delete('host')
  headers.delete('cf-connecting-ip')
  headers.delete('cf-visitor')
  headers.delete('cf-ray')

  const init = {
    method: request.method,
    headers,
    redirect: 'follow',
  }

  // GET/HEAD 不能有 body
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body
  }

  const response = await fetch(target, init)

  // 透传后端响应；同源访问，浏览器不会触发 CORS 校验。
  return response
}
