# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# Backend
- Preserve backward compatibility: do not modify existing APIs, break existing functionality, or change unrelated code when implementing new features. Confidence: 0.85

# Download Formats
- Never hardcode video qualities; always fetch all available formats directly from the provider and use the exact format_id when downloading. Never substitute a user-selected format with "best" or any other format unless the selected format fails. Confidence: 0.85
- Return detailed metadata for every format from the provider (resolution, width, height, fps, codec, bitrate, filesize, extension, HDR). Never invent qualities that do not exist in the actual format list. Confidence: 0.80

# Error Handling
- Always log the complete Python traceback using logger.exception() or logger.error(..., exc_info=True); never use bare except that swallows the real exception. Confidence: 0.85
- Return descriptive, platform-aware error messages instead of generic failures (e.g., indicate if content is private, geo-restricted, or requires authentication). Confidence: 0.70

