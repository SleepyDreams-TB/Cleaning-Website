from slowapi import Limiter
from helpers import get_origin_ip

limiter = Limiter(key_func=get_origin_ip)