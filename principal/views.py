# ---------------------------------------------
# 🔹 Python Standard Imports
# ---------------------------------------------
import io
import json
import traceback
import re
import secrets
import os
import logging
from datetime import timedelta
from datetime import datetime
from decimal import Decimal

# ---------------------------------------------
# 🔹 Django Imports
# ---------------------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from django.contrib import messages
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail, BadHeaderError
from smtplib import SMTPException
from django.utils import timezone

# ---------------------------------------------
# 🔹 External Libraries (ReportLab)
# ---------------------------------------------
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

# ---------------------------------------------
# 🔹 Local App Imports
# ---------------------------------------------
from .models import Empresa, Empleado

# ---------------------------------------------
# 🔹 Home
# ---------------------------------------------

# Página principal
def index(request):
    return render(request, 'index.html')

# Sidebar izquierdo (informativo)
def sidebar_left(request):
    return render(request, 'sidebar-left.html')

# Sidebar derecho (informativo)
def sidebar_right(request):
    return render(request, 'sidebar-right.html')

# Página de contacto
def contact(request):
    return render(request, 'contact.html')

# Página acerca de / about
def about(request):
    return render(request, 'about.html')


# ---------------------------------------------
# 🔹 Registrar empresa
# ---------------------------------------------
@csrf_exempt
def registrar(request):
    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
            username = datos.get('nombre_usuario')
            email = datos.get('correo')
            contraseña = datos.get('contraseña')

            # --- Validaciones de contraseña ---
            if len(contraseña) < 8:
                return JsonResponse({'error': 'La contraseña debe tener al menos 8 caracteres.'}, status=400)
            if not re.search(r'[A-Z]', contraseña):
                return JsonResponse({'error': 'Debe incluir al menos una letra mayúscula.'}, status=400)
            if not re.search(r'[a-z]', contraseña):
                return JsonResponse({'error': 'Debe incluir al menos una letra minúscula.'}, status=400)
            if not re.search(r'[0-9]', contraseña):
                return JsonResponse({'error': 'Debe incluir al menos un número.'}, status=400)
            if not re.search(r'[!@#$%^&*]', contraseña):
                return JsonResponse({'error': 'Debe incluir al menos un símbolo (!@#$%^&*).'}, status=400)

            # --- Encriptar la contraseña ---
            contraseña_encriptada = make_password(contraseña)

            # --- Crear la empresa ---
            Empresa.objects.create(
                correo=email,
                nit=datos['nit'],
                razon_social=datos['razon_social'],
                contraseña=contraseña_encriptada
            )

            return JsonResponse({'mensaje': 'Registro exitoso.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'register.html')


# ---------------------------------------------
# 🔹 Login empresa
# ---------------------------------------------
@csrf_protect
def login(request):
    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
            correo = datos.get('correo')
            contraseña = datos.get('contraseña')

            empresa = Empresa.objects.get(correo=correo)

            if check_password(contraseña, empresa.contraseña):
                # 🔹 Guardar sesión
                request.session['empresa_id'] = empresa.id
                request.session['empresa_nombre'] = empresa.razon_social
                return JsonResponse({'mensaje': 'OK'})
            else:
                return JsonResponse({'error': 'Correo o contraseña incorrectos.'}, status=401)

        except Empresa.DoesNotExist:
            return JsonResponse({'error': 'Correo o contraseña incorrectos.'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # Si ya hay sesión, redirigir a inicio
    if request.session.get('empresa_id'):
        return redirect('inicio')

    return render(request, 'login.html')


# ---------------------------------------------
# 🔹 Recuperar contraseña Gmail SMTP
# ---------------------------------------------
"""
def recuperar_contraseña(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Ingrese un correo.")
            return redirect("recuperar")

        try:
            empresa = Empresa.objects.get(correo=email)
        except Empresa.DoesNotExist:
            empresa = None

        # Este mensaje se muestra SIEMPRE
        messages.info(request, "Si el correo está registrado, enviaremos instrucciones.")

        # Si no existe, se redirige sin enviar nada
        if not empresa:
            return redirect("correo_enviado")

        # Crear token seguro
        token = secrets.token_urlsafe(32)

        # Guardamos token y fecha de expiración
        empresa.token_recuperacion = token
        empresa.token_expira = timezone.now() + timedelta(hours=1)
        empresa.save()

        # Enviar correo con el enlace
        enlace = request.build_absolute_uri(
            reverse("restablecer", kwargs={"token": token})
        )

        asunto = "Restablece tu contraseña - TecNomina"
        mensaje = f"""
#Hola {empresa.razon_social},

#Has solicitado restablecer tu contraseña.

#Haz clic en el siguiente enlace para crear una nueva contraseña:

#👉 {enlace}

#Este enlace expirará en 1 hora.

#Si no solicitaste esto, ignora este mensaje.
"""

        send_mail(asunto, mensaje, None, [email], fail_silently=False)

        return redirect("correo_enviado")

    return render(request, "recuperar_contrasena.html")

def correo_enviado(request):
    return render(request, "correo_enviado.html")

# 3. Restablecer la contraseña
def restablecer_contraseña(request, token):
    try:
        empresa = Empresa.objects.get(token_recuperacion=token)
    except Empresa.DoesNotExist:
        return render(request, "token_invalido.html")

    # Verificar si expiró
    if timezone.now() > empresa.token_expira:
        return render(request, "token_expirado.html")

    if request.method == "POST":
        nueva1 = request.POST.get("nueva1")
        nueva2 = request.POST.get("nueva2")

        if nueva1 != nueva2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(request.path)

        # Guardar contraseña encriptada
        empresa.contraseña = make_password(nueva1)

        # Borrar token
        empresa.token_recuperacion = None
        empresa.token_expira = None

        empresa.save()

        messages.success(request, "Tu contraseña fue actualizada correctamente.")
        return redirect("login")

    return render(request, "restablecer_form.html", {"empresa": empresa}) """

logger = logging.getLogger(__name__)

# ---------- Helper: enviar correo usando la API de Brevo ----------
def enviar_correo_brevo(destino: str, asunto: str, texto: str, html: str | None = None) -> bool:
    """
    Envía un correo a través de la API de Brevo (TransactionalEmailsApi).
    Devuelve True si el envío parece correcto, False si ocurre un error.
    """
    api_key = os.getenv("BREVO_API_KEY")
    remitente = os.getenv("BREVO_EMAIL")

    if not api_key or not remitente:
        logger.error("BREVO_API_KEY o BREVO_EMAIL no están configurados en las variables de entorno.")
        return False

    configuration = Configuration()
    configuration.api_key["api-key"] = api_key

    api_instance = TransactionalEmailsApi(ApiClient(configuration))

    email = SendSmtpEmail(
        to=[{"email": destino}],
        sender={"email": remitente},
        subject=asunto,
        text_content=texto,
    )
    # Si deseas enviar HTML, incluye html_content
    if html:
        email.html_content = html

    try:
        api_instance.send_transac_email(email)
        logger.info("Correo enviado por Brevo a %s", destino)
        return True
    except ApiException as e:
        logger.exception("Error API Brevo al enviar correo a %s: %s", destino, getattr(e, "body", str(e)))
        return False
    except Exception as e:
        logger.exception("Error inesperado al enviar correo por Brevo: %s", str(e))
        return False


# -----------------------------
# Recuperar contraseña
# -----------------------------
def recuperar_contraseña(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Ingrese un correo.")
            return redirect("recuperar")

        try:
            empresa = Empresa.objects.get(correo=email)
        except Empresa.DoesNotExist:
            empresa = None

        # Mensaje informativo (siempre)
        messages.info(request, "Si el correo está registrado, enviaremos instrucciones.")

        # Si no existe, no enviamos nada pero mostramos la pantalla de confirmación
        if not empresa:
            return redirect("correo_enviado")

        # Crear token seguro
        token = secrets.token_urlsafe(32)

        # Guardar token y fecha de expiración
        empresa.token_recuperacion = token
        empresa.token_expira = timezone.now() + timedelta(hours=1)
        empresa.save()

        # Construir enlace absoluto
        enlace = request.build_absolute_uri(
            reverse("restablecer", kwargs={"token": token})
        )

        asunto = "Restablece tu contraseña - TecNomina"
        mensaje_texto = f"""Hola {empresa.razon_social},

Has solicitado restablecer tu contraseña.

Haz clic en el siguiente enlace para crear una nueva contraseña:

{enlace}

Este enlace expirará en 1 hora.

Si no solicitaste esto, ignora este mensaje.
"""

        # (Opcional) HTML simple para mejor presentación
        mensaje_html = f"""
<p>Hola <strong>{empresa.razon_social}</strong>,</p>
<p>Has solicitado restablecer tu contraseña.</p>
<p><a href="{enlace}">Haz clic aquí para crear una nueva contraseña</a></p>
<p>Este enlace expirará en 1 hora.</p>
<p>Si no solicitaste esto, ignora este mensaje.</p>
"""

        # Enviar por Brevo (API). No debe bloquear la vista si falla.
        enviado = enviar_correo_brevo(email, asunto, mensaje_texto, mensaje_html)
        if not enviado:
            # Ya registramos el error en logs; no mostramos detalles al usuario
            logger.warning("No se pudo enviar el correo de recuperación a %s (se continuará el flujo).", email)

        return redirect("correo_enviado")

    return render(request, "recuperar_contrasena.html")


def correo_enviado(request):
    return render(request, "correo_enviado.html")


# -----------------------------
# Restablecer la contraseña
# -----------------------------
def restablecer_contraseña(request, token):
    try:
        empresa = Empresa.objects.get(token_recuperacion=token)
    except Empresa.DoesNotExist:
        return render(request, "token_invalido.html")

    # Verificar expiración
    if timezone.now() > empresa.token_expira:
        return render(request, "token_expirado.html")

    if request.method == "POST":
        nueva1 = request.POST.get("nueva1")
        nueva2 = request.POST.get("nueva2")

        if nueva1 != nueva2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(request.path)

        # Guardar contraseña encriptada
        empresa.contraseña = make_password(nueva1)

        # Borrar token
        empresa.token_recuperacion = None
        empresa.token_expira = None

        empresa.save()

        messages.success(request, "Tu contraseña fue actualizada correctamente.")
        return redirect("login")

    return render(request, "restablecer_form.html", {"empresa": empresa})

# ---------------------------------------------
# 🔹 Logout
# ---------------------------------------------
def logout_view(request):
    request.session.flush()
    return redirect('login')


# ---------------------------------------------
# 🔹 Registrar empleado
# ---------------------------------------------
@csrf_protect
def registrar_empleado(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    if request.method == 'POST':
        try:
            datos = request.POST
            imagen = request.FILES.get('imagen')
            empresa = Empresa.objects.get(id=request.session['empresa_id'])

            # --- Validaciones ---
            if not datos.get('nombres') or not datos.get('apellidos'):
                return JsonResponse({'error': 'Los nombres y apellidos son obligatorios.'}, status=400)

            if not datos.get('numero_documento') or int(datos['numero_documento']) <= 0:
                return JsonResponse({'error': 'El número de documento debe ser positivo.'}, status=400)

            if not datos.get('correo'):
                return JsonResponse({'error': 'El correo es obligatorio.'}, status=400)

            if not datos.get('telefono') or not datos['telefono'].isdigit() or not (7 <= len(datos['telefono']) <= 10):
                return JsonResponse({'error': 'El teléfono debe tener entre 7 y 10 dígitos numéricos.'}, status=400)

            # --- Crear empleado ---
            Empleado.objects.create(
                empresa=empresa,
                nombres=datos['nombres'],
                apellidos=datos['apellidos'],
                tipo_documento=datos['tipo_documento'],
                numero_documento=datos['numero_documento'],
                tipo_contrato=datos['tipo_contrato'],
                jornada=datos['jornada'],
                cargo=datos['cargo'],
                sede=datos['sede'],
                fecha_ingreso=datos['fecha_ingreso'],
                tipo_salario=datos['tipo_salario'],
                salario_basico=datos['salario_basico'],
                ciudad=datos['ciudad'],
                direccion=datos['direccion'],
                correo=datos['correo'],
                telefono=datos['telefono'],
                eps=datos['eps'],
                fondo_pensiones=datos['fondo_pensiones'],
                arl=datos['arl'],
                caja_compensacion=datos['caja_compensacion'],
                imagen=imagen
                
            )

            return JsonResponse({'mensaje': 'Empleado registrado con éxito.'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'registrar_empleados.html')


# ---------------------------------------------
# 🔹 Buscar empleado
# ---------------------------------------------
def buscar_empleado(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    if request.method == 'POST':
        numero_documento = request.POST.get('numero_documento')
        if not numero_documento:
            return render(request, 'buscar.html', {'error': 'Ingrese un número de documento.'})

        # Verificar que el empleado pertenece a la empresa logueada
        empresa_id = request.session['empresa_id']
        empleado = Empleado.objects.filter(
            numero_documento=numero_documento,
            empresa_id=empresa_id
        ).first()

        if not empleado:
            return render(request, 'buscar.html', {'error': 'Empleado no encontrado en tu empresa.'})

        return redirect('perfil_empleado', numero_documento=numero_documento)

    return render(request, 'buscar.html')


# ---------------------------------------------
# 🔹 Perfil empleado
# ---------------------------------------------
def perfil_empleado(request, numero_documento):
    if not request.session.get('empresa_id'):
        return redirect('login')

    empresa_id = request.session['empresa_id']

    empleado = get_object_or_404(
        Empleado,
        numero_documento=numero_documento,
        empresa_id=empresa_id
    )

    if request.method == 'POST':
        # Datos generales
        empleado.nombres = request.POST.get('nombres')
        empleado.apellidos = request.POST.get('apellidos')
        empleado.correo = request.POST.get('correo')
        empleado.cargo = request.POST.get('cargo')
        empleado.sede = request.POST.get('sede')

        # Convertir a Decimal
        empleado.horas_extra_diurna = Decimal(request.POST.get('horas_extra_diurna') or 0)
        empleado.horas_extra_nocturna = Decimal(request.POST.get('horas_extra_nocturna') or 0)
        empleado.horas_extra_festiva = Decimal(request.POST.get('horas_extra_festiva') or 0)
        empleado.bonificaciones = Decimal(request.POST.get('bonificaciones') or 0)
        empleado.descuentos = Decimal(request.POST.get('descuentos') or 0)

        # Guardar salario total calculado desde JS
        salario_total = request.POST.get('salario_total')
        if salario_total:
            try:
                empleado.salario_total = Decimal(salario_total)
            except:
                empleado.salario_total = Decimal(0)

        # Imagen
        if 'imagen' in request.FILES:
            empleado.imagen = request.FILES['imagen']

        empleado.save()
        messages.success(request, '✅ Datos actualizados correctamente.')

    return render(request, 'perfil.html', {'empleado': empleado, 'modo_edicion': False})

def inicio(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    empresa_nombre = request.session.get('empresa_nombre', 'Tu Empresa')

    return render(request, 'inicio.html', {
        'empresa_nombre': empresa_nombre
    })

# ---------------------------------------------
# 🔹 Reportes (protegido)
# ---------------------------------------------
def reportes(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    empresa_id = request.session['empresa_id']

    empleados = Empleado.objects.filter(empresa_id=empresa_id)

    total_nomina = empleados.aggregate(total=Sum('salario_total'))['total'] or 0
    total_empleados = empleados.count()
    total_sedes = empleados.values('sede').distinct().count()

    contexto = {
        'total_nomina': total_nomina,
        'total_empleados': total_empleados,
        'total_sedes': total_sedes,
        'empleados': empleados,
    }

    return render(request, 'reportes.html', contexto)

def reportes_descarga(request):
    if not request.session.get('empresa_id'):
        return redirect('login')
    return render(request, 'reportes_descarga.html')

def encabezado_pdf(pdf, titulo):
    page_width, page_height = A4

    # Logo PNG
    try:
        logo_path = "static/images/TecNomina1.png"  # PNG convertido desde SVG
        pdf.drawImage(logo_path, 40, page_height - 100, width=120, height=60, preserveAspectRatio=True, mask='auto')
    except:
        # Si no existe, escribe texto
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(page_width / 2, page_height - 80, "TecNómina — Sistema de Nómina")

    # Fecha y título
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, page_height - 120, "Reporte generado: " + datetime.now().strftime("%d/%m/%Y %H:%M"))

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(page_width / 2, page_height - 140, titulo)

    pdf.line(40, page_height - 150, page_width - 40, page_height - 150)

def reporte_individual(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    empresa_id = request.session['empresa_id']

    documento = request.GET.get('documento')
    if not documento:
        messages.error(request, "Debes ingresar un número de documento.")
        return redirect('reportes_descarga')

    empleado = get_object_or_404(
        Empleado,
        numero_documento=documento,
        empresa_id=empresa_id
    )

    # Crear PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    encabezado_pdf(pdf, "Reporte Individual de Empleado")

    y = 700
    pdf.setFont("Helvetica", 11)
    data = [
        ["Campo", "Valor"],
        ["Nombres", empleado.nombres],
        ["Apellidos", empleado.apellidos],
        ["Tipo documento", empleado.tipo_documento],
        ["Número documento", empleado.numero_documento],
        ["Cargo", empleado.cargo],
        ["Tipo contrato", empleado.tipo_contrato],
        ["Jornada", empleado.jornada],
        ["Sede", empleado.sede],
        ["Ciudad", empleado.ciudad],
        ["Correo", empleado.correo],
        ["Teléfono", empleado.telefono],
        ["EPS", empleado.eps],
        ["Fondo pensiones", empleado.fondo_pensiones],
        ["ARL", empleado.arl],
        ["Caja compensación", empleado.caja_compensacion],
        ["Salario básico", f"${empleado.salario_basico:,.2f}"],
        ["Horas extra diurna", empleado.horas_extra_diurna],
        ["Horas extra nocturna", empleado.horas_extra_nocturna],
        ["Horas extra festiva", empleado.horas_extra_festiva],
        ["Bonificaciones", f"${empleado.bonificaciones:,.2f}"],
        ["Descuentos", f"${empleado.descuentos:,.2f}"],
        ["Salario total", f"${empleado.salario_total:,.2f}"],
    ]

    table = Table(data, colWidths=[180, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
    ]))
    table.wrapOn(pdf, 50, y)
    table.drawOn(pdf, 50, y - 500)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

def reporte_general(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    empresa_id = request.session['empresa_id']

    empleados = Empleado.objects.filter(empresa_id=empresa_id).order_by('apellidos')

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4
    
    encabezado_pdf(pdf, "Listado General de Empleados")

    data = [["Documento", "Nombre", "Cargo", "Sede", "Correo", "Teléfono"]]
    for e in empleados:
        data.append([
            e.numero_documento,
            f"{e.nombres} {e.apellidos}",
            e.cargo,
            e.sede,
            e.correo,
            e.telefono
        ])
    table = Table(data, colWidths=[80, 120, 100, 80, 100, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    table_width, table_height = table.wrap(0, 0)
    x = (page_width - table_width) / 2
    y = page_height - 150
    table.drawOn(pdf, x, y - table_height)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

def reporte_nomina(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    empresa_id = request.session['empresa_id']

    empleados = Empleado.objects.filter(empresa_id=empresa_id).order_by('apellidos')

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    encabezado_pdf(pdf, "Listado General con Valores de Nómina")

    data = [["Documento", "Nombre", "Cargo", "Salario Básico", "Salario Total"]]
    for e in empleados:
        data.append([
            e.numero_documento,
            f"{e.nombres} {e.apellidos}",
            e.cargo,
            f"${e.salario_basico:,.2f}",
            f"${e.salario_total:,.2f}"
        ])

    table = Table(data, colWidths=[80, 150, 120, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    table_width, table_height = table.wrap(0, 0)
    x = (page_width - table_width) / 2
    y = page_height - 150
    table.drawOn(pdf, x, y - table_height)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')



# ---------------------------------------------
# 🔹 Configuración (protegido)
# ---------------------------------------------
def configuracion(request):
    if not request.session.get('empresa_id'):
        return redirect('login')

    configuracion_actual = {
        'smmlv': 1300000,
        'auxilio_transporte': 162000,
        'porcentaje_eps': 4,
        'porcentaje_pension': 4,
        'umbral_fondo_solidaridad': 4,
    }

    return render(request, 'configuracion.html', {'config': configuracion_actual})
