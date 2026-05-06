from flask import Flask, render_template, request, redirect, session
import mysql.connector
import logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = "clave_secreta_123"
import os


conexion = None
cursor = None

from urllib.parse import urlparse
import os
import mysql.connector

url = os.getenv("MYSQL_PUBLIC_URL")

if not url:
    print("❌ NO EXISTE MYSQL_PUBLIC_URL")
    conexion = None
    cursor = None
else:
    db = urlparse(url)

    conexion = mysql.connector.connect(
        host=db.hostname,
        user=db.username,
        password=db.password,
        database=db.path.replace("/", ""),
        port=db.port
    )

    cursor = conexion.cursor()
    print("✅ CONECTADO A MYSQL")

# -----------------------
# CALCULAR PUNTOS (IGUAL QUE TU APP)
# -----------------------
def calcular_puntuacion(honor, r1, r2, r3, extra):

    honor = honor or 0
    r1 = r1 or 0
    r2 = r2 or 0
    r3 = r3 or 0
    extra = extra or 0

    placas = r1 + r2 + r3

    # HONOR
    if honor >= 10000:
        puntos_honor = 8
    elif honor >= 4000:
        puntos_honor = 5
    elif honor >= 2000:
        puntos_honor = 2
    elif honor >= 1000:
        puntos_honor = 0.5
    else:
        puntos_honor = 0

    # PLACAS
    if placas >= 150:
        puntos_placas = 4
    elif placas >= 100:
        puntos_placas = 2
    elif placas >= 70:
        puntos_placas = 1
    else:
        puntos_placas = 0

    return placas, puntos_honor + puntos_placas + extra

# -----------------------
# INICIO
# -----------------------
@app.route("/")
def inicio():
    if cursor is None:
        return "❌ Error de conexión a la base de datos"

    try:
        cursor.execute("""
            SELECT nombre, player_id, telefono,
            honor, ronda1_gc, ronda2_gc, ronda3_gc,
            puntos_extra, vidas
            FROM jugadores
        """)
    except Exception as e:
        return f"💥 Error SQL: {e}"

    jugadores = []

    for fila in cursor.fetchall():

        telefono = fila[2] or ""

        honor = int(fila[3] or 0)
        r1 = int(fila[4] or 0)
        r2 = int(fila[5] or 0)
        r3 = int(fila[6] or 0)
        extra = int(fila[7] or 0)

        # 🔥 CALCULAR PLACAS
        placas = r1 + r2 + r3

        # 🔥 PUNTOS
        if honor >= 10000:
            puntos_honor = 8
        elif honor >= 4000:
            puntos_honor = 5
        elif honor >= 2000:
            puntos_honor = 2
        elif honor >= 1000:
            puntos_honor = 0.5
        else:
            puntos_honor = 0

        if placas >= 150:
            puntos_placas = 4
        elif placas >= 100:
            puntos_placas = 2
        elif placas >= 70:
            puntos_placas = 1
        else:
            puntos_placas = 0

        puntos = puntos_honor + puntos_placas + extra

        jugadores.append((
            fila[0],   # nombre
            fila[1],   # id
            telefono,  # 📱 telefono
            honor,
            r1, r2, r3,
            placas,
            extra,
            puntos,
            fila[8]    # vidas
        ))

    # 🔥 ORDENAR POR HONOR
    jugadores.sort(key=lambda x: x[3], reverse=True)

    return render_template(
        "index.html",
        jugadores=jugadores,
        admin=session.get("admin")
    )
    
@app.route("/login", methods=["POST"])
def login():
    user = request.form["user"]
    password = request.form["pass"]

    if user == "admin" and password == "MIGAJASYUMYUM":
        session["admin"] = True
        return redirect("/")

    session.pop("admin", None)
    return redirect("/?error=1")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# -----------------------
