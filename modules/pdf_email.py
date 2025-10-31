"""
PDF generation and email sending module
Professional PDF reports with ReportLab
SMTP email delivery with attachment support
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_meeting_pdf(meeting_id, title, date, participants, transcript, summary, google_notes, audio_link):
    """
    Generate comprehensive PDF report with professional formatting
    
    Args:
        meeting_id: Unique meeting identifier
        title: Meeting title
        date: Meeting date/time
        participants: Comma-separated participant names
        transcript: List of transcript segments with speakers and timestamps
        summary: Markdown-formatted summary
        google_notes: Additional notes from Google Docs
        audio_link: URL or path to audio file
    
    Returns:
        Path to generated PDF file
    """
    logger.info(f"Generating PDF for meeting: {meeting_id}")
    
    pdf_path = f"data/{meeting_id}/meeting_report.pdf"
    Path(f"data/{meeting_id}").mkdir(parents=True, exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#5f6368'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#202124'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#202124'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # ========== TITLE PAGE ==========
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("🎙️ MeetingInsight", title_style))
    story.append(Paragraph("AI-Powered Meeting Transcription & Analysis", subtitle_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Meeting title
    story.append(Paragraph(f"<b>{title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    # Meeting info table
    meeting_info = [
        ['Meeting ID:', meeting_id],
        ['Date & Time:', date],
        ['Participants:', participants],
        ['Audio Recording:', f'<link href="{audio_link}" color="blue">{audio_link[:60]}...</link>']
    ]
    
    info_table = Table(meeting_info, colWidths=[1.5*inch, 5*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 11),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Divider line
    story.append(Spacer(1, 0.2*inch))
    story.append(PageBreak())
    
    # ========== SUMMARY SECTION ==========
    story.append(Paragraph("📊 Meeting Summary & Analysis", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Parse and add summary sections
    summary_lines = summary.split('\n')
    current_section = None
    
    for line in summary_lines:
        line = line.strip()
        if not line:
            continue
        
        # Handle markdown headers
        if line.startswith('# '):
            continue  # Skip main title
        elif line.startswith('## '):
            section_title = line.replace('##', '').strip()
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(section_title, subheading_style))
        elif line.startswith('- ') or line.startswith('• '):
            # Bullet points
            bullet_text = line.lstrip('-• ').strip()
            story.append(Paragraph(f"• {bullet_text}", body_style))
        elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
            # Numbered lists
            story.append(Paragraph(line, body_style))
        else:
            # Regular text
            story.append(Paragraph(line, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(PageBreak())
    
    # ========== TRANSCRIPT SECTION ==========
    story.append(Paragraph("📝 Full Transcript with Millisecond Timestamps", heading_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Transcript note
    transcript_note = Paragraph(
        "<i>This transcript includes speaker attribution with exact timestamps at millisecond precision (HH:MM:SS.mmm format).</i>",
        body_style
    )
    story.append(transcript_note)
    story.append(Spacer(1, 0.15*inch))
    
    # Create transcript table
    transcript_data = [['Timestamp', 'Speaker', 'Text']]
    
    for segment in transcript:
        # Wrap text for better formatting
        text_para = Paragraph(segment['text'], body_style)
        speaker_para = Paragraph(f"<b>{segment['speaker']}</b>", body_style)
        time_para = Paragraph(segment['start'], body_style)
        
        transcript_data.append([time_para, speaker_para, text_para])
    
    # Create table with proper column widths
    transcript_table = Table(
        transcript_data,
        colWidths=[1*inch, 1.3*inch, 4.2*inch],
        repeatRows=1  # Repeat header on each page
    )
    
    transcript_table.setStyle(TableStyle([
        # Header row styling
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0fe')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        
        # Body styling
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Grid and padding
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    
    story.append(transcript_table)
    
    # ========== GOOGLE NOTES SECTION ==========
    if google_notes and google_notes.strip():
        story.append(PageBreak())
        story.append(Paragraph("📄 Google Meet Notes", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        notes_lines = google_notes.split('\n')
        for line in notes_lines:
            if line.strip():
                story.append(Paragraph(line, body_style))
                story.append(Spacer(1, 0.05*inch))
    
    # ========== FOOTER ==========
    story.append(Spacer(1, 0.5*inch))
    
    footer_text = f"""
    <i>This report was generated by <b>MeetingInsight</b> on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}.</i><br/>
    <i>MeetingInsight is a free, open-source meeting transcription platform.</i><br/>
    <i>For questions or support, contact: aditya.dev@projectmail.com</i>
    """
    
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#5f6368'),
        alignment=TA_CENTER
    )))
    
    # Build PDF
    try:
        doc.build(story)
        logger.info(f"PDF generated successfully: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise

def send_meeting_email(recipients, pdf_path, meeting_title, custom_message=None):
    """
    Send meeting PDF via email using SMTP
    
    Args:
        recipients: Comma-separated email addresses
        pdf_path: Path to PDF file
        meeting_title: Meeting title for subject line
        custom_message: Optional custom message body
    
    Returns:
        bool: True if successful, False otherwise
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    logger.info(f"Sending email to: {recipients}")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_password:
        logger.error("SMTP credentials not configured")
        raise ValueError("SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
    
    # Parse recipients
    recipient_list = [r.strip() for r in recipients.split(',')]
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = ', '.join(recipient_list)
    msg['Subject'] = f"Meeting Report: {meeting_title}"
    
    # Email body
    if custom_message:
        body = custom_message
    else:
        body = f"""
Hello,

Please find attached the complete transcript and AI-generated summary for the meeting:

📋 {meeting_title}

This comprehensive report includes:
• Speaker-attributed transcript with millisecond-precision timestamps
• AI-generated executive summary and key points
• Extracted action items with assignees and priorities
• Decisions made during the meeting
• Time-coded references to important moments

The transcript was generated using MeetingInsight, a free and open-source meeting transcription platform.

If you have any questions about this meeting or need the audio recording, please reply to this email.

Best regards,
MeetingInsight Bot

---
This is an automated message from MeetingInsight.
For technical support: aditya.dev@projectmail.com
        """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(pdf_path)}'
        )
        
        msg.attach(part)
    else:
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {len(recipient_list)} recipient(s)")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check your credentials.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_bulk_emails(recipients_list, pdf_path, meeting_title):
    """Send emails to multiple recipients with rate limiting"""
    import time
    
    success_count = 0
    failed_recipients = []
    
    for recipient in recipients_list:
        try:
            if send_meeting_email(recipient, pdf_path, meeting_title):
                success_count += 1
                time.sleep(1)  # Rate limiting
            else:
                failed_recipients.append(recipient)
        except Exception as e:
            logger.error(f"Failed to send to {recipient}: {str(e)}")
            failed_recipients.append(recipient)
    
    logger.info(f"Bulk email complete: {success_count}/{len(recipients_list)} successful")
    
    if failed_recipients:
        logger.warning(f"Failed recipients: {', '.join(failed_recipients)}")
    
    return success_count, failed_recipients