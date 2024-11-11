import os
import logging
from flask import Flask, render_template_string, request

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

LOG_FILES = {
    "/var/log/syslog": "System log",
    "/var/log/auth.log": "Authentication log",
    "/var/log/dmesg": "Kernel ring buffer",
    "/var/log/kern.log": "Kernel log",
    "/var/log/daemon.log": "Daemon log",
    "/var/log/user.log": "User log",
    "/var/log/Xorg.0.log": "Xorg log",
    "/var/log/faillog": "Failed login attempts",
    "/var/log/lastlog": "Last login log",
    "/var/log/boot.log": "Boot log",
    "/var/log/mysql/error.log": "MySQL error log",
    "/var/log/apache2/error.log": "Apache error log",
    "/var/log/apache2/access.log": "Apache access log",
}

@app.route('/')
def index():
    return render_template_string('''
    <html>
        <head>
            <title>Log Viewer</title>
        </head>
        <body>
            <h1>Log Viewer</h1>
            <ul>
                {% for path, description in log_files.items() %}
                    <li><a href="/view_log?path={{ path }}">{{ description }}</a></li>
                {% endfor %}
            </ul>
        </body>
    </html>
    ''', log_files=LOG_FILES)

@app.route('/view_log')
def view_log():
    path = request.args.get('path')
    if path in LOG_FILES:
        with open(path, 'r') as file:
            content = file.read()
        return render_template_string('''
        <html>
            <head>
                <title>Log Viewer</title>
            </head>
            <body>
                <h1>{{ description }}</h1>
                <pre>{{ content }}</pre>
                <a href="/">Back to list</a>
            </body>
        </html>
        ''', description=LOG_FILES[path], content=content)
    else:
        return "Log file not found", 404

def access_log(log_path, progress_callback):
    try:
        print(f"Accessing log file: {log_path}")
        progress_callback(50)
        with open(log_path, 'r') as file:
            content = file.read()
        progress_callback(100)
        print(f"Log file {log_path} accessed.")
        return content
    except Exception as e:
        print(f"Error accessing log file: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