# AGREGAR
# -----------------------
@app.route("/agregar", methods=["POST"])
def agregar():
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        INSERT INTO jugadores
        (nombre, player_id, telefono,
         honor,
         ronda1_gc, ronda2_gc, ronda3_gc,
         puntos_extra,
         vidas,
         penalizado)
        VALUES (%s,%s,%s,0,0,0,0,0,3,0)
    """, (
        request.form["nombre"],
        request.form["id"],
        request.form["telefono"]
    ))

    conexion.commit()
    return redirect("/")


# -----------------------
# ELIMINAR
# -----------------------
@app.route("/eliminar/<id>")
@app.route("/eliminar/<id>")
def eliminar(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"

    cursor.execute(
        "DELETE FROM jugadores WHERE player_id=%s LIMIT 1",
        (id,)
    )

    conexion.commit()
    return redirect("/")

# -----------------------
# EDITAR HONOR
# -----------------------
@app.route("/editar_honor/<id>", methods=["POST"])
def editar_honor(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("UPDATE jugadores SET honor=%s WHERE player_id=%s",
                   (request.form["honor"], id))
    conexion.commit()
    return redirect("/")

# -----------------------
# EDITAR RONDAS
# -----------------------
@app.route("/editar_ronda/<id>/<campo>", methods=["POST"])
def editar_ronda(id, campo):
    if not session.get("admin"):
        return redirect("/")
    valor = request.form["valor"]

    if cursor is None:
        return "❌ Error de conexión a la base de datos"

    cursor.execute(f"""
        UPDATE jugadores
        SET {campo}=%s
        WHERE player_id=%s
    """, (valor, id))

    conexion.commit()
    return redirect("/")

# -----------------------
# 💥 EDITAR EXTRA (FIX REAL)
# -----------------------
@app.route("/editar_extra/<id>", methods=["POST"])
def editar_extra(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET puntos_extra=%s
        WHERE player_id=%s
    """, (request.form["extra"], id))

    conexion.commit()
    return redirect("/")

# -----------------------
# CONTAR VIDAS (IGUAL)
# -----------------------
@app.route("/contar_vidas")
def contar_vidas():
    if cursor is None:
        return "❌ Error de conexión a la base de datos"

    cursor.execute("SELECT player_id, honor, vidas, penalizado FROM jugadores")

    for player_id, honor, vidas, penalizado in cursor.fetchall():

        honor = int(honor or 0)
        vidas = int(vidas or 0)
        penalizado = int(penalizado or 0)

        if honor < 1000 and penalizado == 0:
            if vidas > 0:
                cursor.execute("""
                    UPDATE jugadores
                    SET vidas = vidas - 1, penalizado = 1
                    WHERE player_id=%s
                """, (player_id,))

        elif honor >= 1000 and penalizado == 1:
            if vidas < 3:
                cursor.execute("""
                    UPDATE jugadores
                    SET vidas = vidas + 1, penalizado = 0
                    WHERE player_id=%s
                """, (player_id,))

    conexion.commit()
    return redirect("/")
