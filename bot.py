import discord
from discord import app_commands
import sqlite3
from datetime import datetime
from dateutil import parser
import re

# Define the intents including message content intent
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

class MyBot(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

# Initialize the bot with the defined intents
bot = MyBot(intents=intents)

# Database setup
conn = sqlite3.connect('calendar_bot.db')
c = conn.cursor()

def create_tables():
    c.execute('''CREATE TABLE IF NOT EXISTS place_calendars (
        place_name TEXT, 
        date TEXT, 
        time_from TEXT, 
        time_to TEXT, 
        user_id INTEGER, 
        participants TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS command_roles (
        command_name TEXT, 
        role_id INTEGER
    )''')
    conn.commit()

@bot.event
async def on_ready():
    create_tables()
    print(f'Logged in as {bot.user}')

# Helper functions for parsing date and time
def parse_date(date_str):
    try:
        if len(date_str) in [1, 2]:
            today = datetime.today()
            date = datetime(today.year, today.month, int(date_str))
            return date.strftime('%d/%m')
    except ValueError:
        pass
    return None

def parse_time(time_str):
    try:
        # Normalize different separators
        time_str = re.sub(r'[-]', ':', time_str)
        time_obj = parser.parse(time_str)
        return time_obj.strftime('%I:%M %p')
    except ValueError:
        pass
    return None

def role_check(interaction, command_name):
    user_roles = [role.id for role in interaction.user.roles]
    c.execute("SELECT role_id FROM command_roles WHERE command_name = ?", (command_name,))
    command_roles = c.fetchall()
    command_roles = [role[0] for role in command_roles]

    if not command_roles:
        return True

    for role_id in user_roles:
        if role_id in command_roles:
            return True

    return False

@bot.tree.command(name='assign_role', description='Assign a role to a command')
async def assign_role(interaction: discord.Interaction, command_name: str, role: discord.Role):
    if interaction.user.guild_permissions.administrator:
        c.execute("INSERT INTO command_roles (command_name, role_id) VALUES (?, ?)", (command_name, role.id))
        conn.commit()
        await interaction.response.send_message(f'✅ Role "{role.name}" assigned to command "{command_name}".')
    else:
        await interaction.response.send_message('❌ You do not have permission to use this command.')

@bot.tree.command(name='remove_role', description='Remove a role from a command')
async def remove_role(interaction: discord.Interaction, command_name: str, role: discord.Role):
    if interaction.user.guild_permissions.administrator:
        c.execute("DELETE FROM command_roles WHERE command_name = ? AND role_id = ?", (command_name, role.id))
        conn.commit()
        await interaction.response.send_message(f'✅ Role "{role.name}" removed from command "{command_name}".')
    else:
        await interaction.response.send_message('❌ You do not have permission to use this command.')

# Other bot commands (create_place, reserve, delete_place, delete_reservation, show_reservations, list_places, clear_database, etc.)

@bot.tree.command(name='create_place', description='Create a new place calendar')
async def create_place(interaction: discord.Interaction, place_name: str):
    if not role_check(interaction, 'create_place'):
        await interaction.response.send_message('❌ You do not have the required role to use this command.')
        return

    c.execute("SELECT place_name FROM place_calendars WHERE place_name = ?", (place_name,))
    if c.fetchone():
        await interaction.response.send_message(f'❌ Place "{place_name}" already exists.')
    else:
        c.execute("INSERT INTO place_calendars (place_name) VALUES (?)", (place_name,))
        conn.commit()
        await interaction.response.send_message(f'✅ Place calendar "{place_name}" created.')

@bot.tree.command(name='delete_place', description='Delete an existing place calendar')
async def delete_place(interaction: discord.Interaction, place_name: str):
    if not role_check(interaction, 'delete_place'):
        await interaction.response.send_message('❌ You do not have the required role to use this command.')
        return

    c.execute("DELETE FROM place_calendars WHERE place_name = ?", (place_name,))
    conn.commit()
    await interaction.response.send_message(f'🗑️ Place calendar "{place_name}" deleted.')

@bot.tree.command(name='reserve', description='Reserve a time slot on a place calendar')
async def reserve(interaction: discord.Interaction, place_name: str):
    if not role_check(interaction, 'reserve'):
        await interaction.response.send_message('❌ You do not have the required role to use this command.')
        return

    c.execute("SELECT place_name FROM place_calendars WHERE place_name = ?", (place_name,))
    if not c.fetchone():
        await interaction.response.send_message(f'❌ Place "{place_name}" does not exist. Please create it first.')
        return

    await interaction.response.send_message("📅 Please enter the date (d or dd):")
    date_msg = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
    date = parse_date(date_msg.content)

    if not date:
        await interaction.followup.send('❌ Invalid date format. Please enter the day as d or dd.')
        return

    while True:
        await interaction.followup.send("🕒 Please enter the start time (h:m PM/AM, hh:mm PM/AM, h PM/AM, or hh-mm PM/AM):")
        time_from_msg = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
        time_from = parse_time(time_from_msg.content)

        if not time_from:
            await interaction.followup.send('❌ Invalid time format. Please try again.')
            continue

        c.execute("SELECT time_from, time_to FROM place_calendars WHERE place_name = ? AND date = ?", (place_name, date))
        reservations = c.fetchall()
        valid_time_from = True
        time_from_obj = parser.parse(time_from)

        for res in reservations:
            existing_time_from = parser.parse(res[0])
            existing_time_to = parser.parse(res[1])

            if time_from_obj == existing_time_from:
                valid_time_from = False
                await interaction.followup.send("❌ The start time conflicts with an existing reservation. Please enter a different start time.")
                break
            if existing_time_from < time_from_obj < existing_time_to:
                valid_time_from = False
                await interaction.followup.send("❌ The start time is within an existing reservation period. Please enter a different start time.")
                break

        if valid_time_from:
            break

    await interaction.followup.send("🕒 Please enter the end time (h:m PM/AM, hh:mm PM/AM, h PM/AM, or hh-mm PM/AM):")
    time_to_msg = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
    time_to = parse_time(time_to_msg.content)

    if not time_to:
        await interaction.followup.send('❌ Invalid time format. Please try again.')
        return

    await interaction.followup.send("👥 Please mention the participants (separated by spaces):")
    participants_msg = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
    participants = participants_msg.content

    user_id = interaction.user.id
    participants_str = participants.replace(' ', ',')
    c.execute("INSERT INTO place_calendars (place_name, date, time_from, time_to, user_id, participants) VALUES (?, ?, ?, ?, ?, ?)",
              (place_name, date, time_from, time_to, user_id, participants_str))
    conn.commit()
    await interaction.followup.send(f'✅ Reserved {place_name} on {date} from {time_from} to {time_to} with participants {participants_str}.')

@bot.tree.command(name='delete_reservation', description='Delete an existing reservation')
async def delete_reservation(interaction: discord.Interaction, place_name: str, date: str, time_from: str):
    if not role_check(interaction, 'delete_reservation'):
        await interaction.response.send_message('❌ You do not have the required role to use this command.')
        return

    parsed_date = parse_date(date)
    parsed_time_from = parse_time(time_from)

    if not parsed_date or not parsed_time_from:
        await interaction.response.send_message('❌ Invalid date or time format.')
        return

    c.execute("DELETE FROM place_calendars WHERE place_name = ? AND date = ? AND time_from = ?", (place_name, parsed_date, parsed_time_from))
    conn.commit()
    await interaction.response.send_message(f'🗑️ Reservation for {place_name} on {parsed_date} from {parsed_time_from} deleted.')

@bot.tree.command(name='show_reservations', description='Show all reservations for a place calendar')
async def show_reservations(interaction: discord.Interaction, place_name: str):
    c.execute("SELECT date, time_from, time_to, user_id, participants FROM place_calendars WHERE place_name=?", (place_name,))
    reservations = c.fetchall()

    if not reservations:
        await interaction.response.send_message(f'❌ No reservations for {place_name}.')
    else:
        embed = discord.Embed(title=f'Reservations for {place_name}', color=discord.Color.blue())
        for res in reservations:
            if all(res):
                user_id = res[3]
                try:
                    user = await bot.fetch_user(user_id)
                    user_name = user.name
                except:
                    user_name = "Unknown User"

                embed.add_field(name=f'Date: {res[0]}', value=f'From: {res[1]} To: {res[2]}\nBy: {user_name}\nParticipants: {res[4]}', inline=False)

        await interaction.response.send_message(embed=embed)

@bot.tree.command(name='list_places', description='List all available places')
async def list_places(interaction: discord.Interaction):
    c.execute("SELECT DISTINCT place_name FROM place_calendars")
    places = c.fetchall()

    if not places:
        await interaction.response.send_message(f'❌ No places found.')
    else:
        response = 'Available places:\n' + '\n'.join([place[0] for place in places])
        await interaction.response.send_message(response)

@bot.tree.command(name='clear_database', description='Clear the entire database')
async def clear_database(interaction: discord.Interaction):
    await interaction.response.send_message('⚠️ Are you sure you want to clear the entire database? Reply with "yes" to confirm.')

    confirmation_msg = await bot.wait_for('message', check=lambda m: m.author == interaction.user and m.content.lower() == 'yes')
    if confirmation_msg:
        c.execute("DELETE FROM place_calendars")
        conn.commit()
        await interaction.followup.send('🗑️ The database has been cleared.')

@bot.event
async def on_new_month():
    today = datetime.today()
    if today.day == 1:
        c.execute("DELETE FROM place_calendars")
        conn.commit()
        print("Cleared reservations for the new month.")


bot.run('YOUR_BOT_TOKEN')
