// LuoyeChat 下载代理
// /dl/win -> 由 Cloudflare 边缘拉取 GitHub raw 的 Windows 安装包并流式转发
// 其余所有请求 -> 直接返回静态站点文件 (ASSETS)
// 背景: raw.githubusercontent.com 在中国大陆经常被重置, 访客直连下载失败;
//      Workers assets 单文件上限 25MiB, 73MiB 的 exe 不能直接放进静态资源, 故走 GitHub Release 资产。

const WIN_URL =
  "https://github.com/luoye-duck/LuoyeChat/releases/download/v2.6.0/LuoyeChat_Win_v2.6.0.exe";
const WIN_NAME = "LuoyeChat_Win_v2.6.0.exe";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/dl/win") {
      const cache = caches.default;
      const cacheKey = new Request("https://cache.internal/luoyechat/" + WIN_NAME, {
        method: "GET"
      });

      let res = await cache.match(cacheKey);
      if (!res) {
        let upstream = null;
        for (let attempt = 0; attempt < 3; attempt++) {
          upstream = await fetch(WIN_URL, { redirect: "follow" });
          if (upstream.ok) break;
          if (upstream.status === 404) break;
        }
        if (!upstream || !upstream.ok) {
          const code = upstream ? upstream.status : "network";
          return new Response(
            "Windows 安装包暂时无法获取（云端拉取失败: " + code + "），请稍后重试。",
            {
              status: 502,
              headers: { "Content-Type": "text/plain; charset=utf-8" }
            }
          );
        }
        res = new Response(upstream.body, upstream);
        res.headers.set("Cache-Control", "public, max-age=86400");
        ctx.waitUntil(cache.put(cacheKey, res.clone()));
      }

      const out = new Response(res.body, res);
      out.headers.set("Content-Disposition", 'attachment; filename="' + WIN_NAME + '"');
      return out;
    }

    return env.ASSETS.fetch(request);
  }
};
