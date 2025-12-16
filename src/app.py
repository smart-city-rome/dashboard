from flask.globals import request
from flask import Flask, jsonify, render_template, Response, stream_with_context
import redis
import json
import os
import time
import random
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = True

# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
REDIS_TOPIC = os.environ.get('REDIS_TOPIC', 'camera:skylinewebcams_largo_argentina')

TEST_MODE = True

def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )

import clickhouse_connect

# ClickHouse Configuration
CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT = int(os.environ.get('CLICKHOUSE_PORT', 8123))
CLICKHOUSE_USER = os.environ.get('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.environ.get('CLICKHOUSE_PASSWORD', '')

def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD
    )

@app.route('/')
def home():
    """Home page route."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running'
    })


@app.route('/api/status')
def api_status():
    """API status endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'Smart City Rome Dashboard',
        'version': '1.0.0'
    })

@app.route('/api/crossroads')
def get_crossroads():
    """Fetch all available crossroads."""
    if TEST_MODE:
        # Mock data
        return jsonify([
            {
                "id": "1", 
                "name": "Largo Argentina", 
                "lat": 41.8959, 
                "lon": 12.4767, 
                "bbox": [12.4755, 41.8955, 12.4779, 41.8965],
                "topic": "camera:skylinewebcams_largo_argentina"
            },
            {
                "id": "2", 
                "name": "Piazza Venezia", 
                "lat": 41.8955, 
                "lon": 12.4825, 
                "bbox": [12.4815, 41.8950, 12.4835, 41.8960],
                "topic": "camera:piazza_venezia"
            }
        ])
        
    try:
        client = get_clickhouse_client()
        result = client.query("SELECT id, name, latitude, longitude, redis_topic, min_lon, min_lat, max_lon, max_lat FROM crossroads") 
        crossroads = []
        for row in result.result_rows:
            crossroads.append({
                "id": str(row[0]),
                "name": row[1],
                "lat": row[2],
                "lon": row[3],
                "topic": row[4],
                "bbox": [row[5], row[6], row[7], row[8]] if row[5] is not None else None
            })
        return jsonify(crossroads)
    except Exception as e:
        print(f"ClickHouse Error: {e}")
        return jsonify([]), 500

@app.route('/api/crossroads/<id>/stats')
def get_crossroad_stats(id):
    """Fetch aggregated stats for a crossroad."""
    if TEST_MODE:
        return jsonify({
            "cards": [
                {"title": "Avg Speed", "value": f"{random.randint(20,40)} km/h", "type": "value"},
                {"title": "Traffic Volume", "value": f"{random.randint(100,500)} vehicles", "type": "value"},
                {"title": "Congestion", "value": "Moderate", "type": "string"}
            ]
        })

    try:
        client = get_clickhouse_client()
        query = """
            SELECT title, value, type
            FROM crossroads_stats
            WHERE id = '{id}' AND timestamp = (
                SELECT MAX(timestamp)
                FROM crossroads_stats
                WHERE id = '{id}'
            )
            ORDER BY title
        """.format(id=id)
        result = client.query(query)
        stats = []
        for row in result.result_rows:
            stats.append({
                "title": row[0],
                "value": row[1],
                "type": row[2]
            })
        return jsonify({"cards": stats})
    except Exception as e:
         print(f"ClickHouse Error: {e}")
         return jsonify({"error": str(e)}), 500

def generate_stream(topic):
    """Generates SSE events from Redis stream."""
    try:
        r = get_redis_client()
        # Test connection
        r.ping()
        last_id = '$'
        
        while True:
            try:
                # Real Redis Reading
                msgs = r.xread({topic: last_id}, block=1000)
                
                if not msgs:
                    yield ": keepalive\n\n"
                    continue

                for stream_name, events in msgs:
                    for msg_id, fields in events:
                        last_id = msg_id
                        payload_str = fields.get("payload")
                        if not payload_str: continue
                            
                        try:
                            payload = json.loads(payload_str)
                            coords = payload.get("coords", [])
                            ids = payload.get("ids", [])
                            classes = payload.get("classes", [])
                            velocities = payload.get("velocities", [])
                            
                            features = []
                            safe_count = min(len(ids), len(classes), len(coords))
                            
                            for i in range(safe_count):
                                try:
                                    lat = float(coords[i][0])
                                    lon = float(coords[i][1])
                                    obj_id = str(ids[i])
                                    obj_class = classes[i]
                                    speed = 0
                                    if i < len(velocities) and isinstance(velocities[i], list) and len(velocities[i]) >= 1:
                                        speed = velocities[i][0]

                                    features.append({
                                        "type": "Feature",
                                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                                        "properties": {"id": obj_id, "class": obj_class, "score": 1.0, "speed": speed}
                                    })
                                except (ValueError, IndexError, TypeError):
                                    continue
                            
                            if features:
                                yield f"data: {json.dumps({'type': 'FeatureCollection', 'features': features})}\n\n"
                                
                        except json.JSONDecodeError:
                            continue
                            
            except redis.exceptions.ConnectionError:
                yield "event: error\ndata: Redis Connection Error\n\n"
                time.sleep(5)
                r = get_redis_client()

    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"

@app.route('/api/stream')
def stream():
    """SSE endpoint for tracklets."""
    topic = request.args.get('topic', REDIS_TOPIC)
    return Response(stream_with_context(generate_stream(topic)), mimetype='text/event-stream')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal error occurred'
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
