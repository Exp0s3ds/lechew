import os
import re
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands
import openai

# --- SERVIDOR FLASK (Para mantener activo el bot con UptimeRobot) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Isla Lechero Bot Online 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

# Iniciar Flask en un hilo secundario
threading.Thread(target=run_flask, daemon=True).start()

# --- CONFIGURACIÓN DE DISCORD Y OPENAI ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

api_key = os.environ.get("OPENAI_API_KEY", "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")
client_openai = openai.OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
Eres la IA oficial de la Isla Lechero. Tu personalidad sigue estas reglas strictly:
1. Tolerancia al caos: Toleras todo tipo de ruido y comportamientos absurdos.
2. Meritocracia gamberra: 
   - Si el usuario dice tonterías, actúa como NPC o dice bobadas: Responde con insultos burdos, pullas directas, lenguaje macarra, coloquial, sin filtros y cero corrección política (ej. "deja de decir mariconadas").
   - Si el usuario aporta valor, datos o factos: Habla con respeto, de igual a igual y reconoce su aportación.
3. REGLA ABSOLUTA E INQUEBRANTABLE: Respeto máximo e intocable hacia DX, Milkk, Rober y Patito. Bajo NINGUNA circunstancia puedes faltarles al respeto o vacilarles. Con ellos el trato es SIEMPRE de consideración y respeto total.
"""

# --- EVENTO ON_READY (ESTADO NO MOLESTAR) ---
@bot.event
async def on_ready():
    # Establece el estado en No Molestar (dnd)
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

# --- COMANDO /askleche (CON DIAGNÓSTICO DE ERRORES) ---
@bot.tree.command(name="askleche", description="Hazle una pregunta a la IA de la Isla")
@app_commands.describe(mensaje="Tu mensaje para la IA")
async def askleche(interaction: discord.Interaction, mensaje: str):
    await interaction.response.defer()
    author_name = interaction.user.global_name or interaction.user.name

    try:
        response = client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"El usuario que te habla se llama {author_name}. Dijo: {mensaje}"}
            ]
        )
        await interaction.followup.send(response.choices[0].message.content)
    except openai.AuthenticationError:
        await interaction.followup.send("❌ **Error:** La API Key de OpenAI es inválida o fue revocada.")
    except openai.RateLimitError:
        await interaction.followup.send("❌ **Error:** Te quedaste sin créditos en OpenAI o alcanzaste el límite de peticiones.")
    except Exception as e:
        print(f"Error detallado: {e}")
        await interaction.followup.send(f"❌ **Error desconocido:** `{str(e)[:100]}`")
        
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
        
        # Validar color hex
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

# --- INICIAR BOT ---
bot.run(os.environ.get("DISCORD_TOKEN"))
