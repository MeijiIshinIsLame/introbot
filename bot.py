import asyncio
import os
import discord
from discord.ext import commands

intents = discord.Intents.all()  # All but the two privileged ones
intents.members = True  # Subscribe to the Members intent
bot = commands.Bot(command_prefix='!', intents=intents,case_insensitive=True)
bot.remove_command('help')

# environment variables
INTRO_CHANNEL_ID = int(os.environ["INTRO_CHANNEL_ID"])
GUILD_ID = int(os.environ["GUILD_ID"])
BOT_TOKEN = os.environ["BOT_TOKEN"]

ONE_MINUTE = 60

async def update_intro_list():
    while True:
        global message_list
        intro_channel = guild.get_channel(INTRO_CHANNEL_ID)

        # gets first post in channel
        message_list = [message_list async for message_list in intro_channel.history(limit=4000,oldest_first=True)]
        await asyncio.sleep(ONE_MINUTE)

########################### HELPERS ########################### 

def is_intro_channel(ctx):
    intro_channel = bot.get_channel(INTRO_CHANNEL_ID)
    return ctx.channel == intro_channel

def is_botadmin(ctx):
    zach_id = 138458225958715392
    return ctx.author.id == zach_id

def is_admintea(ctx):
    tea_id = 800778750459379792
    return ctx.author.id == tea_id

def make_mention_object_by_id(author_id):
    return "<@{}>".format(author_id)

def strip_mention_to_id(target_user):
    return int(target_user.strip("<@").strip(">"))

def is_mention(input):
    return input.startswith("<@")

async def fileify(avatar_url):
    filename = "avatar.jpg"
    await avatar_url.save(filename)
    file = discord.File(fp=filename)
    return file

async def make_embed(ctx, target_user):
    username, message, url= await get_intro(target_user)

#### tea-changes ####
# adjusted it so that the 1024 character limit is now 4096
# embed color pulls from user's role color
# added link to original message
    embed = discord.Embed(title="**{}**".format(username),description="**Intro**\n{}".format(message),color=target_user.color)
    embed.set_thumbnail(url=target_user.avatar_url)
    embed.add_field(name="--", value="[*View original message...*]({})".format(url), inline=False)
    return embed

########################### BOOT ########################### 

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name="!intro [name or mention]"))

    #imagine a world where I didn't have to do this
    #but this has to work on ready so here we are
    global guild
    guild = bot.get_guild(GUILD_ID)

    bot.loop.create_task(update_intro_list())

########################### HELP ############################## 

#### tea-changes ####
# made the help command have some information
@bot.command(name='introHelp', pass_context=True)
async def help_info(msg):
    user = msg.author.id

    if user == bot.user.id:
        return

    embed = discord.Embed(title='Help',description=
    """
Someone asks a question and you'd like some quick insight on their background? Use introbot to help! This bot pulls a user's first message from the introductions channel.

*NOTE: If you would like to change your introduction, you must edit your original message.*

**COMMANDS**
**!intro**
*Use this command followed by the user's name or handle to pull a user's introduction.
You can either mention the user or type their EXACT name as known in the sever.*
EXAMPLE 1: `!intro @tea`
EXAMPLE 2: `!intro tea`

**!dmintro**
*Use this command if you would like introbot to send a user's introduction to you via Direct Message.*

Type `!introHelp` for more information on a command. If there are any problems with this bot, please let a moderator know.
    """,
    color=0x7598ff)
    await msg.send(embed=embed)

    print('help information sent')

########################### COMMANDS ########################### 

@bot.command(name='intro', pass_context=True)
async def get_intro(ctx, *,  target_user):
    if is_intro_channel(ctx):
        return
    else:
        try:
            #target_user = target_user.encode('utf-8')
            print("encoding", target_user)
            if is_mention(target_user):
                target_user = await guild.fetch_member(strip_mention_to_id(target_user))
                print("I tried converting user", target_user)
            else:
                target_user = await string_to_user(target_user) #target user can be a string
            await send_intro(ctx, target_user)
        except Exception as e:
            print(e)
            await ctx.channel.send(content="Could not fetch intro.")

#### tea-changes ####
# fixed so mentions work with dm command
@bot.command(name='dmintro', pass_context=True)
async def get_intro_dm(ctx, *,  target_user):
    print("get_intro_dm",target_user)
    try:
        if is_mention(target_user):
            target_user = await guild.fetch_member(strip_mention_to_id(target_user))
            print("I tried converting user for DM", target_user)
        else:
            target_user = await string_to_user(target_user) #target user can be a string
        await send_intro_by_dm(ctx, target_user)
    except Exception as e:
        print(e)
        if is_intro_channel(ctx):
            await ctx.channel.send(content="Could not fetch intro.")

async def get_intro(target_user):
    for message in message_list:
        if message.author == target_user:
            if target_user.nick:
                return target_user.nick, message.content, message.jump_url
            else:
                return target_user.name, message.content, message.jump_url

async def send_intro_by_dm(ctx, target_user):
    print("send_intro_dm",target_user)
    try:
        embed = await make_embed(ctx, target_user)
        await ctx.author.send(embed=embed)
    #probably too long for embed
    except discord.errors.HTTPException as e:
        print(e)
        username, message, url = await get_intro(target_user)
        introstring = "**{}**\n---------------------------------------\n".format(username)
        introstring += "{}\n---------------------------------------".format(message)
        avatar_file = await fileify(target_user.avatar_url)
        await ctx.author.send(content=introstring, file=avatar_file)
    except Exception as e:
        print(e)
        await ctx.channel.send("Could not fetch intro.")

async def send_intro(ctx, target_user):
    print("send_intro",target_user)
    try:
        embed = await make_embed(ctx, target_user)
        await ctx.channel.send(embed=embed)
    #probably too long for embed
    except discord.errors.HTTPException as e:
        print(e)
        username, message, url = await get_intro(target_user)
        introstring = "**{}**\n---------------------------------------\n".format(username)
        introstring += "{}\n---------------------------------------".format(message)
        avatar_file = await fileify(target_user.avatar_url)
        await ctx.channel.send(content=introstring, file=avatar_file)
    except Exception as e:
        print(e)
        await ctx.channel.send("Could not fetch intro.")

async def string_to_user(string_to_convert):
    string_to_convert = string_to_convert.lower()
    for member in guild.members:
        if string_to_convert == str(member.nick).lower() or string_to_convert == str(member.name).lower():
            return member

########################### CHANGES ############################## 

#### tea-changes ####
# made a changelog for dev things
@bot.command(name='changelog', pass_context=True)
async def help_info(msg):
    user = msg.author.id

    if user == bot.user.id:
        return

    embed = discord.Embed(title='Changelog',color=0x7598ff)
    embed.add_field(name="**introbot (v1.1) - updated 11.20.2022**",
    value=
    """
➢ Changed maximum length of intro from 1024 characters --> 4096 characters
➢ Added link to jump to original message
➢ Fixed bug for !dmintro command
➢ Embed color pulls from user role instead of default
➢ Added !introHelp command to pull up specific commands
➢ Added !changelog to see recent changes

Type `!introHelp` for more information on specific commands.
...
    """,inline=False)
    embed.set_footer(text="If there are any problems with this bot, please let a moderator know.")
    await msg.send(embed=embed)

    print('changelog sent')

########################### OTHER STUFF ########################### 

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    #dont talk to urself bruh
    if message.author.id == bot.user.id:
        return

bot.run(BOT_TOKEN)
#test


####### things tea wants to add #######
# Way to set a specific message as intro,
# if user hasn't set a message, then it will pull earliest message