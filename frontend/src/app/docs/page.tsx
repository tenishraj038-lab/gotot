"use client";

import { motion } from "framer-motion";
import { BookOpen, Key, Download, Shield, CreditCard, Globe, Code, Terminal } from "lucide-react";
import Link from "next/link";

const sections = [
  {
    id: "overview",
    icon: BookOpen,
    title: "Overview",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <p>GoTot provides a RESTful API for downloading videos from 11+ platforms. The API is available at <code className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm">https://gotot.app/api</code>.</p>
        <h3>Base URL</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">https://gotot.app/api</pre>
        <h3>Authentication</h3>
        <p>All endpoints except <code>/health</code> and <code>/contact</code> require authentication via Bearer token or API key.</p>
        <h3>Rate Limiting</h3>
        <p>Free: 60 req/min. Pro: 300 req/min. Unlimited: 1000 req/min. Exceeded limits return <code>429 Too Many Requests</code>.</p>
        <h3>Content Type</h3>
        <p>All requests and responses use <code>application/json</code>.</p>
      </div>
    ),
  },
  {
    id: "auth",
    icon: Key,
    title: "Authentication",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <h3>Register a new account</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /auth/register
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "Str0ngPass!"
}`}</pre>
        <h3>Login</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /auth/login
{
  "email": "user@example.com",
  "password": "Str0ngPass!"
}`}</pre>
        <h4>Response</h4>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}`}</pre>
        <p className="mt-4">Use the <code>access_token</code> in subsequent requests via the <code>Authorization: Bearer &lt;token&gt;</code> header.</p>
        <p>When the access token expires (60 min), use the <code>refresh_token</code> to get a new one:</p>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /auth/refresh
{
  "refresh_token": "eyJhbGci..."
}`}</pre>
      </div>
    ),
  },
  {
    id: "api-keys",
    icon: Key,
    title: "API Keys",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <p>For programmatic access, generate an API key. Keys are tier-based with different rate limits.</p>
        <h3>Create an API key</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /api-keys/create
Authorization: Bearer <token>
{
  "name": "My CLI Tool"
}`}</pre>
        <h3>Use an API key</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`GET /download/info
X-API-Key: gt_abc123...`}</pre>
        <h3>List keys</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /api-keys/list</pre>
        <h3>Revoke a key</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{'POST /api-keys/{key_id}/revoke'}</pre>
        <table className="w-full text-sm mt-4">
          <thead><tr><th>Tier</th><th>Daily Limit</th><th>Max Keys</th></tr></thead>
          <tbody>
            <tr><td>Free</td><td>50 requests</td><td>2</td></tr>
            <tr><td>Pro</td><td>1,000 requests</td><td>10</td></tr>
            <tr><td>Unlimited</td><td>10,000 requests</td><td>Unlimited</td></tr>
          </tbody>
        </table>
      </div>
    ),
  },
  {
    id: "download",
    icon: Download,
    title: "Download Endpoints",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <h3>Get video information</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /download/info
Authorization: Bearer <token>
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}

Response:
{
  "title": "Rick Astley - Never Gonna Give You Up",
  "platform": "youtube",
  "duration": 212,
  "thumbnail": "https://i.ytimg.com/vi/...",
  "formats": [...],
  "requires_payment": false
}`}</pre>

        <h3>Start a download</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /download/start
Authorization: Bearer <token>
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "22",
  "as_mp3": false
}`}</pre>

        <h3>Check download queue status</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{'GET /download/queue/{task_id}'}</pre>

        <h3>Get download history</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /download/history?skip=0&limit=50</pre>

        <h3>Search downloads</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /download/search?q=rick+astley</pre>
      </div>
    ),
  },
  {
    id: "subscriptions",
    icon: CreditCard,
    title: "Subscriptions & Payments",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <h3>Check subscription status</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /subscription/status</pre>

        <h3>Create subscription checkout</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /payment/create-subscription
Authorization: Bearer <token>
{
  "tier": "pro"
}`}</pre>

        <h3>Pay per download</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /payment/pay-per-download
Authorization: Bearer <token>
{
  "email": "user@example.com"
}`}</pre>

        <h3>Cancel subscription</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">POST /subscription/cancel</pre>

        <h3>Payment history</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /payment/history?skip=0&limit=20</pre>
      </div>
    ),
  },
  {
    id: "referrals",
    icon: Globe,
    title: "Referrals & Affiliates",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <h3>Get referral code</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /referrals/my-code</pre>

        <h3>Apply a referral code</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`POST /referrals/apply
