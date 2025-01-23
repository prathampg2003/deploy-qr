from flask import Flask, request, render_template_string
import qrcode
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)


form_data = []
allocations = {}


SMTP_SERVER = 'smtp-relay.sendinblue.com'
SMTP_PORT = 587
SMTP_USER = 'prathampg2003@gmail.com'
SMTP_PASS = 'aQbv7CZdDrckyxw8'


FORM_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Form</title>
</head>
<body>
    <h1>Fill the Form</h1>
    <form action="/submit" method="post">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name" required><br><br>
        <label for="email">Email:</label><br>
        <input type="email" id="email" name="email" required><br><br>
        <label for="phone">Phone Number:</label><br>
        <input type="text" id="phone" name="phone" required><br><br>
        <label for="language">Preferred Language:</label><br>
        <select id="language" name="language" required>
            <option value="English">English</option>
            <option value="Hindi">Hindi</option>
            <option value="Marathi">Marathi</option>
            <option value="Punjabi">Punjabi</option>
            <option value="Other">Other (specify below)</option>
        </select><br><br>
        <label for="other_language">If Other, specify:</label><br>
        <input type="text" id="other_language" name="other_language"><br><br>
        <label for="date">Date:</label><br>
        <input type="date" id="date" name="date" required><br><br>
        <label for="time">Time:</label><br>
        <input type="time" id="time" name="time" required><br><br>
        <button type="submit">Submit</button>
    </form>
</body>
</html>
'''

WELCOME_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Welcome</title>
</head>
<body>
    <h1>Welcome, {{ name }}!</h1>
    <p>Your form has been submitted successfully.</p>
</body>
</html>
'''

INVALID_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
</head>
<body>
    <h1>Invalid QR Code</h1>
    <p>The form associated with this QR code does not exist.</p>
</body>
</html>
'''

ALLOCATE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Allocation Manager</title>
</head>
<body>
    <h1>Assign Sales Manager</h1>
    {% for user in users %}
        <p>
            <strong>ID:</strong> {{ user['id'] }}<br>
            <strong>Name:</strong> {{ user['name'] }}<br>
            <strong>Email:</strong> {{ user['email'] }}<br>
            <strong>Phone:</strong> {{ user['phone'] }}<br>
            <strong>Preferred Language:</strong> {{ user['language'] }}<br>
            <strong>Date of Visit:</strong> {{ user['date'] }}<br>
            <strong>Time of Visit:</strong> {{ user['time'] }}<br>
        </p>
        <form action="/assign" method="post" style="display:inline;">
            <input type="hidden" name="user_id" value="{{ user['id'] }}">
            <label for="manager">Manager:</label>
            <input type="text" name="manager" required>
            <button type="submit">Assign</button>
        </form>
        <hr>
    {% endfor %}
</body>
</html>
'''


def send_email(to_address, subject, body, qr_image, filename="qr-code.jpeg"):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_address
    msg['Subject'] = subject

    
    msg.attach(MIMEText(body, 'plain'))

    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(qr_image)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={filename}')
    msg.attach(part)

    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_address, msg.as_string())
        server.quit()
        print(f"Email sent to {to_address} successfully.")
    except Exception as e:
        print(f"Error sending email to {to_address}: {e}")

@app.route('/')
def index():
    return FORM_HTML

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    language = request.form['language']
    other_language = request.form.get('other_language', '').strip()
    date = request.form['date']
    time = request.form['time']
    
    if language == "Other" and other_language:
        language = other_language
    elif language == "Other":
        language = "Unspecified"

    user_id = len(form_data) + 1 

    
    form_data.append({'id': user_id, 'name': name, 'email': email, 'phone': phone, 'language': language, 'date': date, 'time': time})

    
    server_url = request.host_url.strip('/')
    qr_code_data = f"{server_url}/verify/{user_id}"
    qr = qrcode.make(qr_code_data)
    buffered = io.BytesIO()
    qr.save(buffered, format="JPEG")
    qr_image = buffered.getvalue()

    
    email_subject = 'QR Code for Vist'
    email_body = f"Hello {name},\n\nThank you for submitting the form! Please find your QR code attached."
    send_email(email, email_subject, email_body, qr_image)

   
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>QR Code Sent</title>
    </head>
    <body>
        <h1>Form Submitted Successfully!</h1>
        <p>Your QR code has been sent to your email address. Please check your inbox.</p>
        <p><a href="/">Go back to the form</a></p>
    </body>
    </html>
    '''

@app.route('/verify/<int:user_id>')
def verify(user_id):
    user = next((entry for entry in form_data if entry['id'] == user_id), None)

    if user:
        manager = allocations.get(user_id)
        if manager:
           
            print(f"Notification to {manager}: {user['name']} ({user['email']}, {user['phone']}, Preferred Language: {user['language']}) has arrived.")
        return render_template_string(WELCOME_HTML, name=user['name'])
    else:
        return INVALID_HTML

@app.route('/allocation_manager')
def allocation_manager():
    unassigned_users = [user for user in form_data if user['id'] not in allocations]
    return render_template_string(ALLOCATE_HTML, users=unassigned_users)

@app.route('/assign', methods=['POST'])
def assign():
    user_id = int(request.form['user_id'])
    manager = request.form['manager']
    allocations[user_id] = manager
    print(f"User {user_id} assigned to manager {manager}.")
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Assignment Success</title>
    </head>
    <body>
        <h1>Manager Assigned Successfully!</h1>
        <p>User ID <strong>{user_id}</strong> has been assigned to Manager <strong>{manager}</strong>.</p>
        <p><a href="/allocation_manager">Go back to Allocation Manager</a></p>
    </body>
    </html>
    '''


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
