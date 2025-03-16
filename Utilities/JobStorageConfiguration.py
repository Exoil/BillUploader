import redis

# Initialize Redis (like Hangfire.Redis.StackExchange)
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)