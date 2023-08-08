from flask import Flask
from flask_caching import Cache

__all__ = ['cache', 'initialize_cache']

cache = Cache()

def initialize_cache(app: Flask) -> None:
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    return None