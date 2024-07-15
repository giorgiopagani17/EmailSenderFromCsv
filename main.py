from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import base64

load_dotenv()

app = FastAPI()

templates = Jinja2Templates(directory="templates")
env = Environment(loader=FileSystemLoader('templates'))

dati = []

SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = "NOME AZIENDA " + "<" + EMAIL_ADDRESS + ">"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        return f"Email inviata a {to_email} con successo!"
    except Exception as e:
        return f"Errore nell'invio dell'email a {to_email}: {e}"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/upload/", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    global dati
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Il file deve essere di tipo CSV")

    contents = await file.read()
    stream = io.StringIO(contents.decode("UTF-8"))
    csv_input = csv.reader(stream, delimiter=';') 
    dati = [row for row in csv_input]

    return templates.TemplateResponse("data.html", {"request": request, "data": dati})

@app.post("/sendcredential/", response_class=HTMLResponse)
async def send_credentials(request: Request):
    global dati
    form_data = await request.form()
    
    messages = []

    ssid = form_data.get(f"ssid")
    company = form_data.get(f"compagnia")

        
    for row in dati:
        if row and len(row) >= 4: 
            email = row[2]
            subject = "Credenziali di rete " + company
            body_content = {
                'username': row[0],
                'password': row[1],
                'name': row[3],
                'ssid': ssid,
            }

            template = env.get_template('email.html')
            email_body = template.render(body=body_content)

            result_message = send_email(email, subject, email_body)
            messages.append(result_message)

    dati = []

    return templates.TemplateResponse("result.html", {"request": request, "messages": messages})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)