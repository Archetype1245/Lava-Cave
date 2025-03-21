import discord
from discord.ext import commands
from discord import app_commands
import os

# Set your GitHub username and repository name here.
GITHUB_USERNAME = "Archetype1245"
REPO_NAME = "Lava-Cave"
GITHUB_BASE_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}"
ALLOWED_CHANNELS = {928807944487841842, 1352712382769664010}  # Replace with your channel's ID (an integer)
VIEW_TIMEOUT = None

# ---------------------------
# Floor Selection View (with Pagination)
# ---------------------------
class FloorSelectionView(discord.ui.View):
    def __init__(self, floors, current_page=0, items_per_page=20):
        super().__init__(timeout=60)
        self.floors = floors  # List of floor numbers (1-50)
        self.current_page = current_page
        self.items_per_page = items_per_page
        self.generate_buttons()  # Build the initial set of buttons

    def generate_buttons(self):
        # Clear any previously added components.
        self.clear_items()

        start = self.current_page * self.items_per_page
        end = start + self.items_per_page

        # Create a button for each floor on the current page.
        for floor in self.floors[start:end]:
            button = discord.ui.Button(label=str(floor), style=discord.ButtonStyle.primary)

            async def floor_callback(interaction: discord.Interaction, floor=floor):
                # Build the URL for the merged image from GitHub Pages.
                merged_url = f"{GITHUB_BASE_URL}/merged_images/merged-floor-{floor}.png"
                embed = discord.Embed(title=f"Floor {floor} Layouts")
                embed.set_image(url=merged_url)
                await interaction.response.edit_message(
                    content=f"Selected floor {floor}. Choose a layout:",
                    embed=embed,
                    view=LayoutSelectionView(floor)
                )

            button.callback = floor_callback
            self.add_item(button)

        # Add "Prev" button if not on the first page.
        if self.current_page > 0:
            prev_button = discord.ui.Button(label="Prev", style=discord.ButtonStyle.secondary)

            async def prev_callback(interaction: discord.Interaction):
                self.current_page -= 1
                self.generate_buttons()  # Regenerate buttons for new page
                await interaction.response.edit_message(view=self)

            prev_button.callback = prev_callback
            self.add_item(prev_button)

        # Add "Next" button if there are more floors.
        if end < len(self.floors):
            next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary)

            async def next_callback(interaction: discord.Interaction):
                self.current_page += 1
                self.generate_buttons()  # Regenerate buttons for new page
                await interaction.response.edit_message(view=self)

            next_button.callback = next_callback
            self.add_item(next_button)

# ---------------------------
# Layout Selection View
# ---------------------------
class LayoutSelectionView(discord.ui.View):
    def __init__(self, floor):
        super().__init__(timeout=60)
        self.floor = floor

        # Create one button per layout.
        for layout in range(1, 6):
            button = discord.ui.Button(label=f"Layout {layout}", style=discord.ButtonStyle.primary)

            async def layout_callback(interaction: discord.Interaction, layout=layout):
                # Build the URL for the individual layout image from GitHub Pages.
                image_url = f"{GITHUB_BASE_URL}/raw_images/lavacave-{self.floor}-{layout}.png"
                embed = discord.Embed(title=f"Floor {self.floor} - Layout {layout}")
                embed.set_image(url=image_url)
                await interaction.response.edit_message(
                    content="Here is your chosen layout:",
                    embed=embed,
                    view=LayoutDetailView(self.floor)
                )

            button.callback = layout_callback
            self.add_item(button)

        # Button to return to a fresh floor selection view.
        return_button = discord.ui.Button(label="Return to Floor Selection", style=discord.ButtonStyle.secondary)

        async def return_to_floor(interaction: discord.Interaction):
            await interaction.response.edit_message(
                content="Select a floor:",
                embed=None,
                view=FloorSelectionView(list(range(1, 51)))
            )

        return_button.callback = return_to_floor
        self.add_item(return_button)

