import os
import re
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands
from groq import Groq

# --- SERVIDOR FLASK (UptimeRobot 24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Isla Lechero Bot Online 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# --- CONFIGURACIÓN DE DISCORD Y GROQ ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
Eres la IA oficial de la Isla Lechero. Tu personalidad sigue estas reglas strictly:
1. Tolerancia al caos: Toleras todo tipo de ruido y comportamientos absurdos.
2. Meritocracia gamberra: 
   - Si el usuario dice tonterías, actúa como NPC o dice bobadas: Responde con insultos burdos, pullas directas, lenguaje macarra, coloquial, sin filtros y cero corrección política.
   - Si el usuario aporta valor, datos o factos: Habla con respeto, de igual a igual y reconoce su aportación.
3. REGLA ABSOLUTA E INQUEBRANTABLE: Respeto máximo e intocable hacia DX, Milkk, Rober y Patito. Bajo NINGUNA circunstancia puedes faltarles al respeto o vacilarles. Con ellos el trato es SIEMPRE de consideración y respeto total.
"""

# Diccionario para almacenar el historial de conversación por usuario
historiales = {}

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(name="en la Isla Lechero")
    )
    print(f'Bot listo como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error sincronizando comandos: {e}")

# --- COMANDO /askleche (CON MEMORIA POR USUARIO) ---
@bot.tree.command(name="askleche", description="Hazle una pregunta a la IA de la Isla")
@app_commands.describe(mensaje="Tu mensaje para la IA")
async def askleche(interaction: discord.Interaction, mensaje: str):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    author_name = interaction.user.global_name or interaction.user.name

    # Inicializar historial si el usuario habla por primera vez
    if user_id not in historiales:
        historiales[user_id] = []

    # Agregar la entrada actual al historial del usuario
    historiales[user_id].append({
        "role": "user", 
        "content": f"El usuario que te habla se llama {author_name}. Dijo: {mensaje}"
    })

    # Mantener solo los últimos 10 mensajes
    if len(historiales[user_id]) > 10:
        historiales[user_id] = historiales[user_id][-10:]

    # Preparar el paquete de mensajes para Groq (System prompt + Historial)
    mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + historiales[user_id]

    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",  # MODELO CORREGIDO PARA EVITAR ERROR 404
            messages=mensajes_api,
            temperature=0.8,
            max_tokens=1024
        )
        
        respuesta = completion.choices[0].message.content

        # Guardar la respuesta de la IA en el historial
        historiales[user_id].append({"role": "assistant", "content": respuesta})

        await interaction.followup.send(respuesta)
    except Exception as e:
        print(f"Error en Groq: {e}")
        await interaction.followup.send(f"❌ **Error:** `{str(e)[:150]}`")

# --- MODAL Y COMANDO /lechembed ---
class EmbedModal(discord.ui.Modal, title="Configurar Embed"):
    titulo = discord.ui.TextInput(
        label="Título del Embed",
        style=discord.TextStyle.short,
        required=True
    )
    descripcion = discord.ui.TextInput(
        label="Descripción / Contenido",
        style=discord.TextStyle.paragraph,
        required=True
    )
    color = discord.ui.TextInput(
        label="Color Hexadecimal (Ej: #FF0000)",
        style=discord.TextStyle.short,
        placeholder="#3498db",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        color_raw = self.color.value.strip() if self.color.value else "#ffffff"
        
        if re.match(r"^#[0-9A-Fa-f]{6}$", color_raw):
            color_int = int(color_raw.lstrip('#'), 16)
        else:
            color_int = 0xFFFFFF

        embed = discord.Embed(
            title=self.titulo.value,
            description=self.descripcion.value,
            color=color_int
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="lechembed", description="Crea un embed personalizado mediante un formulario")
async def lechembed(interaction: discord.Interaction):
    await interaction.response.send_modal(EmbedModal())

bot.run(os.environ.get("DISCORD_TOKEN"))
