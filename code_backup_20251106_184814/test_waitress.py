from waitress import serve
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
    <head><title>WHS App - Production Test</title></head>
    <body style="font-family: Arial; padding: 50px; text-align: center;">
        <h1 style="color: #2ecc71;">✓ Waitress läuft!</h1>
        <h2>WHS Test Application</h2>
        <p>Production Server ist bereit für Deployment</p>
        <hr>
        <p><small>Powered by Waitress WSGI Server</small></p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'OK', 'server': 'Waitress'}

if __name__ == '__main__':
    print('='*70)
    print('WHS App - Waitress Production Test')
    print('='*70)
    print('Server: Waitress WSGI Server')
    print('URL: http://localhost:5000')
    print('='*70)
    print('Drücke Ctrl+C zum Beenden...')
    print()
    
    serve(app, host='0.0.0.0', port=5000, threads=4)
