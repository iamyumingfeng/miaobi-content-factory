/**
 * EdgeOne Pages 边缘函数：将 /cos/* 反向代理到后端静态文件服务。
 *
 * 后端在 app/main.py 中通过 app.mount("/cos", StaticFiles(...)) 挂载了本地存储目录，
 * 前端部分素材/生成文件可能通过该路径访问。此处同样做同源代理，
 * 避免浏览器直连后端 HTTP 地址产生的混合内容问题。
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
  const target = backendOrigin + url.pathname + url.search

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

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body
  }

  return await fetch(target, init)
}
