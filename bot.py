import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()

# Replace placeholders with environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PASSWORD = os.getenv("PASSWORD")
DATA_FILE = "engagement_data.txt"  # Text file to store data

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Scrape engagement metrics using Playwright
def scrape_metrics(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Launch headless browser
        page = browser.new_page()
        page.goto(url)

        # Example: Scrape likes, shares, etc. (adjust selectors based on platform)
        likes = page.query_selector(".like-count").inner_text().strip()
        shares = page.query_selector(".share-count").inner_text().strip()
        comments = page.query_selector(".comment-count").inner_text().strip()

        browser.close()

        return {
            "likes": int(likes.replace(",", "")),
            "shares": int(shares.replace(",", "")),
            "comments": int(comments.replace(",", ""))
        }

# Save engagement data to a .txt file
def save_to_txt(data):
    with open(DATA_FILE, "a") as file:
        file.write(f"{data['user']},{data['likes']},{data['shares']},{data['comments']}\n")

# Load data from the .txt file
def load_from_txt():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r") as file:
        lines = file.readlines()

    data = []
    for line in lines:
        user, likes, shares, comments = line.strip().split(",")
        data.append({
            "user": user,
            "likes": int(likes),
            "shares": int(shares),
            "comments": int(comments)
        })
    return data

# Bot command to submit a post URL
@bot.command()
async def submit(ctx, url):
    user = ctx.author.name
    await ctx.send(f"{user}, processing your submission...")

    # Scrape metrics
    metrics = scrape_metrics(url)
    if metrics:
        data = {"user": user, "likes": metrics["likes"], "shares": metrics["shares"], "comments": metrics["comments"]}

        # Save to .txt file
        save_to_txt(data)

        await ctx.send(f"Submission successful! Likes: {metrics['likes']}, Shares: {metrics['shares']}, Comments: {metrics['comments']}")
    else:
        await ctx.send("Failed to process submission. Please check the URL.")

# Bot command to view rankings
@bot.command()
async def rankings(ctx, password: str = None):
    if password != PASSWORD:
        await ctx.send("Access denied. Incorrect password.")
        return

    data = load_from_txt()
    if not data:
        await ctx.send("No data available yet.")
        return

    # Sort by likes (you can change this to shares or comments)
    data.sort(key=lambda x: x["likes"], reverse=True)

    # Format rankings
    rankings = "\n".join([f"{i+1}. {row['user']} - Likes: {row['likes']}, Shares: {row['shares']}, Comments: {row['comments']}" for i, row in enumerate(data)])
    await ctx.send(f"**Rankings:**\n{rankings}")

# Run the bot
bot.run(DISCORD_TOKEN)
