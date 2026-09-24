import os
from flask import Flask, jsonify
import redis

app = Flask(__name__)

ALERT_THRESHOLD = 25


def alert_threshold():
    return ALERT_THRESHOLD


def sanitize_input(value):
    return value.replace("<", "&lt;").replace(">", "&gt;")


def get_redis_client():
    redis_host = os.getenv("REDIS_HOST", "redis")
    return redis.Redis(
        host=redis_host,
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=2
    )


@app.route("/health")
def health():
    try:
        r = get_redis_client()
        if r.ping():
            return jsonify(status="ok"), 200
        return jsonify(status="unhealthy"), 503
    except Exception:
        return jsonify(status="unhealthy"), 503


@app.route("/status")
def status():
    return jsonify(
        service="projet-devops-groupe-demo",
        version="1.0",
        deploy_color=os.getenv("DEPLOY_COLOR", "unknown"),
        commit_sha=os.getenv("COMMIT_SHA", "dev")
    ), 200


@app.route("/visits")
def visits():
    r = get_redis_client()
    count = r.incr("counter")
    return jsonify(visits=count), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)