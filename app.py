from flask import Flask, request, redirect, url_for, session, render_template_string
import subprocess
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

messages = []
wifi_ssids = []

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.txt')

def run_command(command):
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return result.decode(), None
    except subprocess.CalledProcessError as e:
        error_message = f"Command '{' '.join(command)}' failed with error: {e.output.decode()}"
        print(error_message)
        return None, error_message

def get_wifi_networks():
    command = ["nmcli", "--colors", "no", "-m", "multiline", "--get-value", "SSID", "dev", "wifi", "list"]
    result, error = run_command(command)
    if result:
        ssids_list = result.split('\n')
        ssids = list(set([ssid.removeprefix("SSID:") for ssid in ssids_list if len(ssid.removeprefix("SSID:")) > 0]))
        return ssids
    return []

def get_known_networks():
    command = ["nmcli", "-t", "-f", "NAME", "connection", "show"]
    result, error = run_command(command)
    if result:
        known_list = result.split('\n')
        known_networks = [net for net in known_list if net]
        return known_networks
    return []

def get_active_connections():
    command = ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"]
    result, error = run_command(command)
    if result:
        active_list = result.split('\n')
        active_connections = [conn.split(':') for conn in active_list if conn]
        print(f"Active connections: {active_connections}")  # Debug output
        return active_connections
    return []

def get_ip_address(interface):
    command = ["ip", "addr", "show", interface]
    result, error = run_command(command)
    if result:
        for line in result.split('\n'):
            if 'inet ' in line:
                ip_address = line.strip().split()[1].split('/')[0]  # Extracting the IP address
                return ip_address
    return "N/A"

