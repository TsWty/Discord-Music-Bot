import discord
import os
from discord.ext import commands
import youtube_dl
import ffmpeg
import asyncio
from discord import FFmpegPCMAudio
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Tüm müzikle ilgili ayarlar
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            
            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()
                if self.vc is None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="play", aliases=["p", "playing"], help="Plays a selected song from YouTube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
            return
        
        if self.is_paused:
            self.vc.resume()
            return

        song = self.search_yt(query)
        if type(song) == type(True):
            await ctx.send("Could not download the song. Incorrect format, try another keyword. This could be due to playlist or livestream format.")
        else:
            await ctx.send("Song added to the queue")
            self.music_queue.append([song, voice_channel])

            if not self.is_playing:
                await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx):
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            self.vc.pause()
            await ctx.send("Paused the song")
        elif self.is_paused:
            self.is_paused = False
            self.vc.resume()
            await ctx.send("Resumed the song")
        else:
            await ctx.send("No song is currently playing")

    @commands.command(name="skip", aliases=["s"], help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc is not None and self.vc.is_playing():
            self.vc.stop()
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx):
        if len(self.music_queue) > 0:
            retval = ""
            for i in range(0, min(5, len(self.music_queue))):
                retval += self.music_queue[i][0]['title'] + "\n"
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.vc is not None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kicks the bot from the voice channel")
    async def leave(self, ctx):
        if self.vc is not None:
            await self.vc.disconnect()
            self.is_playing = False
            self.is_paused = False

def setup(bot):
    bot.add_cog(MusicCog(bot))
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
