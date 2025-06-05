import discord
from discord.ext import commands
import youtube_dl
import ffmpeg
import asyncio
from discord import FFmpegPCMAudio

import spotipy
from spotipy.oauth2 import SpotifyOAuth

intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = 'http://localhost/callback'

# Kimlik doğrulama işlemi
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri))

@bot.event
async def on_ready():
    print(f'Bot olarak giriş yapıldı: {bot.user.name}')

@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    voice_client = await channel.connect()

@bot.command()
async def leave(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()

@bot.command()
async def play(ctx, url):
    voice_client = ctx.voice_client
    if not voice_client:    
        channel = ctx.author.voice.channel
        voice_client = await channel.connect()

    voice_channel = ctx.author.voice.channel
    if voice_channel:
        voice_client = await voice_channel.connect()
        source = FFmpegPCMAudio(url)
        voice_client.play(source)
    else:
        await ctx.send("Bir sesli kanalda değilsiniz.")

@bot.command()
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()

# Kullanıcıların spam yaptığını takip etmek için bir sözlük oluşturuyoruz
spam_tracker = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # kullanıcının spam takibini yapmak için bir kullanıcı anahtarı oluşturuyoruz
    user_key = str(message.author.id)

    if user_key not in spam_tracker:
        # yeni bir kullanıcı mesajı, sözlüğe ekliyoruz
        spam_tracker[user_key] = [message.content]
    else:
        # Kullanıcının son 5 mesajını kontrol ediyoruz
        user_messages = spam_tracker[user_key]
        user_messages.append(message.content)
        if len(user_messages) > 5:
            user_messages.pop(0)  # En eski mesajı kaldır

        # kullanıcının son 5 mesajının aynı olduğunu kontrol ediyoruz
        if all(msg == user_messages[0] for msg in user_messages):
            await message.channel.send(f"{message.author.mention} Spam yapmayı bırak!")

    await bot.process_commands(message) 

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f'{member.name}#{member.discriminator} banlandı.')

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Bu komutu kullanma yetkiniz yok.')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('Geçerli bir üye belirtin.')
    else:
        await ctx.send('Bir hata oluştu.')

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
