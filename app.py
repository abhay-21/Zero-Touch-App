import socket
from flask import Flask, render_template_string

app = Flask(__name__)

# This is the modern HTML/CSS template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zero-Touch Pipeline</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #ffffff;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
            text-align: center;
            max-width: 500px;
            width: 90%;
        }
        .status {
            display: inline-flex;
            align-items: center;
            background: rgba(46, 204, 113, 0.2);
            color: #2ecc71;
            padding: 8px 16px;
            border-radius: 50px;
            font-weight: 600;
            margin-bottom: 20px;
            border: 1px solid #2ecc71;
        }
        .pulse {
            width: 10px;
            height: 10px;
            background-color: #2ecc71;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7);
            animation: pulsing 1.5s infinite;
        }
        @keyframes pulsing {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
        }
        h1 { margin: 0 0 10px 0; font-size: 28px; }
        p { color: #cccccc; line-height: 1.6; }
        .container-id {
            margin-top: 30px;
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            color: #f1c40f;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="status">
            <div class="pulse"></div>
            SYSTEM ACTIVE
        </div>
        <h1>Zero-Touch Deployment</h1>
        <p>If you are seeing this page, the CI/CD pipeline is fully operational. Code changes pushed to GitHub are automatically built and deployed via Jenkins and Docker.</p>
        <div class="container-id">
            Docker Container ID:<br> 
            <span style="color: #fff; font-size: 20px;">{{ container_id }}</span>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # Automatically grabs the Docker Container ID
    container_id = socket.gethostname()
    return render_template_string(HTML_TEMPLATE, container_id=container_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)