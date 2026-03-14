#!/usr/bin/env python3
"""
MONTFORT SENIOR SECONDARY SCHOOL Management System
Setup and Run Script
"""
import subprocess
import sys
import os

def setup():
    print("=" * 60)
    print("  MONTFORT SENIOR SECONDARY SCHOOL")
    print("  Setup & Installation")
    print("=" * 60)

    # Install requirements
    print("\n📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # Initialize data
    print("\n🗄️  Initializing database...")
    sys.path.insert(0, os.path.dirname(__file__))
    from utils.excel_helper import init_data
    init_data()

    print("\n✅ Setup complete!")
    print("\n" + "=" * 60)
    print("  DEFAULT LOGIN CREDENTIALS")
    print("=" * 60)
    print("  Admin   : username=admin      password=admin123")
    print("  Teacher : username=teacher1   password=teacher123")
    print("  Student : username=student1   password=student123")
    print("  Parent  : username=parent1    password=parent123")
    print("=" * 60)
    print("\n🚀 Starting server at http://localhost:8080")
    print("   Press CTRL+C to stop\n")

    # Run app
    from app import app
    app.run(debug=True, port=8080, host='0.0.0.0')

if __name__ == "__main__":
    setup()
