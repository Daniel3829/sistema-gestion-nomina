from django.db import models

class Empresa(models.Model):
    correo = models.EmailField(unique=True)
    nit = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=100)
    contraseña = models.CharField(max_length=100)
    token_recuperacion = models.CharField(max_length=200, null=True, blank=True)
    token_expira = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.razon_social

class Empleado(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    # --- tus otros campos ---
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=50)
    numero_documento = models.CharField(max_length=50, unique=True)
    tipo_contrato = models.CharField(max_length=50)
    jornada = models.CharField(max_length=50)
    cargo = models.CharField(max_length=100)
    sede = models.CharField(max_length=100)
    fecha_ingreso = models.DateField()
    tipo_salario = models.CharField(max_length=50)
    salario_basico = models.DecimalField(max_digits=10, decimal_places=2)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=150)
    correo = models.EmailField()
    telefono = models.CharField(max_length=50)
    eps = models.CharField(max_length=100)
    fondo_pensiones = models.CharField(max_length=100)
    arl = models.CharField(max_length=100)
    caja_compensacion = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='empleados/', null=True, blank=True)

    # --- pagos ---
    horas_extra_diurna = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    horas_extra_nocturna = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    horas_extra_festiva = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bonificaciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    salario_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)

    def calcular_salario_total(self):
        """Calcula el salario total con horas extras, bonificaciones y descuentos"""
        valor_hora = float(self.salario_basico) / 240  # Promedio 240 horas al mes

        total = (
            float(self.salario_basico)
            + float(self.horas_extra_diurna) * valor_hora * 1.25
            + float(self.horas_extra_nocturna) * valor_hora * 1.75
            + float(self.horas_extra_festiva) * valor_hora * 2.0
            + float(self.bonificaciones)
            - float(self.descuentos)
        )
        return round(total, 2)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
