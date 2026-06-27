"""
Shared LLM instance with rate limiting.
All nodes import from here — one instance, one rate limiter.

Free tier limit for gemini-2.5-flash: ~20 requests/minute.
We cap at 8 RPM (one request every ~7.5s) to stay comfortably under.
When the pipeline makes back-to-back calls, the rate limiter
automatically sleeps the right amount — no 429s.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter

_rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.25,    # ~15 RPM, well under 1500 RPD free tier
    check_every_n_seconds=0.5,
    max_bucket_size=5,
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    max_retries=3,
    rate_limiter=_rate_limiter,
)
