import os
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email_with_report(to_email: str, report_path: str, session_data: dict) -> None:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        raise ValueError(
            "SMTP_USER and SMTP_PASSWORD must be set in your .env file. "
            "For Gmail, use an App Password."
        )

    results = session_data.get("results", [])
    total_defects = sum(
        len(r.get("analysis", {}).get("defects", [])) for r in results
    )
    major = sum(
        1
        for r in results
        for d in r.get("analysis", {}).get("defects", [])
        if d.get("severity", "").lower() == "major"
    )
    moderate = sum(
        1
        for r in results
        for d in r.get("analysis", {}).get("defects", [])
        if d.get("severity", "").lower() == "moderate"
    )

    owner = session_data.get("owner_name") or "Property Owner"
    address = session_data.get("property_address", "N/A")
    unit = session_data.get("unit_number", "")
    unit_str = f" #{unit}" if unit else ""
    agent = session_data.get("agent_name", "N/A")
    insp_date = session_data.get("inspection_date", "N/A")

    subject = f"Property Defect Inspection Report – {address}{unit_str}"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; color: #111827; background: #f3f4f6; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background: #1B3A6B; color: white; padding: 28px 30px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 20px; }}
    .header p {{ margin: 6px 0 0; font-size: 12px; color: #DBEAFE; }}
    .body {{ padding: 28px 30px; }}
    .greeting {{ font-size: 15px; margin-bottom: 16px; }}
    .info-table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    .info-table td {{ padding: 8px 12px; border: 1px solid #E5E7EB; font-size: 13px; }}
    .info-table td:first-child {{ background: #EFF6FF; font-weight: bold; color: #1B3A6B; width: 40%; }}
    .stats {{ display: flex; gap: 10px; margin: 20px 0; }}
    .stat {{ flex: 1; text-align: center; padding: 14px; border-radius: 6px; }}
    .stat .num {{ font-size: 28px; font-weight: bold; }}
    .stat .lbl {{ font-size: 11px; margin-top: 4px; }}
    .stat-total {{ background: #1B3A6B; color: white; }}
    .stat-major {{ background: #DC2626; color: white; }}
    .stat-moderate {{ background: #D97706; color: white; }}
    .stat-minor {{ background: #16A34A; color: white; }}
    .disclaimer {{ background: #FFF7ED; border-left: 4px solid #D97706; padding: 12px 16px; font-size: 12px; color: #92400E; margin-top: 20px; border-radius: 0 4px 4px 0; }}
    .footer {{ background: #F9FAFB; padding: 16px 30px; text-align: center; font-size: 11px; color: #6B7280; border-top: 1px solid #E5E7EB; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Property Defect Inspection Report</h1>
    <p>AI-Powered Computer Vision Analysis · Singapore Property Inspection System</p>
  </div>
  <div class="body">
    <p class="greeting">Dear {owner},</p>
    <p>Please find attached the defect inspection report for your property. The AI analysis has been completed.</p>

    <table class="info-table">
      <tr><td>Property Address</td><td>{address}{unit_str}</td></tr>
      <tr><td>Inspection Date</td><td>{insp_date}</td></tr>
      <tr><td>Inspecting Agent</td><td>{agent}</td></tr>
      <tr><td>Images Analyzed</td><td>{len(results)}</td></tr>
      <tr><td>Report Date</td><td>{datetime.now().strftime('%d %B %Y')}</td></tr>
    </table>

    <div class="stats">
      <div class="stat stat-total"><div class="num">{total_defects}</div><div class="lbl">TOTAL DEFECTS</div></div>
      <div class="stat stat-major"><div class="num">{major}</div><div class="lbl">MAJOR</div></div>
      <div class="stat stat-moderate"><div class="num">{moderate}</div><div class="lbl">MODERATE</div></div>
      <div class="stat stat-minor"><div class="num">{total_defects - major - moderate}</div><div class="lbl">MINOR</div></div>
    </div>

    <p>The full detailed report is attached as a PDF. Please review all findings carefully.</p>

    <div class="disclaimer">
      ⚠️ <strong>Important:</strong> This report was generated using AI-assisted computer vision.
      We recommend verifying major defects with a qualified BCA-registered property inspector before
      making repair or transaction decisions.
    </div>
  </div>
  <div class="footer">
    This is an automated email from the Property Defect Inspection System.<br>
    Generated on {datetime.now().strftime('%d %B %Y at %H:%M SGT')}
  </div>
</div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject

    plain_body = (
        f"Dear {owner},\n\n"
        f"Please find attached the Property Defect Inspection Report.\n\n"
        f"Property: {address}{unit_str}\n"
        f"Inspection Date: {insp_date}\n"
        f"Agent: {agent}\n"
        f"Total Defects Found: {total_defects} (Major: {major}, Moderate: {moderate})\n\n"
        f"The PDF report is attached.\n\n"
        f"Note: This is an AI-assisted analysis. Please verify critical defects with a qualified inspector.\n\n"
        f"Property Defect Inspection System\n"
        f"Generated: {datetime.now().strftime('%d %B %Y')}"
    )

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # Attach PDF
    with open(report_path, "rb") as f:
        pdf_part = MIMEApplication(f.read(), _subtype="pdf")
        pdf_part.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"inspection_report_{address[:20].replace(' ', '_')}.pdf",
        )
    msg.attach(pdf_part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
