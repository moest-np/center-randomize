from flask import Flask, send_from_directory
import os

app = Flask(__name__)

PORT = int(os.getenv('PORT',8005))

# Route to serve the index.html file from the 'static' directory
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Route to serve static files (e.g., CSS, JavaScript, images)
@app.route('/generated-pdfs/<path:filename>')
def static_files(filename):
    return send_from_directory('generated-pdfs', filename)


if __name__ == "__main__":
    app.run(port=PORT,debug=True)

#Todo: Gracefully shutdown the server when the tab is closed