Authorization: Bearer <token>
{
  "code": "GOTOTABC123"
}`}</pre>

        <h3>List affiliate links</h3>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">GET /affiliates/links</pre>
      </div>
    ),
  },
  {
    id: "code-examples",
    icon: Code,
    title: "Code Examples",
    content: (
      <div className="prose dark:prose-invert max-w-none space-y-6">
        <div>
          <h3 className="flex items-center gap-2"><Terminal className="w-4 h-4" /> cURL</h3>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`# Get video info
curl -X POST https://gotot.app/api/download/info \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"url":"https://youtube.com/watch?v=..."}'`}</pre>
        </div>

        <div>
          <h3 className="flex items-center gap-2"><Code className="w-4 h-4" /> Python</h3>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`import requests

API = "https://gotot.app/api"
TOKEN = "your_access_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Get video info
resp = requests.post(
    f"{API}/download/info",
    json={"url": "https://youtube.com/watch?v=..."},
    headers=headers,
)
data = resp.json()
print(f"Title: {data['title']}")

# Start download
resp = requests.post(
    f"{API}/download/start",
    json={"url": data["url"], "format_id": data["formats"][0]["format_id"]},
    headers=headers,
)
result = resp.json()
print(f"Download URL: {result['download_url']}")`}</pre>
        </div>

        <div>
          <h3 className="flex items-center gap-2"><Code className="w-4 h-4" /> JavaScript</h3>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-sm overflow-x-auto">{`const API = "https://gotot.app/api";

async function getVideoInfo(url, token) {
  const resp = await fetch(\`\${API}/download/info\`, {
    method: "POST",
    headers: {
      "Authorization": \`Bearer \${token}\`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });
  return resp.json();
}`}</pre>
        </div>
      </div>
    ),
  },
  {
    id: "errors",
    icon: Shield,
    title: "Error Codes",
    content: (
      <div className="prose dark:prose-invert max-w-none">
        <table className="w-full text-sm">
          <thead><tr><th>Status</th><th>Code</th><th>Description</th></tr></thead>
          <tbody>
            <tr><td>400</td><td>INVALID_INPUT</td><td>Missing or invalid parameters</td></tr>
            <tr><td>401</td><td>UNAUTHORIZED</td><td>Missing or invalid authentication</td></tr>
            <tr><td>403</td><td>FORBIDDEN</td><td>Insufficient permissions or CSRF</td></tr>
            <tr><td>404</td><td>NOT_FOUND</td><td>Resource not found</td></tr>
            <tr><td>409</td><td>CONFLICT</td><td>Duplicate resource (e.g., email exists)</td></tr>
            <tr><td>422</td><td>VALIDATION_ERROR</td><td>Request body validation failed</td></tr>
            <tr><td>429</td><td>RATE_LIMITED</td><td>Too many requests</td></tr>
            <tr><td>500</td><td>SERVER_ERROR</td><td>Internal server error</td></tr>
          </tbody>
        </table>
      </div>
    ),
  },
];

export default function DocsPage() {
  return (
    <div className="pt-24 pb-16 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <BookOpen className="w-8 h-8 text-primary-500" />
          <h1 className="text-3xl font-bold">API Documentation</h1>
        </div>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          Integrate GoTot into your applications. All endpoints return JSON. Use Bearer tokens or API keys for authentication.
        </p>

        <nav className="flex gap-2 mb-8 overflow-x-auto pb-2 flex-wrap">
          {sections.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all whitespace-nowrap"
            >
              <s.icon className="w-3 h-3" />
              {s.title}
            </a>
          ))}
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-600 hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-all whitespace-nowrap"
          >
            <Key className="w-3 h-3" />
            Get API Key
          </Link>
        </nav>

        <div className="space-y-8">
          {sections.map((section, i) => (
            <motion.div
              key={section.id}
              id={section.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200/50 dark:border-gray-800/50 p-6 sm:p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 p-2">
                  <section.icon className="w-full h-full text-white" />
                </div>
                <h2 className="text-xl font-bold">{section.title}</h2>
              </div>
              {section.content}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
