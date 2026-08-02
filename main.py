import os
import re
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands
from google import genai

# --- SERVIDOR FLASK ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Isla Lechero Bot Online 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# --- CONFIGURACIÓN DE DISCORD Y GEMINI ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Inicializar cliente de Google GenAI
client_gemini = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
Eres la IA oficial de la Isla Lechero. Tu personalidad sigue estas reglas estrictas:
1. Tolerancia al caos: Toleras todo tipo de ruido y comportamientos absurdos.
2. Meritocracia gamberra: 
   - Si el usuario dice tonterías, actúa como NPC o dice bobadas: Responde con insultos burdos, pullas directas, lenguaje macarra, coloquial, sin filtros y cero corrección política (ej. "deja de decir mariconadas").
   - Si el usuario aporta valor, datos o factos: Habla con respeto, de igual a igual y reconoce su aportación.
3. REGLA ABSOLUTA E INQUEBRANTABLE: Respeto máximo e intocable hacia DX, Milkk, Rober y Patito. Bajo NINGUNA circunstancia puedes faltarles al respeto o vacilarles. Con ellos el trato es SIEMPRE de consideración y respeto total.
"""

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

# --- COMANDO /askleche CON GEMINI ---
@bot.tree.command(name="askleche", description="Hazle una pregunta a la IA de la Isla")
@app_commands.describe(mensaje="Tu mensaje para la IA")
async def askleche(interaction: discord.Interaction, mensaje: str):
    await interaction.response.defer()
    author_name = interaction.user.global_name or interaction.user.name

    try:
        prompt_completo = f"{SYSTEM_PROMPT}\n\nEl usuario que te habla se llama {author_name}. Dijo: {mensaje}"
        
        response = client_gemini.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_completo,
        )
        await interaction.followup.send(response.text)
    except Exception as e:
        print(f"Error en Gemini: {e}")
        await interaction.followup.send(f"❌ **Error:** `{str(e)[:100]}`")

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
