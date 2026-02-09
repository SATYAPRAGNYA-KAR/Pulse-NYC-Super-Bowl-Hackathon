"""
Debug Checklist - Run this to identify the problem
"""

import subprocess
import sys
import socket

print("=" * 70)
print("🔍 LOCALHOST:5000 NOT WORKING - DEBUG CHECKLIST")
print("=" * 70)

# 1. Check if Flask is installed
print("\n1️⃣  Checking Flask Installation...")
try:
    import flask
    print(f"   ✅ Flask is installed (version {flask.__version__})")
except ImportError:
    print("   ❌ Flask is NOT installed!")
    print("   FIX: pip install flask")
    sys.exit(1)

# 2. Check if port 5000 is available
print("\n2️⃣  Checking if port 5000 is available...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 5000))
sock.close()

if result == 0:
    print("   ⚠️  Port 5000 is ALREADY IN USE!")
    print("   This could mean:")
    print("   a) Flask server is already running (check terminal)")
    print("   b) Another application is using port 5000")
    print("   c) Previous Flask process didn't close properly")
    print("\n   FIX OPTIONS:")
    print("   - Find and kill the process: lsof -ti:5000 | xargs kill -9")
    print("   - Use a different port: Change port=5000 to port=5001")
else:
    print("   ✅ Port 5000 is available")

# 3. Check Python version
print("\n3️⃣  Checking Python Version...")
version = sys.version_info
print(f"   Python {version.major}.{version.minor}.{version.micro}")
if version.major < 3 or (version.major == 3 and version.minor < 7):
    print("   ⚠️  Python 3.7+ recommended")

# 4. Test if we can create a simple Flask app
print("\n4️⃣  Testing Flask App Creation...")
try:
    from flask import Flask
    test_app = Flask(__name__)
    
    @test_app.route('/')
    def test():
        return 'test'
    
    print("   ✅ Flask app can be created")
except Exception as e:
    print(f"   ❌ Error creating Flask app: {e}")

# 5. Check current directory
print("\n5️⃣  Checking Current Directory...")
import os
cwd = os.getcwd()
print(f"   Current directory: {cwd}")

files_present = []
required_files = ['app_fixed.py', 'index.html', 'app_fixed.js', 'styles.css']
for file in required_files:
    if os.path.exists(file):
        files_present.append(file)
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} - NOT FOUND")

if not files_present:
    print("\n   ⚠️  You might be in the wrong directory!")
    print("   Navigate to your project directory before running the server")

# 6. Instructions
print("\n" + "=" * 70)
print("📋 NEXT STEPS")
print("=" * 70)

if result == 0:
    print("\n⚠️  Port 5000 is in use. Two options:\n")
    print("OPTION A - Kill existing process:")
    print("  1. Find process: lsof -i:5000")
    print("  2. Kill it: kill -9 <PID>")
    print("  3. Or: lsof -ti:5000 | xargs kill -9")
    print("\nOPTION B - Use different port:")
    print("  1. Edit app_fixed.py")
    print("  2. Change: app.run(debug=True, host='0.0.0.0', port=5000)")
    print("  3. To:     app.run(debug=True, host='0.0.0.0', port=5001)")
    print("  4. Open: http://localhost:5001")
else:
    print("\n✅ Port is available! Try these steps:\n")
    print("1. Make sure you're in the correct directory (where app_fixed.py is)")
    print("2. Start the server:")
    print("   python app_fixed.py")
    print("\n3. Look for this output in terminal:")
    print("   * Running on http://0.0.0.0:5000")
    print("\n4. Open browser and go to:")
    print("   http://localhost:5000")
    print("\n5. If browser shows nothing:")
    print("   - Check terminal for errors")
    print("   - Try http://127.0.0.1:5000")
    print("   - Check browser console (F12)")

print("\n" + "=" * 70)
print("COMMON ISSUES")
print("=" * 70)
print("""
❌ "This site can't be reached"
   → Flask server is not running. Start it with: python app_fixed.py

❌ "Connection refused"
   → Server isn't started OR firewall blocking

❌ Blank white page
   → Server running but files not being served correctly
   → Check terminal for errors
   → Try the minimal test: python test_flask.py

❌ "Address already in use"
   → Port 5000 is taken
   → Kill process or use different port
""")

print("=" * 70)