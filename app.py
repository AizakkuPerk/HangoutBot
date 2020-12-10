import discord, sqlite3, json, random
from datetime import date
from discord.ext import tasks
from discord.ext import commands

token = ""
bot = commands.Bot(command_prefix="h.", intents=discord.Intents().all())
conn = sqlite3.connect("database.db")

cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS guild_starboard (star_message_id text, bot_message_id text)")
cursor.execute("CREATE TABLE IF NOT EXISTS guild_warns (user_id text, warn_id text, expiry text, reason text)")
conn.commit()

def save():
    opts["stars"] = opt_stars
    opts["warns"] = opt_warns

    file = open("opts.json", "w")
    json.dump(opts, file)
    file.close()

def mod(member):
    for role in member.roles:
        if role.id == 690644743054426162: return True
        elif role.id == 690644715951095888: return True
    return False

def admin(member):
    for role in member.roles:
        if role.id == 690644715951095888: return True
    return False

file = open("opts.json")
opts = json.load(file)
file.close()

opt_stars = opts["stars"]
opt_warns = opts["warns"]
activity_timer = 0

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    await bot.get_channel(690644064797851673).send(embed=discord.Embed(title=f"Hey {member.name}!", description="Welcome to the server! Enjoy your stay!"))
    await member.send(embed=discord.Embed(title="Welcome to The Hangout!", description="Please choose a color using h.set color <id>!\n\n:one: Aqua\n:two: Green\n:three: Blue\n:four: Purple\n:five: Pink\n:six: Yellow\n:seven: Orange\n:eight: Red"))

@bot.event
async def on_member_remove(member):
    await bot.get_channel(690644064797851673).send(embed=discord.Embed(title=f"Bye {member.name}!", description="We hope you come back soon!"))

