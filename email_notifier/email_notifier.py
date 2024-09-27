import smtplib
from email.message import EmailMessage


FROM = "testcompletionnotifier@gmail.com"
PASSWORD = "qwnl vjwr inil ywbf"
SUCCESS = "matthewdeanlarkins+test_complete@gmail.com"
ERROR = "matthewdeanlarkins+test_error@gmail.com"


def notify_success(test_name: str):
    msg = EmailMessage()
    msg["Subject"] = f"{test_name} Test Completed"
    msg["From"] = FROM
    msg["To"] = SUCCESS
    msg.set_content("Test Successfully Completed")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.ehlo()
        smtp.login(FROM, PASSWORD)
        smtp.send_message(msg)


def notify_error(test_name: str, traceback: str):
    msg = EmailMessage()
    msg["Subject"] = f"ERROR: {test_name} Test Failed!!!"
    msg["From"] = FROM
    msg["To"] = ERROR
    msg.set_content(traceback)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.ehlo()
        smtp.login(FROM, PASSWORD)
        smtp.send_message(msg)


if __name__ == '__main__':
    notify_success("Debugging")
