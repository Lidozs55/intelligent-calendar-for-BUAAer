from flask import Flask
import os

# Create a Flask app instance
app = Flask(__name__)

# Print the instance path
print(f"Instance path: {app.instance_path}")
print(f"Does instance directory exist? {os.path.exists(app.instance_path)}")
print(f"Current working directory: {os.getcwd()}")
print(f"Absolute path to instance directory: {os.path.abspath(app.instance_path)}")

# Test if we can write to the instance directory
try:
    test_file = os.path.join(app.instance_path, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('test')
    print(f"Successfully wrote to {test_file}")
    os.remove(test_file)
    print(f"Successfully removed {test_file}")
except Exception as e:
    print(f"Error writing to instance directory: {e}")
