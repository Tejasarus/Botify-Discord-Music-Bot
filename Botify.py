from os import link
import discord
import youtube_dl
import asyncio
import datetime as dt
import enum
import requests
import urllib.parse
import urllib.request
import re
import lxml.html
import random
import time
from apikeys import *
from itertools import islice
from youtube_dl import YoutubeDL
from discord import voice_client
from discord.channel import VoiceChannel
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get
from enum import Enum
from bs4 import BeautifulSoup

client = commands.Bot(command_prefix = '-')
#stores the downloaded audio
playlist = []
#stores the url of the videos
playlist_url = []

#YouTube DL options 
YDL_OPTIONS = {'format': 'bestaudio/best','noplaylist':'True','postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}] }
#FFMPEG options:
FFMPEG_OPTIONS = {'options': '-vn', 'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

#when the bot first boots up and is ready, print to console and show online status
@client.event
async def on_ready():
    print("Bot is ready woop woop")
    activity = discord.Game(name="Type -h for help", type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)

#clear all function, clears the playlist
def clear_all():
    playlist = []
    playlist_url = []

#play next song function
def play_next(ctx):
    if playlist != []:

        #get the song and then delete it off of playlist
        url = playlist[0]
        del playlist[0]
        
        url_title = playlist_url[0]
        del playlist_url[0]

        asyncio.run_coroutine_threadsafe(ctx.send("Now playing " + url_title), client.loop)
        #play the song
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url))
        ctx.voice_client.play(source, after=lambda e: play_next(ctx))
        
    else:
        vc = get(client.voice_clients, guild=ctx.guild)
        if not vc.is_playing():
            time.sleep(300) 
            asyncio.run_coroutine_threadsafe(ctx.send("No one was using me so I left"), client.loop)
            asyncio.run_coroutine_threadsafe(vc.disconnect(), client.loop)
            clear_all()

           
#play command
@client.command()
async def p(ctx, *, url):

    #check if user is in vc and if not tell them to join one
    if(ctx.author.voice):

        #get the bot to join the vc that the user is in (if it's not in it already)
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()

        #Play the song the user requested
        
        voice = get(client.voice_clients, guild=ctx.guild)
        
        #check to see if the "url" is actually one or not
        if(url[0:5] == "https"):
            
            #if the bot isn't playing a song then play the song, else add that song to the queue
            if not voice.is_playing():

                #get the audio from the link
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['formats'][0]['url'] 
        
                #play the song
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(URL))
                ctx.voice_client.play(source, after=lambda e: play_next(ctx))
                voice.is_playing()

                #write that it is playing song to the user
                await ctx.send("Playing " + url)

            #if the bot is playing a song, then add the requested song to the queue
            else:
                #tell the user that their song has been added to the queue
                await ctx.send("Already playing song, added " + url + " to queue")

                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['formats'][0]['url'] 

                playlist_url.append(url)
                playlist.append(URL)


        #if the user request is NOT a url, find the best url and play that
        else:
            #find the best url for the text inputted
            query_string = urllib.parse.urlencode({'search_query': url})
            htm_content = urllib.request.urlopen('http://www.youtube.com/results?' + query_string)
            search_results = re.findall(r'/watch\?v=(.{11})',htm_content.read().decode())
            url = "http://www.youtube.com/watch?v=" + search_results[0]

            #if the bot isn't playing a song then play the song, else add that song to the queue
            if not voice.is_playing():

                #get the audio from the link
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['formats'][0]['url'] 
        
                #play the song
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(URL))
                ctx.voice_client.play(source, after=lambda e: play_next(ctx))
                voice.is_playing()

                #write that it is playing song to the user
                await ctx.send("Playing " + url)

            #if the bot is playing a song, then add the requested song to the queue
            else:
                #tell the user that their song has been added to the queue
                await ctx.send("Already playing song, added " + url + " to queue")

                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                URL = info['formats'][0]['url']

                playlist_url.append(url)
                playlist.append(URL)

        #leave after all of the songs are done playing
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
            
    #if user is not in vc, tell them to join one
    else:
        await ctx.send("You are not in a voice channel, so join one!")

#leave command
@client.command(pass_context = True)
async def L(ctx):
    if(ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        clear_all()
        await ctx.send("No wants me so I left")
    else:
        await ctx.send("I am not in a vc")

#join command
@client.command(pass_context = True)
async def J(ctx):
    if(ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

#pause command
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

#resume command
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

#queue command
def get_name(url):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title")
    return title

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
        for i in playlist_url:
            embed.add_field(name = counter, value= get_name(i), inline=False)
            counter = counter + 1
        await ctx.send(embed=embed)
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

#help command
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
    
    await ctx.send(embed=embed)

#clear command
@client.command()
async def clear(ctx):
    if(ctx.author.voice):
        clear_all()
        await ctx.send("Cleared the queue")
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

@client.command()
async def r(ctx, number):
    if(ctx.author.voice):
        index = int(number)
        index = index - 1
        url = playlist_url[index]
        playlist_url.pop(index)
        playlist.pop(index)
        await ctx.send("Removed " + get_name(url) + " from the queue")
    else:
        await ctx.send("You aren't in a voice channel, so join one!")

client.run(OAUTH_TOKEN)