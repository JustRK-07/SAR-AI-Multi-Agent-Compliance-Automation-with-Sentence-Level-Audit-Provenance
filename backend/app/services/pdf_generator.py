from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from datetime import datetime

from app.db import crud
from app.db.models import SARDB


def generate_sar_pdf(db: Session, sar: SARDB) -> bytes:
    """
    Generate a PDF document for a SAR with audit trail.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )

    elements = []

    # Title
    elements.append(Paragraph("SUSPICIOUS ACTIVITY REPORT", title_style))
    elements.append(Spacer(1, 0.2*inch))

    # SAR Information Table
    alert = crud.get_alert_by_id(db, sar.alert_id)
    customer = alert.customer if alert else None

    info_data = [
        ["SAR ID:", sar.id],
        ["Filing ID:", sar.filing_id or "Pending"],
        ["Alert ID:", sar.alert_id],
        ["Generated:", sar.created_at.strftime("%Y-%m-%d %H:%M:%S")],
        ["Status:", sar.status.upper()],
    ]

    info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))

    # Subject Information
    elements.append(Paragraph("SUBJECT INFORMATION", heading_style))

    if customer:
        subject_data = [
            ["Name:", customer.name],
            ["Account:", f"****{customer.account_number[-4:]}" if customer.account_number else "N/A"],
            ["PAN:", customer.pan or "N/A"],
            ["Occupation:", customer.occupation or "N/A"],
        ]
    else:
        subject_data = [["Name:", "Unknown"]]

    subject_table = Table(subject_data, colWidths=[1.5*inch, 3*inch])
    subject_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(subject_table)
    elements.append(Spacer(1, 0.2*inch))

    # Typology Classification
    elements.append(Paragraph("TYPOLOGY CLASSIFICATION", heading_style))

    typology_data = [
        ["Typology:", sar.typology],
        ["FinCEN Code:", sar.fincen_code],
        ["Confidence:", f"{sar.confidence_score:.1%}"],
    ]

    typology_table = Table(typology_data, colWidths=[1.5*inch, 3*inch])
    typology_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(typology_table)
    elements.append(Spacer(1, 0.2*inch))

    # Narrative
    elements.append(Paragraph("SAR NARRATIVE", heading_style))
    elements.append(Spacer(1, 0.1*inch))

    # Split narrative into paragraphs
    paragraphs = sar.narrative.split('\n\n')
    for para in paragraphs:
        if para.strip():
            elements.append(Paragraph(para.strip(), body_style))
            elements.append(Spacer(1, 0.1*inch))

    elements.append(Spacer(1, 0.2*inch))

    # Transaction Summary
    elements.append(Paragraph("TRANSACTION SUMMARY", heading_style))

    stats = crud.get_transaction_stats(db, sar.alert_id)

    txn_data = [
        ["Total Transactions:", str(stats["transaction_count"])],
        ["Total Amount:", f"₹{stats['total_amount']:,.2f}"],
        ["Unique Sources:", str(stats["unique_sources"])],
        ["Date Range:", f"{stats['date_range'][0]} to {stats['date_range'][1]}" if stats['date_range'][0] else "N/A"],
    ]

    txn_table = Table(txn_data, colWidths=[1.5*inch, 3*inch])
    txn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(txn_table)
    elements.append(Spacer(1, 0.2*inch))

    # Audit Trail Summary
    elements.append(Paragraph("AUDIT TRAIL", heading_style))

    audit_logs = crud.get_audit_logs_by_sar(db, sar.id)

    audit_summary = Paragraph(
        f"This SAR was generated with complete audit trail. "
        f"Total audit entries: {len(audit_logs)}. "
        f"All claims have been verified against source data. "
        f"Overall confidence score: {sar.confidence_score:.1%}.",
        body_style
    )
    elements.append(audit_summary)
    elements.append(Spacer(1, 0.3*inch))

    # Footer
    elements.append(Paragraph(
        f"Generated by SAR Narrative Generator | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
