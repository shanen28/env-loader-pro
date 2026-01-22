"""FastAPI integration for dependency injection."""

from typing import Any, Callable, Dict, Optional, Type
from functools import lru_cache

try:
    from fastapi import Depends
except ImportError:
    Depends = None


def config_dependency(
    schema: Optional[Type] = None,
    path: str = ".env",
    env: Optional[str] = None,
    **load_env_kwargs
):
    """Create a FastAPI dependency for configuration.
    
    Usage:
        from env_loader_pro.integrations.fastapi import config_dependency
        from fastapi import FastAPI, Depends
        
        app = FastAPI()
        
        @app.get("/config")
        def get_config(config = Depends(config_dependency())):
            return config
        
        # With schema:
        @app.get("/typed-config")
        def get_typed_config(config = Depends(config_dependency(ConfigSchema))):
            return config.port
    """
    if Depends is None:
        raise ImportError("FastAPI is required. Install with: pip install fastapi")
    
    from ..core.loader import load_env
    from ..schema import load_with_schema
    
    @lru_cache()
    def get_config():
        if schema:
            return load_with_schema(schema, path=path, env=env, **load_env_kwargs)
        else:
            return load_env(path=path, env=env, **load_env_kwargs)
    
    return Depends(get_config)


def inject_config(
    config_name: str = "config",
    schema: Optional[Type] = None,
    path: str = ".env",
    env: Optional[str] = None,
    **load_env_kwargs
):
    """Decorator to inject configuration into function.
    
    Usage:
        from env_loader_pro.integrations.fastapi import inject_config
        
        @inject_config("db_config")
        def connect_database(db_config):
            return create_connection(db_config)
    """
    def decorator(func: Callable):
        from ..loader import load_env
        from ..schema import load_with_schema
        
        @lru_cache()
        def load_cached_config():
            if schema:
                return load_with_schema(schema, path=path, env=env, **load_env_kwargs)
            else:
                return load_env(path=path, env=env, **load_env_kwargs)
        
        def wrapper(*args, **kwargs):
            config = load_cached_config()
            kwargs[config_name] = config
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator

