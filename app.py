import discord, sqlite3, json, random, string, asyncio, math
from datetime import date
from discord.ext import tasks
from discord.ext import commands

token = ""
bot = commands.Bot(command_prefix="!", intents=discord.Intents().all())
conn = sqlite3.connect("database.db")
bot.cursor = conn.cursor()

cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS guild_starboard (star_message_id text, bot_message_id text)")
cursor.execute("CREATE TABLE IF NOT EXISTS guild_warns (user_id text, warn_id text, expiry text, reason text)")
cursor.execute("CREATE TABLE IF NOT EXISTS guild_xp (user_id text, xp int)")
conn.commit()

def save():
    opts["stars"] = opt_stars
    opts["warns"] = opt_warns
    opts["repeats"] = opt_repeats

    file = open("opts.json", "w")
    json.dump(opts, file)
    file.close()

file = open("opts.json")
opts = json.load(file)
file.close()

opt_stars = opts["stars"]
opt_warns = opts["warns"]
opt_repeats = opts["repeats"]
xp_cache = []
spam_cache = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    init = False
    for object in spam_cache:
        if message.author.id == object["id"]:
            init = True

            if message.content.lower() == object["last"]: object["repeats"] += 1
            else: object["repeats"] = 0

            if object["repeats"] >= opt_repeats - 1:
                object["repeats"] = opt_repeats - 4

                today = date.today().strftime("%d-%m-%Y")
                month = int(today.split("-")[1]) + 1
                if month == 13: month = 1
                expiry = today.split("-")[0] + "-" + str(month) + "-" + today.split("-")[2]

                warn_id = "".join(random.choices(string.digits, k=4))
                cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE warn_id = ?", (warn_id,))
                while cursor.fetchone()[0] == 1:
                    warn_id = "".join(random.choices(string.digits, k=4))
                    cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE warn_id = ?", (warn_id,))

                cursor.execute("INSERT INTO guild_warns VALUES (?, ?, ?, ?)", (str(message.author.id), str(warn_id), expiry, "AntiSpam"))
                conn.commit()

                cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE user_id = ?", (str(message.author.id),))
                warns = cursor.fetchone()[0]

                await message.channel.send(embed=discord.Embed(description=f"Warned {message.author} with reason AntiSpam. They now have {warns} warn(s).\n\nWarn ID: {warn_id}"))
                try: 
                    await message.author.send(embed=discord.Embed(title=f"You were warned in The Hangout.", description=f"Warned with reason AntiSpam. Sorry!"))
                except discord.HTTPException: 
                    print(f"wasn\'t able to dm {message.author}")

                if warns >= opt_warns:
                    try: 
                        await message.author.send(embed=discord.Embed(title=f"You were banned from The Hangout.", description=f"Banned for reaching {warns} warns. Sorry!"))
                    except discord.HTTPException: 
                        print(f"wasn\'t able to dm {message.author}")

                    await message.author.ban(reason=f"Reached {warns} warns.")
                    await message.channel.send(embed=discord.Embed(description=f"Banned {message.author} for reaching {warns} warns."))

            object["last"] = message.content.lower()

    if init == False: spam_cache.append({"id": message.author.id, "last": message.content.lower(), "repeats": 0})

    points = math.ceil(len(message.content) / 100)

    init = False
    cursor.execute("SELECT user_id FROM guild_xp")
    for object in cursor.fetchall():
        if message.author == object[0]: init = True
    if init == False:
        cursor.execute("INSERT INTO guild_xp VALUES (?, ?)", (str(message.author.id), 0))
        conn.commit()

    for object in xp_cache:
        if message.author.id == object["id"]:
            cursor.execute("SELECT xp FROM guild_xp WHERE user_id = ?", (str(message.author.id),))
            xp = cursor.fetchone()[0]

            if (xp + object["xp"] < 250) and (xp + object["xp"] + points >= 250):
                await message.author.add_roles(message.guild.get_role(776261971145654303))
                await message.channel.send(embed=discord.Embed(title=f"Level Up, {message.author.name}!", description=f"You now have full media access!"))
            if (xp + object["xp"] < 500) and (xp + object["xp"] + points >= 500):
                await message.author.add_roles(message.guild.get_role(776263004987457546))
                await message.channel.send(embed=discord.Embed(title=f"Level Up, {message.author.name}!", description=f"You now have the Normal role!"))
            if (xp + object["xp"] < 1000) and (xp + object["xp"] + points >= 1000):
                await message.author.add_roles(message.guild.get_role(776263222931488809))
                await message.channel.send(embed=discord.Embed(title=f"Level Up, {message.author.name}!", description=f"You now have the Active role!"))
            if (xp + object["xp"] < 2500) and (xp + object["xp"] + points >= 2500):
                await message.author.add_roles(message.guild.get_role(776263364519133232))
                await message.channel.send(embed=discord.Embed(title=f"Level Up, {message.author.name}!", description=f"You now have the Cool Kid role!"))
            if (xp + object["xp"] < 5000) and (xp + object["xp"] + points >= 5000):
                await message.author.add_roles(message.guild.get_role(776263493413634078))
                await message.channel.send(embed=discord.Embed(title=f"Level Up, {message.author.name}!", description=f"You now have the Beast role!"))

            object["xp"] += points
            await bot.process_commands(message)
            return
    
    xp_cache.append({"id": message.author.id, "xp": points})
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    await bot.get_channel(690644064797851673).send(embed=discord.Embed(title=f"Hey {member.name}!", description="Welcome to the server! Enjoy your stay!"))
    try: 
        await member.send(embed=discord.Embed(title="Welcome to The Hangout!", description="You will receive the member role in 3 minutes. Please read the rules.\n\nChoose a color using !color <id>!\n\nAqua\nGreen\nBlue\nPurple\nPink\nYellow\nOrange\nRed"))
    except discord.HTTPException: 
        pass
    spam_cache.append({"id": member.id, "last": "", "repeats": 0})
    await asyncio.sleep(180)
    await member.add_roles(member.guild.get_role(690644748607815770))

@bot.event
async def on_member_remove(member):
    await bot.get_channel(690644064797851673).send(embed=discord.Embed(title=f"Bye {member.name}!", description="We hope you come back soon!"))

@bot.event
async def on_reaction_add(reaction, user):
    for reaction_2 in reaction.message.reactions:
        if reaction_2.emoji == "⭐":
            if reaction_2.count >= opt_stars:
                cursor.execute("SELECT * FROM guild_starboard WHERE star_message_id = ?", (str(reaction.message.id),))
                message_info = cursor.fetchone()

                if message_info != None:
                    message = await bot.get_channel(785937885995991040).fetch_message(int(message_info[1]))
                    return await message.edit(content=f":star: {reaction_2.count}")

                embed = discord.Embed(description=reaction.message.content)

                try: embed.set_thumbnail(url=reaction.message.attachments[0]["url"])
                except: pass

                embed.set_author(name=reaction.message.author, icon_url=reaction.message.author.avatar_url)
                embed.set_footer(text=reaction.message.channel)
                message = await bot.get_channel(785937885995991040).send(f":star: {reaction_2.count}", embed=embed)

                cursor.execute("INSERT INTO guild_starboard VALUES (?, ?)", (str(reaction.message.id), str(message.id)))
                conn.commit()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): 
        return
    elif isinstance(error, commands.BadArgument): 
        return await ctx.send(embed=discord.Embed(title="Error!", description="Invalid argument(s)!"))
    elif isinstance(error, commands.MissingRequiredArgument): 
        return await ctx.send(embed=discord.Embed(title="Error!", description=f"Missing argument `{error.param.name}`!"))
    else: 
        return await ctx.send(embed=discord.Embed(title="Error!", description=f"```py{error}```"))

@bot.command(name="color")
async def _color(ctx, color_choice:str):
    if color_choice == "list": return await ctx.send(embed=discord.Embed(description="Colors\n\nAqua\nGreen\nBlue\nPurple\nPink\nYellow\nOrange\nRed"))
    colors = [{"name": "Aqua", "id": 776257095107477516}, {"name": "Green", "id": 776257402890485791}, {"name": "Blue", "id": 776257469231398933}, {"name": "Purple", "id": 776257638241402920}, {"name": "Pink", "id": 776257687398383637}, {"name": "Yellow", "id": 776257777328455700}, {"name": "Orange", "id": 776257827328491571}, {"name": "Red", "id": 776257876842905600}]

    guild = bot.get_guild(690644064797851669)
    member = guild.get_member(ctx.author.id)

    id = None
    for object in colors:
        for role in member.roles:
            if role.id == object["id"]: await member.remove_roles(guild.get_role(object["id"]))
        if color_choice == object["name"]: id = object["id"]
    if id == None: return await ctx.send(embed=discord.Embed(description="Invalid color!"))

    await member.add_roles(guild.get_role(id))
    await ctx.send(embed=discord.Embed(description="Changed color."))

@bot.command()
@commands.has_role("Admin")
async def set(ctx, variable:str, count:int):
    if variable == "stars":
        global opt_stars
        opt_stars = count
        save()

        await ctx.send(embed=discord.Embed(description=f"Stars set to {opt_stars}."))
    if variable == "warns":
        global opt_warns
        opt_warns = count
        save()

        await ctx.send(embed=discord.Embed(description=f"Warns set to {opt_warns}."))
    if variable == "repeats":
        global opt_repeats
        opt_repeats = count
        save()

        await ctx.send(embed=discord.Embed(description=f"Repeated message warning set to {opt_repeats}."))

@bot.command()
@commands.has_role("Staff")
async def warn(ctx, member:discord.Member, *, reason:str):
    today = date.today().strftime("%d-%m-%Y")
    month = int(today.split("-")[1]) + 1
    if month == 13: month = 1
    expiry = today.split("-")[0] + "-" + str(month) + "-" + today.split("-")[2]

    warn_id = "".join(random.choices(string.digits, k=4))
    cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE warn_id = ?", (warn_id,))
    while cursor.fetchone()[0]:
        warn_id = "".join(random.choices(string.digits, k=4))
        cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE warn_id = ?", (warn_id,))

    cursor.execute("INSERT INTO guild_warns VALUES (?, ?, ?, ?)", (str(member.id), str(warn_id), expiry, reason))
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE user_id = ?", (str(member.id),))
    warns = cursor.fetchone()[0]

    await ctx.send(embed=discord.Embed(description=f"Warned {member} with reason {reason}. They now have {warns} warn(s).\n\nWarn ID: {warn_id}"))
    try:
        await member.send(embed=discord.Embed(title=f"You were warned in The Hangout.", description=f"Warned with reason {reason}. Sorry!"))
    except discord.HTTPException: 
        await ctx.send(f"Was not able to DM {member}")

    if warns >= opt_warns:
        try: 
            await member.ban(reason=f"Reached {warns} warns.")
            await member.send(embed=discord.Embed(title=f"You were banned from The Hangout.", description=f"Banned for reaching {warns} warns. Sorry!"))
            await ctx.send(embed=discord.Embed(description=f"Banned {member} for reaching {warns} warns."))
        except discord.HTTPException: 
            await ctx.send(f"Couldn\'t ban {member}. Maybe i\'m missing permissions?")


            

@bot.command()
@commands.has_role("Staff")
async def unwarn(ctx, warn_id:int):
    cursor.execute("SELECT COUNT(*) FROM guild_warns WHERE warn_id = ?", (str(warn_id),))
    if not cursor.fetchone()[0]: return await ctx.send(embed=discord.Embed(description="Invalid warn ID!"))

    cursor.execute("DELETE FROM guild_warns WHERE warn_id = ?", (str(warn_id),))
    conn.commit()

    await ctx.send(embed=discord.Embed(description=f"Deleted warn with ID {warn_id}."))

@bot.command()
async def warnings(ctx, member:discord.Member=None):
    if member is None: member = ctx.author

    cursor.execute("SELECT * FROM guild_warns WHERE user_id = ?", (str(member.id),))
    content = ""

    for member_warn in cursor.fetchall(): content += f"Reason: {member_warn[3]} | Warn ID: {member_warn[1]} | Expires: {member_warn[2]}\n"
    if not content: content = "No warns!"

    await ctx.send(embed=discord.Embed(description=f"Warns for {member}\n\n{content}"))

@bot.command()
@commands.has_role("Staff")
async def lock(ctx, channel:discord.TextChannel=None, minutes:int=None):
    if not channel: channel = ctx.channel

    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=discord.Embed(description="Locked channel."))

    if minutes != None:
        await asyncio.sleep(minutes * 60)
        await channel.set_permissions(ctx.guild.default_role, overwrite=None)
        await ctx.send(embed=discord.Embed(description="Unlocked channel."))

@bot.command()
@commands.has_role("Staff")
async def unlock(ctx, channel:discord.TextChannel=None):
    if not channel: channel = ctx.channel

    await channel.set_permissions(ctx.guild.default_role, overwrite=None)
    await ctx.send(embed=discord.Embed(description="Unlocked channel."))

@bot.command()
@commands.has_role("Staff")
async def purge(ctx, count:int):
    try:
        await ctx.channel.purge(limit=count)
        await ctx.send(embed=discord.Embed(description=f"Purged {count} messages."))
    except discord.HTTPException as e:
        await ctx.send(f'Error: {e} (try a smaller search?)')

@bot.command()
@commands.has_role("Staff")
async def mute(ctx, member:discord.Member, minutes:int=None):
    await member.add_roles(ctx.guild.get_role(786317238487351306))
    await ctx.send(embed=discord.Embed(description=f"Muted {member}."))

    if minutes != None:
        await asyncio.sleep(minutes * 60)
        await member.remove_roles(ctx.guild.get_role(786317238487351306))
        await ctx.send(embed=discord.Embed(description=f"Unmuted {member}."))

@bot.command()
@commands.has_role("Staff")
async def unmute(ctx, member:discord.Member):
    await member.remove_roles(ctx.guild.get_role(786317238487351306))
    await ctx.send(embed=discord.Embed(description=f"Unmuted {member}."))

@bot.command()
@commands.has_role("Staff")
async def kick(ctx, member:discord.Member, *, reason:str):
    msg = f"Kicked {member} with reason {reason}."
    try: 
        await member.ban(reason=reason)
    except discord.HTTPException:
        await ctx.send(f"Was\'nt able to kick {member}")
    finally:
        try:
            await member.send(embed=discord.Embed(title=f"You were kicked from The Hangout.", description=f"Kicked with reason {reason}. Sorry!"))
         except discord.HTTPException:
           msg = f"Kicked {member} with reason {reason}. Info: Was not able to DM user."
     await ctx.send(embed=discord.Embed(description=msg)

@bot.command()
@commands.has_role("Staff")
async def ban(ctx, member:discord.Member, *, reason:str):
    msg = f"Banned {member} with reason {reason}."
    try: 
        await member.ban(reason=reason)
    except discord.HTTPException:
        await ctx.send(f"Was\'nt able to ban {member}")
    finally:
        try:
            await member.send(embed=discord.Embed(title=f"You were banned from The Hangout.", description=f"Banned with reason {reason}. Sorry!"))
         except discord.HTTPException:
           msg = f"Banned {member} with reason {reason}. Info: Was not able to DM user."
     await ctx.send(embed=discord.Embed(description=msg



@bot.command(name="xp")
async def _xp(ctx, member:discord.Member=None):
    if member is None: member = ctx.author

    cursor.execute("SELECT xp FROM guild_xp WHERE user_id = ?", (str(member.id),))
    xp = cursor.fetchone()[0]

    await ctx.send(embed=discord.Embed(title="XP", description=f"You have {xp} xp."))

@tasks.loop(seconds=10)
async def activity_loop():
    for object in xp_cache:
        cursor.execute("SELECT xp FROM guild_xp WHERE user_id = ?", (str(object["id"]),))
        xp = cursor.fetchone()[0] + object["xp"]
        object["xp"] = 0
        cursor.execute("UPDATE guild_xp SET xp = ? WHERE user_id = ?", (xp, str(object["id"])))
        
    cursor.execute("DELETE FROM guild_warns WHERE expiry = ?", (date.today().strftime("%d-%m-%Y"),))
    conn.commit()

activity_loop.start()
bot.run(token, reconnect=True)