def check_authentication(username, password):
    # Read credentials from a file
    try:
        with open(CREDENTIALS_PATH, 'r') as file:
            stored_username, stored_password_hash = file.read().strip().split(',')
            password_hash = hashlib.md5(password.encode()).hexdigest()
            return username == stored_username and password_hash == stored_password_hash
    except FileNotFoundError:
        print(f"Credentials file not found: {CREDENTIALS_PATH}")
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_authentication(username, password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template_string(login_page, error="Invalid credentials")
    return render_template_string(login_page)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    global messages, wifi_ssids
    wifi_ssids = get_wifi_networks()
    known_networks = get_known_networks()
    active_connections = get_active_connections()

    dropdowndisplay = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WiFi Control</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    padding: 20px;
                    max-width: 600px;
                    margin: auto;
                    background-color: #fff;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    border-radius: 10px;
                    margin-top: 20px;
                }
                h1, h2 {
                    color: #333;
                    text-align: center;
                }
                form {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 8px;
                    color: #555;
                }
                select, input[type="password"], input[type="submit"], button {
                    padding: 10px;
                    margin-bottom: 10px;
                    width: 100%;
                    max-width: 100%;
                    box-sizing: border-box;
                    border-radius: 5px;
                    border: 1px solid #ccc;
                    font-size: 16px;
                }
                input[type="submit"], button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                }
                input[type="submit"]:hover, button:hover {
                    background-color: #45a049;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                }
                li {
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                }
                .message {
                    padding: 10px;
                    background-color: #f9f9f9;
                    border-left: 6px solid #4CAF50;
                    margin-bottom: 10px;
                    word-break: break-word;
                    border-radius: 5px;
                }
                .message.error {
                    border-left-color: #f44336;
                }
                .small-btn {
                    padding: 10px;
                    font-size: 16px;
                }
                .icon-btn {
                    background: none;
                    border: none;
                    color: red;
                    cursor: pointer;
                    font-size: 18px;
                    margin-right: 10px;
                }
                .icon-btn:hover {
                    color: darkred;
                }
                .refresh-btn {
                    background: none;
                    border: none;
                    color: #008CBA;
                    cursor: pointer;
                    font-size: 24px;
                    margin-left: 10px;
                }
                .refresh-btn:hover {
                    color: #007bb5;
                }
                .refresh-container {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                .action-buttons {
                    display: flex;
                    justify-content: space-between;
                    gap: 20px;
                    margin-top: 30px;
                }
                .action-button {
                    width: 100%;
                    background-color: #FF5722;
                    color: white;
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                    text-align: center;
                }
                .action-button:hover {
                    background-color: #E64A19;
                }
                @media (max-width: 600px) {
                    .refresh-container {
                        flex-direction: row;
                        justify-content: flex-start;
                    }
                    .refresh-container label {
                        margin-right: 10px;
                    }
                    .refresh-btn {
                        margin-left: 0;
                    }
                    .action-buttons {
                        flex-direction: column;
                    }
                    .action-button {
                        width: 100%;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>WiFi Control</h1>
                <form action="/submit" method="post">
                    <div class="refresh-container">
                        <label for="ssid">Choose a WiFi network:</label>
                        <button type="submit" form="refresh-form" class="refresh-btn"><i class="fas fa-sync-alt"></i></button>
                    </div>
                    <select name="ssid" id="ssid">
    """
    for ssid in wifi_ssids:
        dropdowndisplay += f"""
                        <option value="{ssid}">{ssid}</option>
        """
    
    dropdowndisplay += """
                    </select>
                    <label for="password">Password:</label>
                    <input type="password" name="password"/>
                    <label for="known_ssid">Or connect to a known network:</label>
                    <select name="known_ssid" id="known_ssid">
                        <option value="">Select a known network</option>
    """
    
    for known in known_networks:
        dropdowndisplay += f"""
                        <option value="{known}">{known}</option>
        """
    
    dropdowndisplay += """
                    </select>
                    <input type="submit" class="small-btn" value="Connect">
                </form>
                <form id="refresh-form" action="/refresh" method="post" style="display:none;">
                </form>
                <h2>Active Connections</h2>
                <ul>
    """
    
    for conn in active_connections:
        name, conn_type, device = conn
        ip_address = get_ip_address(device)
        if conn_type == '802-11-wireless':  # Display WiFi connections
            dropdowndisplay += f"""
                    <li>
                        <form action="/disconnect" method="post" style="display:inline;">
                            <input type="hidden" name="connection" value="{name}">
                            <button type="submit" class="icon-btn"><i class="fas fa-times-circle"></i></button>
                        </form>
                        {name} ({device}) - IP: {ip_address}
                    </li>
            """
        elif conn_type == 'vpn':  # Display VPN connections
            dropdowndisplay += f"""
                    <li>
                        <form action="/disconnect" method="post" style="display:inline;">
                            <input type="hidden" name="connection" value="{name}">
                            <button type="submit" class="icon-btn"><i class="fas fa-times-circle"></i></button>
                        </form>
                        {name} (VPN) - IP: {ip_address}
                    </li>
            """
        elif conn_type == '802-3-ethernet':  # Display Ethernet connections
            dropdowndisplay += f"""
                    <li>
                        <form action="/disconnect" method="post" style="display:inline;">
                            <input type="hidden" name="connection" value="{name}">
                            <button type="submit" class="icon-btn"><i class="fas fa-times-circle"></i></button>
                        </form>
                        {name} ({device}) - IP: {ip_address}
                    </li>
            """
    
    dropdowndisplay += """
                </ul>
                <h2>Logging</h2>
                <ul>
    """
    
    for message in messages:
        message_class = "message"
        if "Error" in message:
            message_class += " error"
        dropdowndisplay += f"<li class='{message_class}'>{message}</li>"
    
    dropdowndisplay += """
                </ul>
                <div class="action-buttons">
                    <form action="/reboot" method="post" style="display:inline;">
                        <button type="submit" class="action-button">Reboot</button>
                    </form>
                    <form action="/shutdown" method="post" style="display:inline;">
                        <button type="submit" class="action-button">Shutdown</button>
                    </form>
                    <form action="/logout" method="post" style="display:inline;">
                        <button type="submit" class="action-button">Logout</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
    """
    messages = []
    return dropdowndisplay

login_page = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-container {
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            width: 90%;
            max-width: 400px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        form {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            text-align: left;
        }
        input[type="text"], input[type="password"] {
            padding: 10px;
            margin-bottom: 10px;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 16px;
        }
        input[type="submit"] {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 16px;
            padding: 10px;
            width: 100%;
            border-radius: 5px;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
        .error {
            color: #f44336;
            margin-bottom: 10px;
        }
        @media (max-width: 600px) {
            .login-container {
                width: 90%;
                padding: 15px;
            }
            input[type="text"], input[type="password"], input[type="submit"] {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>Login</h1>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <label for="username">Username:</label>
            <input type="text" name="username" id="username" required>
            <label for="password">Password:</label>
            <input type="password" name="password" id="password" required>
            <input type="submit" value="Login">
        </form>
    </div>
</body>
</html>
"""

@app.route('/submit', methods=['POST'])
def submit():
    global messages
    ssid = request.form.get('ssid')
    password = request.form.get('password')
    known_ssid = request.form.get('known_ssid')
    
    if known_ssid and known_ssid != "":
        connection_command = ["nmcli", "--colors", "no", "connection", "up", known_ssid]
    elif ssid and ssid != "":
        connection_command = ["nmcli", "--colors", "no", "device", "wifi", "connect", ssid]
        if password and password != "":
            connection_command += ["password", f'"{password}"']
    else:
        messages.append("Error: No SSID or known network selected.")
        return redirect(url_for('index'))

    result, error = run_command(connection_command)
    if result:
        messages.append(f"Success: {result}")
    if error:
        messages.append(f"Error: {error}")

    return redirect(url_for('index'))


@app.route('/refresh', methods=['POST'])
def refresh():
    global wifi_ssids
    wifi_ssids = get_wifi_networks()
    messages.append("WiFi networks refreshed.")
    return redirect(url_for('index'))


@app.route('/disconnect', methods=['POST'])
def disconnect():
    global messages
    connection = request.form['connection']
    
    disconnect_command = ["nmcli", "--colors", "no", "connection", "down", connection]

    result, error = run_command(disconnect_command)
    if result:
        messages.append(f"Success: {result}")
    if error:
        messages.append(f"Error: {error}")

    return redirect(url_for('index'))

@app.route('/reboot', methods=['POST'])
def reboot():
    run_command(['sudo', 'reboot'])
    return redirect(url_for('index'))

@app.route('/shutdown', methods=['POST'])
def shutdown():
    run_command(['sudo', 'shutdown', '-h', 'now'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    wifi_ssids = get_wifi_networks()
    app.run(debug=True, host='0.0.0.0', port=80)