@bot.event
async def on_reaction_add(reaction, user):
    cursor = conn.cursor()

    for reaction_2 in reaction.message.reactions:
        if reaction_2.emoji == "⭐":
            if reaction_2.count >= opt_stars:
                cursor.execute("SELECT * FROM guild_starboard WHERE star_message_id = ?", (str(reaction.message.id),))
                message_info = cursor.fetchone()
                if message_info == None:
                    embed = discord.Embed(description=reaction.message.content)
                    embed.set_author(name=reaction.message.author, icon_url=reaction.message.author.avatar_url)
                    embed.set_footer(text="Starboard")
                    message = await bot.get_channel(785937885995991040).send(f":star: {reaction_2.count}", embed=embed)

                    cursor.execute("INSERT INTO guild_starboard VALUES (?, ?)", (str(reaction.message.id), str(message.id)))
                    conn.commit()
                else:
                    message = await bot.get_channel(785937885995991040).fetch_message(int(message_info[1]))
                    await message.edit(content=f":star: {reaction_2.count}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): await ctx.send(embed=discord.Embed(description="Command not found!"))
    elif isinstance(error, commands.BadArgument): await ctx.send(embed=discord.Embed(description="Invalid member/channel!"))
    else: await ctx.send(embed=discord.Embed(description=f"Error!```{error}```"))

@bot.command()
async def set(ctx, c:str=None, count:int=None):
    if c == None: return await ctx.send(embed=discord.Embed(description="Please specify an option!\n\nh.set <option>\n\ncolor\nstars\nwarns"))
    if count == None: return await ctx.send(embed=discord.Embed(description="Please specify the amount/ID!"))

    if c == "color":
        colors = [776257095107477516, 776257402890485791, 776257469231398933, 776257638241402920, 776257687398383637, 776257777328455700, 776257827328491571, 776257876842905600]

        guild = bot.get_guild(690644064797851669)
        member = guild.get_member(ctx.author.id)

        for color in colors:
            for role in member.roles:
                if color == role.id: await member.remove_roles(guild.get_role(color))

        await member.add_roles(guild.get_role(colors[count - 1]))
        await ctx.send(embed=discord.Embed(description="Changed color."))
    if c == "stars":
        if admin(ctx.author):
            global opt_stars
            opt_stars = count
            save()

            await ctx.send(embed=discord.Embed(description=f"Stars set to {opt_stars}."))
        else:
            await ctx.send(embed=discord.Embed(description="You need to be an admin to do this!"))
    if c == "warns":
        if admin(ctx.author):
            global opt_warns
            opt_warns = count
            save()

            await ctx.send(embed=discord.Embed(description=f"Warns set to {opt_warns}."))
        else:
            await ctx.send(embed=discord.Embed(description="You need to be an admin to do this!"))

@bot.command()
async def warn(ctx, member:discord.Member, *, reason:str=None):
    cursor = conn.cursor()

    if mod(ctx.author):
        if reason == None: await ctx.send(embed=discord.Embed(description="Please specify a reason!"))

        today = date.today().strftime("%d-%m-%Y")
        month = int(today.split("-")[1]) + 1
        if month == 13: month = 1
        expiry = today.split("-")[0] + "-" + str(month) + "-" + today.split("-")[2]

        warn_id = random.randint(1000000000000000, 9999999999999999)

        cursor.execute("INSERT INTO guild_warns VALUES (?, ?, ?, ?)", (str(member.id), str(warn_id), expiry, reason))
        conn.commit()

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE user_id = ?", (str(member.id),))
        warns = cursor.fetchone()[0]

        await ctx.send(embed=discord.Embed(description=f"Warned {member} with reason {reason}. They now have {warns} warn(s).\n\nWarn ID: {warn_id}"))
        await member.send(embed=discord.Embed(title=f"You were warned in The Hangout.", description=f"Warned with reason {reason}. Sorry!"))

        if warns >= opt_warns:
            await member.send(embed=discord.Embed(title=f"You were banned from The Hangout.", description=f"Banned for reaching {warns} warns. Sorry!"))

            await member.ban(reason=f"Reached {warns} warns.")
            await ctx.send(embed=discord.Embed(description=f"Banned {member} for reaching {warns} warns."))
    else:
        await ctx.send(embed=discord.Embed(description="You need to be a mod to do this!"))

@bot.command()
async def unwarn(ctx, warn_id:str=None):
    cursor = conn.cursor()

    if mod(ctx.author):
        if warn_id == None: return await ctx.send(embed=discord.Embed(description="Please specify a warn ID!"))
    
        cursor.execute("DELETE FROM guild_warns WHERE warn_id = ?", (warn_id,))
        conn.commit()

        await ctx.send(embed=discord.Embed(description=f"Deleted warn with ID {warn_id}"))
    else:
        await ctx.send(embed=discord.Embed(description="You need to be a mod to do this!"))

@bot.command()
async def warnlist(ctx, member_id:int=None):
    if member_id == None: return await ctx.send(embed=discord.Embed(description="Please specify a member ID!"))

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM guild_warns WHERE user_id = ?", (str(member_id),))
    content = ""
    for member_warn in cursor.fetchall():
        content += f"Reason: {member_warn[3]} | ID: {member_warn[1]} | Expires: {member_warn[2]}\n"
    if not content: content = "No warns!"
    try: member_name = bot.get_user(member_id).name
    except: member_name = "Invalid User"
    await ctx.send(embed=discord.Embed(description=f"Warns for {member_name}\n\n{content}"))

@bot.command()
async def lock(ctx, channel:discord.TextChannel=None):
    if mod(ctx.author):
        if channel == None: channel = ctx.channel
    
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(embed=discord.Embed(description="Locked channel."))
    else:
        await ctx.send(embed=discord.Embed(description="You need to be a mod to do this!"))

@bot.command()
async def unlock(ctx, channel:discord.TextChannel=None):
    if mod(ctx.author):
        if channel == None: channel = ctx.channel

        await channel.set_permissions(ctx.guild.default_role, overwrite=None)
        await ctx.send(embed=discord.Embed(description="Unlocked channel."))
    else:
        await ctx.send(embed=discord.Embed(description="You need to be a mod to do this!"))

@bot.command()
async def kick(ctx, member:discord.Member, *, reason:str=None):
    if mod(ctx.author):
        if reason == None: return await ctx.send(embed=discord.Embed(description="Please specify a reason!"))

        await member.kick(reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Kicked {member} with reason {reason}."))
    else:
        await ctx.send(embed=discord.Embed(description="You need to be a mod to do this!"))

@bot.command()
async def ban(ctx, member:discord.Member, *, reason:str=None):
    if mod(ctx.author):
        if reason == None: return await ctx.send(embed=discord.Embed(description="Please specify a reason!"))

        await member.send(embed=discord.Embed(title=f"You were banned from The Hangout.", description=f"Banned with reason {reason}. Sorry!"))

        await member.ban(reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Banned {member} with reason {reason}."))
    else:
        await ctx.send(embed=discord.Embed(description="You need to be a mod to do this!"))

@tasks.loop(seconds=1.0)
async def activity_loop():
    global activity_timer
    if activity_timer >= 1800:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM guild_warns WHERE expiry = ?", (date.today().strftime("%d-%m-%Y"),))
        conn.commit()

        activity_timer = 0
        activity_loop.restart()
    activity_timer += 1

activity_loop.start()
bot.run(token, reconnect=True)