# -----------------------
# ➕ SUMAR VIDA
# -----------------------
@app.route("/sumar_vida/<id>")
def sumar_vida(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET vidas = LEAST(vidas+1, 3)
        WHERE player_id=%s
    """, (id,))
    conexion.commit()
    return redirect("/")
# -----------------------
# BUSCAR
# -----------------------
from flask import request, render_template, session

@app.route("/buscar")
def buscar():
    dato = request.args.get("q")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"

    cursor.execute("""
        SELECT nombre, player_id, telefono,
        honor, ronda1_gc, ronda2_gc, ronda3_gc,
        puntos_extra, vidas
        FROM jugadores
        WHERE nombre LIKE %s OR player_id LIKE %s
    """, (f"%{dato}%", f"%{dato}%"))

    jugadores = []

    def generar_mensaje(honor, placas, vidas):

        if honor >= 10000:
            return "👑 WOW!! QUE GRAN APORTE AL CLAN!! MIS RESPETOS 🔥"

        if honor >= 2000:
            if placas < 70:
                return "⚠️ WOW! amo tu dedicación, pero échale más ganas a Guerra de Clanes 💀"
            return "🔥 WOW! gracias por tu esfuerzo!! sigue así 💪"

        if honor >= 1000:
            if placas < 70:
                return "⚠️ Me gusta como va la cosa, pero échale más ganas a Guerra de Clanes porfi 💀"
            return "✨ Excelente! sigue así... intenta llegar a +2000 📈"

        return f"😬 necesitas echarle más ganas... tienes {vidas} ❤️"

    for fila in cursor.fetchall():

        placas, puntos = calcular_puntuacion(
            fila[3], fila[4], fila[5], fila[6], fila[7]
        )

        mensaje = generar_mensaje(
            fila[3],
            placas,
            fila[8]
        )

        jugadores.append((
            fila[0],
            fila[1],
            fila[2],
            fila[3],
            fila[4],
            fila[5],
            fila[6],
            placas,
            fila[7],
            puntos,
            fila[8],
            mensaje
        ))

    # 🔥 AQUÍ LA CLAVE
    no_encontrado = len(jugadores) == 0
    jugadores.sort(key=lambda x: x[3], reverse=True)

    return render_template(
        "index.html",
        jugadores=jugadores,
        admin=session.get("admin", False),
        no_encontrado=no_encontrado  # 👈 FALTABA ESTO
    )





opiniones = []

@app.route("/opiniones")
def opiniones_page():
    return render_template(
        "opiniones.html",
        opiniones=opiniones,
        admin=session.get("admin", False)
    )

@app.route("/agregar_opinion", methods=["POST"])
def agregar_opinion():
    opiniones.append(request.form["opinion"])
    return redirect("/opiniones")

@app.route("/borrar_opinion/<int:index>")
def borrar_opinion(index):
    if not session.get("admin"):
        return redirect("/opiniones")

    if 0 <= index < len(opiniones):
        opiniones.pop(index)

    return redirect("/opiniones")

    # 🔥 ORDENAR POR HONOR (ESTO TE FALTABA)
    jugadores.sort(key=lambda x: x[3], reverse=True)

    return render_template(
        "index.html",
        jugadores=jugadores,
        admin=session.get("admin", False)
    )
  


@app.route("/actualizar_vidas")
def actualizar_vidas():
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        SELECT player_id, honor, vidas, penalizado
        FROM jugadores
    """)

    for player_id, honor, vidas, penalizado in cursor.fetchall():

        honor = int(honor or 0)
        vidas = int(vidas or 0)
        penalizado = int(penalizado or 0)

        # 💀 CASO 1: pierde vida SOLO UNA VEZ
        if honor < 1000 and penalizado == 0:

            if vidas > 0:
                cursor.execute("""
                    UPDATE jugadores
                    SET vidas = vidas - 1,
                        penalizado = 1
                    WHERE player_id=%s
                """, (player_id,))

        # ❤️ CASO 2: recupera vida si vuelve a subir honor
        elif honor >= 1000 and penalizado == 1:

            if vidas < 3:
                cursor.execute("""
                    UPDATE jugadores
                    SET vidas = vidas + 1,
                        penalizado = 0
                    WHERE player_id=%s
                """, (player_id,))

    conexion.commit()
    return redirect("/")
   
# -----------------------
# EDITAR NOMBRE
# -----------------------
@app.route("/editar_nombre/<id>", methods=["POST"])
def editar_nombre(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET nombre=%s
        WHERE player_id=%s
    """, (request.form["nombre"], id))
    conexion.commit()
    return redirect("/")

@app.route("/reset_corazones")
def reset_corazones():
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET vidas = 3,
            penalizado = 0
    """)

    conexion.commit()
    return redirect("/")
# -----------------------
# EDITAR TELEFONO
# -----------------------
@app.route("/editar_tel/<id>", methods=["POST"])
def editar_tel(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET telefono=%s
        WHERE player_id=%s
    """, (request.form["telefono"], id))
    conexion.commit()
    return redirect("/")
# -----------------------
# ➖ QUITAR VIDA
# -----------------------
@app.route("/quitar_vida/<id>")
def quitar_vida(id):
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET vidas = GREATEST(vidas-1, 0)
        WHERE player_id=%s
    """, (id,))
    conexion.commit()
    return redirect("/")
# -----------------------
# RESET SEMANA
# -----------------------
@app.route("/reset_semana")
def reset_semana():
    if not session.get("admin"):
        return redirect("/")
    if cursor is None:
        return "❌ Error de conexión a la base de datos"
    cursor.execute("""
        UPDATE jugadores
        SET honor=0,
            ronda1_gc=0,
            ronda2_gc=0,
            ronda3_gc=0,
            penalizado=0
    """)
    conexion.commit()
    return redirect("/")