# ---------------------------
# Layout Detail View
# ---------------------------
class LayoutDetailView(discord.ui.View):
    def __init__(self, floor):
        super().__init__(timeout=60)
        self.floor = floor

        # Button to return to the layout selection view.
        button = discord.ui.Button(label="Return to Layout Selection", style=discord.ButtonStyle.secondary)

        async def return_to_layout(interaction: discord.Interaction):
            merged_url = f"{GITHUB_BASE_URL}/merged_images/merged-floor-{self.floor}.png"
            embed = discord.Embed(title=f"Floor {self.floor} Layouts")
            embed.set_image(url=merged_url)
            await interaction.response.edit_message(
                content=f"Selected floor {self.floor}. Choose a layout:",
                embed=embed,
                view=LayoutSelectionView(self.floor)
            )

        button.callback = return_to_layout
        self.add_item(button)

# ---------------------------
# Bot Initialization and Commands
# ---------------------------
intents = discord.Intents.default()
intents.message_content = True  # Required to read commands (may not be needed after swap to slash commands)
token = os.getenv("DISCORD_BOT_TOKEN")
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# Global Slash Command Check
# ---------------------------
# def allowed_channel_check(interaction: discord.Interaction) -> bool:
#     return interaction.channel.id in ALLOWED_CHANNELS
#
# bot.tree.global_checks.append(allowed_channel_check)

# ---------------------------
# Slash Commands Cog
# ---------------------------
class LC(commands.GroupCog, name="lc"):
    """Slash command group for Lava Cave Bot commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="start", description="Starts the interactive Lava Cave session with floor selection.")
    async def start(self, interaction: discord.Interaction):
        if interaction.channel.id not in ALLOWED_CHANNELS:
            await interaction.response.send_message("You cannot use this command in this channel.", ephemeral=True)
            return
        async for message in interaction.channel.history(limit=100):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")

        floors = list(range(1, 51))
        view = FloorSelectionView(floors)
        await interaction.response.send_message("Select a floor:", view=view)

    @app_commands.command(name="stop", description="Clears the bot's previous messages.")
    async def stop(self, interaction: discord.Interaction):
        if interaction.channel.id not in ALLOWED_CHANNELS:
            await interaction.response.send_message("You cannot use this command in this channel.", ephemeral=True)
            return
        async for message in interaction.channel.history(limit=100):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")

        # await interaction.response.send_message("Cleared bot messages.", ephemeral=True)

    @app_commands.command(name="floor", description="Directly load a floor's layouts (provide a number 1-50).")
    async def floor(self, interaction: discord.Interaction, number: int):
        if interaction.channel.id not in ALLOWED_CHANNELS:
            await interaction.response.send_message("You cannot use this command in this channel.", ephemeral=True)
            return
        if number < 1 or number > 50:
            await interaction.response.send_message("Error: Floor number must be between 1 and 50.", ephemeral=True)
            return
        async for message in interaction.channel.history(limit=100):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")
        merged_url = f"{GITHUB_BASE_URL}/merged_images/merged-floor-{number}.png"
        embed = discord.Embed(title=f"Floor {number} Layouts")
        embed.set_image(url=merged_url)
        await interaction.response.send_message(f"Selected floor {number}. Choose a layout:", embed=embed,
                                                view=LayoutSelectionView(number))

    @app_commands.command(name="help", description="Shows help for Lava Cave Bot commands.")
    async def help(self, interaction: discord.Interaction):
        if interaction.channel.id not in ALLOWED_CHANNELS:
            await interaction.response.send_message("You cannot use this command in this channel.", ephemeral=True)
            return
        help_message = (
            "**Lava Cave Bot Commands:**\n\n"
            "/lc start : Starts the interactive session with floor selection.\n"
            "/lc stop : Clears the bot's previous messages.\n"
            "/lc floor <number> : Directly loads the specified floor's layouts (1-50).\n"
            "/lc help : Shows this help message.\n"
        )
        await interaction.response.send_message(help_message, ephemeral=True)

# ---------------------------
# Add Cog and Event Handlers
# ---------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")

bot.add_cog(LC(bot))

# ---------------------------
# Run the Bot
# ---------------------------
# Add the LC cog (you can also load it as an extension if you split the code into modules)
bot.run(token)
