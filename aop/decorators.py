# decorators.py

import os
from functools import wraps

def proxy_switcher_decorator(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        original_http_proxy = os.environ.get("HTTP_PROXY", None)
        original_https_proxy = os.environ.get("HTTPS_PROXY", None)
        os.environ["HTTP_PROXY"] = ""
        os.environ["HTTPS_PROXY"] = ""
        try:
            result = method(*args, **kwargs)
            return result
        finally:
            if original_http_proxy is not None:
                os.environ["HTTP_PROXY"] = original_http_proxy
            else:
                del os.environ["HTTP_PROXY"]
                
            if original_https_proxy is not None:
                os.environ["HTTPS_PROXY"] = original_https_proxy
            else:
                del os.environ["HTTPS_PROXY"]
    return wrapper
