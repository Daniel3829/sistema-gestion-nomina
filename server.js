const express = require('express');
const mysql = require('mysql');
const bodyParser = require('body-parser');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');

const app = express();
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// Middleware
app.use(cors());
app.use(express.json());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Conexión a la base de datos
const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: '', // coloca tu contraseña si tienes
    database: 'tecnomina',
    port: 3306
});

db.connect(err => {
    if (err) {
        console.error('❌ Error al conectar a MySQL:', err);
    } else {
        console.log('✅ Conectado a MySQL');
    }
});

// 🚀 RUTA DE REGISTRO
app.post('/registrar', (req, res) => {
    const { correo, nit, razon_social, contraseña } = req.body;

    if (!correo || !nit || !razon_social || !contraseña) {
        return res.status(400).send('Faltan datos.');
    }

    const sql = 'INSERT INTO empresas (correo, nit, razon_social, contraseña) VALUES (?, ?, ?, ?)';
    db.query(sql, [correo, nit, razon_social, contraseña], (err, result) => {
        if (err) {
            console.error('❌ Error al registrar:', err);
            return res.status(500).send('Error en el registro.');
        }
        console.log('✅ Empresa registrada:', correo);
        res.send('Registro exitoso.');
    });
});

app.post('/login', (req, res) => {
    const { correo, contraseña } = req.body;

    if (!correo || !contraseña) {
        return res.status(400).send('Faltan datos.');
    }

    const sql = 'SELECT * FROM empresas WHERE correo = ? AND contraseña = ?';
    db.query(sql, [correo, contraseña], (err, result) => {
        if (err) {
            console.error('❌ Error al iniciar sesión:', err);
            return res.status(500).send('Error en el servidor.');
        }

        if (result.length > 0) {
            console.log('✅ Inicio de sesión exitoso:', correo);
            res.send('OK');
        } else {
            res.status(401).send('Correo o contraseña incorrectos.');
        }
    });
});

// Ruta modificada para aceptar foto

app.post('/registrarEmpleado', upload.single('imagen'), (req, res) => {
    const {
        nombres, apellidos, tipo_documento, numero_documento,
        tipo_contrato, jornada, cargo, sede, fecha_ingreso,
        tipo_salario, salario_basico, ciudad, direccion,
        correo, telefono, eps, fondo_pensiones, arl, caja_compensacion
    } = req.body;

    const imagen = req.file ? req.file.filename : null;

    const sql = `
        INSERT INTO empleados (
            nombres, apellidos, tipo_documento, numero_documento, tipo_contrato, jornada, cargo,
            sede, fecha_ingreso, tipo_salario, salario_basico, ciudad, direccion, correo, telefono,
            eps, fondo_pensiones, arl, caja_compensacion, imagen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    db.query(sql, [
        nombres, apellidos, tipo_documento, numero_documento, tipo_contrato, jornada, cargo,
        sede, fecha_ingreso, tipo_salario, salario_basico, ciudad, direccion, correo, telefono,
        eps, fondo_pensiones, arl, caja_compensacion, imagen
    ], (err) => {
        if (err) {
            console.error(err);
            res.status(500).send('Error al registrar empleado');
        } else {
            res.send('Empleado registrado con éxito');
        }
    });
});


app.get('/buscarEmpleado/:documento', (req, res) => {
    const documento = req.params.documento;
    const sql = 'SELECT * FROM empleados WHERE numero_documento = ?';

    db.query(sql, [documento], (error, resultado) => {
        if (error) {
            console.error("❌ Error en la consulta SQL:", error.sqlMessage);
            res.status(500).send('Error en el servidor: ' + error.sqlMessage);
        } else if (resultado.length === 0) {
            res.status(404).send('Empleado no encontrado');
        } else {
            res.json(resultado[0]);
        }
    });
});

// Iniciar servidor
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
