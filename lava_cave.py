import discord
from discord.ext import commands
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
intents.message_content = True  # Required to read commands
token = os.getenv("DISCORD_BOT_TOKEN")
bot = commands.Bot(command_prefix="!", intents=intents)

# Create a command group for 'lc'
@bot.group(invoke_without_command=True)
async def lc(ctx, floor: int = None):
    """
    If invoked as !lc <number>, clears previous bot messages and skips directly
    to showing the merged layouts for that floor.
    """
    if floor is None:
        await ctx.send("Usage: `!lc start` to start, `!lc stop` to stop, or `!lc <floor>` to go directly to a floor.")
    else:
        # Validate the floor number.
        if floor < 1 or floor > 50:
            await ctx.send("Error: Floor number must be between 1 and 50.")
            return

        # Clear previous bot messages.
        async for message in ctx.channel.history(limit=100):
            if message.author == bot.user:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")
        merged_url = f"{GITHUB_BASE_URL}/merged_images/merged-floor-{floor}.png"
        embed = discord.Embed(title=f"Floor {floor} Layouts")
        embed.set_image(url=merged_url)
        await ctx.send(f"Selected floor {floor}. Choose a layout:", embed=embed, view=LayoutSelectionView(floor))

@lc.command(name="start")
async def lc_start(ctx):
    """Starts the Lava Cave interactive session with floor selection."""
    # Clear previous bot messages.
    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user:
            try:
                await message.delete()
            except Exception as e:
                print(f"Error deleting message: {e}")
    floors = list(range(1, 51))
    view = FloorSelectionView(floors)
    await ctx.send("Select a floor:", view=view)

@lc.command(name="stop")
async def lc_stop(ctx):
    """Stops the interactive session by deleting recent bot messages."""
    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user:
            try:
                await message.delete()
            except Exception as e:
                print(f"Error deleting message: {e}")

@lc.command(name="help")
@commands.cooldown(1, 60, commands.BucketType.channel)
async def lc_help(ctx):
    """
    Displays a help message for Lava Cave Bot commands.
    """
    help_message = (
        "**Lava Cave Bot Commands:**\n\n"
        "- `!lc start` : Starts the interactive Lava Cave session with floor selection.\n"
        "- `!lc stop` : Stops the interactive session by deleting the bot's recent messages.\n"
        "- `!lc <floor>` : Skips the floor selection and directly loads the specified floor's layouts (valid floors: 1-50).\n"
        "   For example: `!lc 45` loads floor 45.\n"
    )
    await ctx.send(help_message)

@bot.check
def only_in_allowed_channel(ctx):
    return ctx.channel.id in ALLOWED_CHANNELS

# ---------------------------
# Run the Bot
# ---------------------------
bot.run(token)
