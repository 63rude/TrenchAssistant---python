import time
import functools
import logging

# Optional: configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def retry(retries=3, delay=1.0, allowed_exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    attempt += 1
                    logging.warning(f"[retry] Attempt {attempt} failed: {e}")
                    time.sleep(delay)
            raise RuntimeError(f"[retry] All {retries} retries failed for {func.__name__}")
        return wrapper
    return decorator


def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"[log] Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"[log] {func.__name__} returned {result}")
        return result
    return wrapper


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.info(f"[timeit] {func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper
