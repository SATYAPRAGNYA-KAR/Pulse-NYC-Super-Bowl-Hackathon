"""
Minimal Flask test - if this doesn't work, Flask isn't running properly
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
        <head><title>Flask Test</title></head>
        <body>
            <h1>✅ Flask is Working!</h1>
            <p>If you see this, Flask is running correctly.</p>
            <p>Server time: <script>document.write(new Date())</script></p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 MINIMAL FLASK TEST")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("If you see this in your terminal, Flask is starting...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)