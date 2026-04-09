from waitress import serve
import sys
import os

# Working Directory setzen
os.chdir('C:\\inetpub\\whs_app')
sys.path.insert(0, 'C:\\inetpub\\whs_app')

# Import App
from app import app

if __name__ == '__main__':
    print('='*70)
    print('WHS App - Production Server')
    print('='*70)
    print('Starting on http://0.0.0.0:5000')
    print('='*70)
    
    serve(app, host='0.0.0.0', port=5000, threads=4)
