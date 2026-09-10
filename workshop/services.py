from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML

def generate_coating_certificate_pdf(certificate) -> bytes:
    """Renderuje szablon HTML certyfikatu do binarnego pliku PDF."""
    context = {
        'cert': certificate,
        'order': certificate.order,
        'vehicle': certificate.order.vehicle,
        'customer': certificate.order.vehicle.owner,
    }
    
    html_string = render_to_string('workshop/certificate_pdf.html', context)
    
    pdf_buffer = BytesIO()
    HTML(string=html_string).write_pdf(target=pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()
    pdf_buffer.close()
    
    return pdf_bytes
