from os import link
import discord
import yt_dlp as youtube_dl
import asyncio
import datetime as dt
import enum
import requests
import urllib.parse
import urllib.request
import re
import lxml.html
import random
#from apikeys import *
from itertools import islice
from yt_dlp import YoutubeDL
from discord import voice_client
from discord.channel import VoiceChannel
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get
from enum import Enum
from bs4 import BeautifulSoup

#intents = discord.Intents().all()
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = commands.Bot(command_prefix = '-', intents = intents)
queues = {}
playlist = []
universal_url = ""
looped = False
current_song = ""
#YouTube DL options 
ydl_opts = {'format': 'bestaudio/best','noplaylist':'True','postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}] }
#FFMPEG options:
FFMPEG_OPTIONS = {'options': '-vn', 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

def check_queue(ctx, id):
    if id in queues and queues[id]:
        voice = ctx.guild.voice_client
        source = queues[id].pop(0)
        current_song = playlist[0]
        playlist.pop(0)

        titleurl = get_name(current_song)

        embed = discord.Embed(
            title="Playing " + titleurl,
            colour=ctx.author.colour,
        )

        asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), client.loop)
        player = voice.play(source, after=lambda x=None: check_queue(ctx, ctx.message.guild.id))
    else:
        # Handle the case when the queue is empty or the guild ID doesn't exist
        pass

def get_name(url):
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')
    for title in soup.find_all('title'):
        t =  "[" + title.get_text() + "](" + url + ")"
    return t

@client.event
async def on_ready():
    print("Bot is ready woop woop")
    activity = discord.Game(name="-h for help", type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)

def clear_all():
    queues.clear()
    playlist[:] = []

@client.command()
async def print(ctx):
    print(queues)

@client.command()
async def p(ctx, *, url):

    if(ctx.author.voice):

        if(ctx.voice_client):
            print("already in a vc, moving to song")
        else:
            channel = ctx.author.voice.channel
            await channel.connect()
        voice = get(client.voice_clients, guild=ctx.guild)
    
        if(url[0:5] == "https"):
           
            if not voice.is_playing():
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['url']
                voice.play(discord.FFmpegPCMAudio(URL), after=lambda x=None: check_queue(ctx,ctx.message.guild.id))
                voice.is_playing()
                await ctx.send("Playing " + url)

                #########################################
                while voice.is_playing(): #Checks if voice is playing
                    await asyncio.sleep(1) #While it's playing it sleeps for 1 second
                else:
                    await asyncio.sleep(300) #If it's not playing it waits 300 seconds
                    while voice.is_playing(): #and checks once again if the bot is not playing
                        break #if it's playing it breaks
                    else:
                        await voice.disconnect() #if not it disconnects
                        clear_all()
                        await ctx.send("No one was using me so I left")
                    
            else:
                await ctx.send("Already playing song, added " + url + " to queue")
                playlist.append(url)

                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['url']

                source = FFmpegPCMAudio(URL, **FFMPEG_OPTIONS)
                guild_id = ctx.message.guild.id
                if(guild_id in queues):
                    queues[guild_id].append(source)
                else:
                    queues[guild_id] = [source]
                return
        else:
            #do the youtube search thing here
            query_string = urllib.parse.urlencode({'search_query': url})
            htm_content = urllib.request.urlopen('http://www.youtube.com/results?' + query_string)
            search_results = re.findall(r'/watch\?v=(.{11})',htm_content.read().decode())
            url = "http://www.youtube.com/watch?v=" + search_results[0]
            universal_url = url
           
            voice = get(client.voice_clients, guild=ctx.guild)

            if not voice.is_playing():
                
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['url']
                voice.play(discord.FFmpegPCMAudio(URL), after=lambda x=None: check_queue(ctx,ctx.message.guild.id))
                voice.is_playing()
                await ctx.send("Playing " + url)
            
                #########################################
                while voice.is_playing(): #Checks if voice is playing
                    await asyncio.sleep(1) #While it's playing it sleeps for 1 second
                else:
                    await asyncio.sleep(300) #If it's not playing it waits 300 seconds
                    while voice.is_playing(): #and checks once again if the bot is not playing
                        break #if it's playing it breaks
                    else:
                        await voice.disconnect() #if not it disconnects
                        clear_all()
                        await ctx.send("No one was using me so I left")
                        
            else:
                playlist.append(url)
                voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

                voice = get(client.voice_clients, guild=ctx.guild)

                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['url']

                source = FFmpegPCMAudio(URL, **FFMPEG_OPTIONS)
                guild_id = ctx.message.guild.id
                if(guild_id in queues):
                    queues[guild_id].append(source)
                else:
                    queues[guild_id] = [source]
                await ctx.send("Already playing song, added " + url + " to queue")

    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command(pass_context = True)
