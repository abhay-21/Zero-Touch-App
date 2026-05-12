from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def home():
    # This grabs the ID of the Docker container
    container_id = socket.gethostname()
    return f"""
    <h1>Zero-Touch Deployment Pipeline is ACTIVE! 🚀</h1>
    <p>If you are seeing this, Jenkins successfully built and deployed the code.</p>
    <p><b>Running inside Docker Container ID:</b> {container_id}</p>
    <p><b>Testing GitHub Webhook automation 🥀</b></p>
    """

if __name__ == '__main__':
    # Running on port 5000
    app.run(host='0.0.0.0', port=5000)