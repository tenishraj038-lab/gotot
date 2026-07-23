export async function onRequest(context) {
  const { request, env } = context;
  const backendUrl = env.BACKEND_API_URL || "https://gotot-api.onrender.com";
  const url = new URL(request.url);
  url.hostname = new URL(backendUrl).hostname;
  url.protocol = "https:";
  url.port = "";

  const reqHeaders = new Headers(request.headers);
  reqHeaders.delete("host");
  reqHeaders.set("X-Forwarded-For", request.headers.get("CF-Connecting-IP") || "");

  const fetchOptions = {
    method: request.method,
    headers: reqHeaders,
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    fetchOptions.body = await request.text();
  }

  const response = await fetch(url.toString(), fetchOptions);
  const respHeaders = new Headers(response.headers);
  respHeaders.set("X-Proxied-By", "Cloudflare-Pages");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: respHeaders,
  });
}