async def L(ctx):
    if(ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        clear_all()
        await ctx.send("No one wanted me so I left")
    else:
        await ctx.send("I am not in a vc")

@client.command(pass_context = True)
async def pause(ctx):
    if(ctx.author.voice):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send("Paused")
        else:
            await ctx.send("No song is playing")
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command(pass_context = True)
async def resume(ctx):
    if(ctx.author.voice):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if(voice.is_paused()):
            voice.resume()
            await ctx.send("Resumed")
        else:
            await ctx.send("Song isn't paused")
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command()
async def s(ctx):
    if(ctx.author.voice):
        if(playlist == []):
            await ctx.send("There aren't any songs in the queue, go add some")
        else:
            await ctx.send("Playing next song")
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            voice.stop()
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command()
async def q(ctx):
    if(ctx.author.voice):
        embed = discord.Embed(
                title="Whats Next:",
                colour=ctx.author.colour,
                timestamp=dt.datetime.utcnow(),
            )
        embed.set_author(name="Queue")
        
        counter = 1
        for i in playlist:
            embed.add_field(name = counter, value= get_name(i), inline=False)
            counter = counter + 1
        await ctx.send(embed=embed)
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command()
async def r(ctx, number):
    if(ctx.author.voice):
        num = int(number)
        num = num - 1

        url = playlist[num]
        playlist.pop(num)

        id = ctx.message.guild.id
        source = queues[id].pop(num)

        await ctx.send("Removed " + get_name(url) + " from the queue")
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command()
async def clear(ctx):
    if(ctx.author.voice):
        clear_all()
        embed = discord.Embed(
            title="Cleared the queue. You're welcome",
            colour=ctx.author.colour,  
        )     

        await ctx.send(embed=embed)
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command()
async def h(ctx):
    embed = discord.Embed(
            title="HOW TO USE BOTIFY:",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow(),
        )
    embed.set_author(name="Help")

    embed.add_field(name = "Play a song", value= "-p + (song name or youtube/soundcloud/spotify link) [Note: Whatever you do, DO NOT PASTE A LINK OF A PLAYLIST! It breaks and Tej is working on a solution]", inline=False)
    embed.add_field(name = "Pause the song", value= "-pause", inline=False)
    embed.add_field(name = "Resume the song", value= "-resume", inline=False)
    embed.add_field(name = "Skip to next song", value= "-s", inline=False)
    embed.add_field(name = "View Queue", value= "-q", inline=False)
    embed.add_field(name = "Remove song from Queue", value= "-r + (# of the song in the queue)", inline=False)
    embed.add_field(name = "Clear the Queue", value= "-clear", inline=False)
    embed.add_field(name = "Talk to ChatGPT", value= "-chat + (the message you want to tell to the bot)", inline=False)
    embed.add_field(name = "Kill someone or something ;)", value= "-kill + whatever you want", inline=False)
    await ctx.send(embed=embed)
    
import openai,os,sys
openai.api_key = "hidden =)"

@client.command()
async def chat(ctx, *, url):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]
    
    message = url + " Make the response less than 2000 characters"
    if message:
        messages.append( 
                {"role": "user", "content": message},
        )
        chat_completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
        )
    answer = chat_completion.choices[0].message.content
    length = len(answer)
    print(length)
    
    await ctx.reply(answer)


client.run('hidden =)')

