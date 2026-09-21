"""
Minimal per-IP throttling using Django's cache framework - no extra
dependency. Good enough to slow down scripted signup/login abuse; not a
replacement for a real WAF/rate-limiting layer if this ever gets serious
traffic, but that's not a now problem.
"""
from django.core.cache import cache
from django.http import HttpResponse


def get_client_ip(request):
    return request.META.get("REMOTE_ADDR")


def too_many_attempts(request, key_prefix, limit=10, window_seconds=600):
    """Return True (and record this attempt) if this IP has hit the limit."""
    ip = get_client_ip(request)
    cache_key = f"throttle:{key_prefix}:{ip}"
    attempts = cache.get(cache_key, 0)
    if attempts >= limit:
        return True
    cache.set(cache_key, attempts + 1, timeout=window_seconds)
    return False


def throttled_response():
    return HttpResponse("Too many attempts. Try again later.", status=429)
