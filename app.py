import os
import logging
from dotenv import load_dotenv
from discord.ext import commands
from playwright.async_api import async_playwright

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get Discord token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in the environment variables.")

# Bot setup with privileged intents
intents = discord.Intents.default()
intents.messages = True  # Enable message content intent
intents.message_content = True  # Explicitly enable message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

# Error handling for Playwright browser launch
async def scrape_metrics(url):
    try:
        async with async_playwright() as p:
            # Specify the Chromium executable path explicitly
            chromium_executable_path = os.path.join(
                "/opt/render/.cache/ms-playwright",
                "chromium-1084",  # Adjust version if necessary
                "chrome-linux",
                "chrome"
            )

            if not os.path.exists(chromium_executable_path):
                logging.error(f"Chromium executable not found at {chromium_executable_path}")
                raise FileNotFoundError(f"Chromium executable not found at {chromium_executable_path}")

            browser = await p.chromium.launch(
                executable_path=chromium_executable_path,
                headless=True
            )
            page = await browser.new_page()
            await page.goto(url, timeout=30000)  # Navigate to the URL with a timeout

            # Example scraping logic (customize this based on your needs)
            title = await page.title()
            likes = await page.query_selector('selector-for-likes')  # Replace with actual selector
            comments = await page.query_selector('selector-for-comments')  # Replace with actual selector

            metrics = {
                "title": title,
                "likes": likes.inner_text() if likes else "N/A",
                "comments": comments.inner_text() if comments else "N/A"
            }

            await browser.close()
            return metrics
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        raise

# Command to submit a URL for scraping
@bot.command(name="submit")
async def submit(ctx, url: str):
    try:
        if not url.startswith("http"):
            await ctx.send("⚠️ Oops! ❌ Please provide a valid URL starting with 'http://' or 'https://'.")
            return

        await ctx.send(f"🚀 {ctx.author.name}, processing your submission...")
        metrics = await scrape_metrics(url)

        response = (
            f"📊 Engagement Metrics for `{metrics['title']}`:\n"
            f"👍 Likes: {metrics['likes']}\n"
            f"💬 Comments: {metrics['comments']}"
        )
        await ctx.send(response)
    except Exception as e:
        logging.error(f"Failed to process submission: {e}")
        await ctx.send(
            "⚠️ Oops! ❌ Failed to process submission. Please check the logs for details."
        )

# Command to display rankings
@bot.command(name="rankings")
async def rankings(ctx):
    try:
        # Placeholder for ranking logic
        await ctx.send("🏆 Rankings are currently unavailable.")
    except Exception as e:
        logging.error(f"Error in rankings command: {e}")
        await ctx.send("⚠️ Oops! ❌ Failed to fetch rankings.")

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logging.error(f"Bot failed to start: {e}")
