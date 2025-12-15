from flask import Flask, jsonify

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = True


@app.route('/')
def home():
    """Home page route."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Smart City Rome</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
            }
            .endpoint {
                background-color: #f0f0f0;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Smart City Rome Dashboard</h1>
            <p>This is a basic Flask web application server.</p>
            <h2>Available Endpoints:</h2>
            <div class="endpoint">GET / - This home page</div>
            <div class="endpoint">GET /health - Health check endpoint</div>
            <div class="endpoint">GET /api/status - API status endpoint</div>
        </div>
    </body>
    </html>
    """


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
