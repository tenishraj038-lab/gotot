# GoTot Production Readiness Checklist

## Legal & Compliance
- [x] Terms of Service page
- [x] Privacy Policy page
- [x] Copyright Policy page
- [x] DMCA/Takedown page
- [x] Disclaimer: users must own content or have permission
- [x] Users must accept Terms before downloading
- [x] Cookie-based Terms acceptance tracking

## Security
- [x] All request inputs validated (Pydantic models)
- [x] Path traversal prevention (os.path.realpath + prefix check)
- [x] Filename sanitization (special chars, length limits, empty fallback)
- [x] Command injection prevention (no shell=True, subprocess args)
- [x] Secure random download IDs (secrets.token_urlsafe)
- [x] CORS with configurable origins
- [x] Rate limiting via slowapi (Redis-backed)
- [x] Request size limits (configurable, 10MB default)
- [x] Security headers (CSP, HSTS, X-Frame-Options, etc.)
- [x] CSRF protection (hmac.compare_digest, cookie+header)
- [x] Configurable CSRF cookie settings
- [x] Error IDs returned instead of stack traces
- [x] Prometheus metrics (requests, latency, downloads, uptime)

## Downloads
- [x] Files saved in configurable temporary directory
- [x] Unique filenames (yt-dlp handles via hash)
- [x] Auto-delete expired files (configurable retention)
- [x] Server filesystem paths never exposed
- [x] File existence verified before serving
- [x] File readability verified before serving
- [x] File size checked before serving
- [x] Proper Content-Disposition headers
- [x] MIME type detection (extended list)

## API Error Handling
- [x] Download ID validated
- [x] FileNotFoundError → 404
- [x] PermissionError → 403
- [x] Path traversal → 403
- [x] Expired download → 410
- [x] Descriptive JSON errors (no generic 500s)
- [x] Queue failure handling
- [x] Database lookup failures gracefully handled

## Background Jobs
- [x] Status tracking: queued, downloading, processing, completed, failed
- [x] Failure reason stored
- [x] Retry on transient failures (3 retries, exponential backoff)
- [x] WebSocket progress via Redis Pub/Sub
- [x] Batch download tracking

## Logging
- [x] Structured JSON logging (timestamp, level, logger, message)
- [x] Download analyze requests logged
- [x] Download requests logged
- [x] Download completions logged
- [x] Download failures logged with error details
- [x] Cleanup jobs logged
- [x] Exceptions logged with request IDs
- [x] No internal stack traces in user responses

## Monitoring
- [x] Health endpoint (/health) with DB status + latency
- [x] Readiness endpoint (/health/readiness) with multi-check
- [x] Metrics endpoint (/metrics) with Prometheus
- [x] Metadata endpoint (/meta)
- [x] Sentry integration for error monitoring
- [x] Slow request warnings (>5s)

## Cleanup
- [x] Automatic expired file removal
- [x] Orphaned .part/.ytdl/.tmp file cleanup
- [x] Failed temporary file cleanup
- [x] Configurable cleanup schedule
- [x] Temp directory cleanup

## Configuration
- [x] All settings via environment variables
- [x] .env.example with documentation
- [x] Download directory configurable
- [x] Temp directory configurable
- [x] Max file size configurable
- [x] Allowed domains configurable
- [x] Rate limits configurable
- [x] Cleanup interval configurable
- [x] Log level configurable

## Testing
- [x] Platform detection tests (all 11 platforms)
- [x] URL validation tests (valid, invalid, empty, too long)
- [x] Domain whitelist tests
- [x] Filename sanitization tests (special chars, traversal)
- [x] Download info endpoint tests
- [x] Invalid URL rejection tests
- [x] Unsupported domain rejection tests
- [x] File missing tests
- [x] Download failed tests
- [x] Queue endpoint tests
- [x] Health endpoint tests
- [x] Readiness endpoint tests
- [x] Metadata endpoint tests
- [x] Terms acceptance tests
- [x] Contact validation tests
