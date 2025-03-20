import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Load environment variables from Render
load_dotenv()

# Replace placeholders with environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PASSWORD = os.getenv("PASSWORD")
DATA_FILE = "engagement_data.txt"  # Text file to store data

# Set up the bot with privileged intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Dummy HTTP server to satisfy Render's port requirement
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 8000), DummyServer)
    server.serve_forever()

# Command: !submit
@bot.command()
async def submit(ctx, url):
    user = ctx.author.name
    await ctx.send(f"{user}, processing your submission...")

    # Temporarily bypass scraping logic
    metrics = {"likes": 0, "shares": 0, "comments": 0}  # Simulate empty data

    if metrics:
        data = {"user": user, "likes": metrics["likes"], "shares": metrics["shares"], "comments": metrics["comments"]}

        # Save to .txt file
        save_to_txt(data)

        await ctx.send(f"Submission successful! Likes: {metrics['likes']}, Shares: {metrics['shares']}, Comments: {metrics['comments']}")
    else:
        await ctx.send("Failed to process submission. Please check the URL.")

# Command: !rankings
@bot.command()
async def rankings(ctx, password):
    if password != PASSWORD:
        await ctx.send("Access denied. Incorrect password.")
        return

    try:
        with open(DATA_FILE, "r") as file:
            lines = file.readlines()

        if not lines:
            await ctx.send("No data available yet.")
            return

        # Parse data
        rankings = []
        for line in lines:
            user, likes, shares, comments = line.strip().split(",")
            rankings.append({
                "user": user,
                "likes": int(likes),
                "shares": int(shares),
                "comments": int(comments)
            })

        # Sort by likes (descending)
        rankings.sort(key=lambda x: x["likes"], reverse=True)

        # Build response
        response = "Rankings:\n"
        for i, entry in enumerate(rankings, start=1):
            response += f"{i}. {entry['user']} - Likes: {entry['likes']}, Shares: {entry['shares']}, Comments: {entry['comments']}\n"

        await ctx.send(response)
    except FileNotFoundError:
        await ctx.send("No data available yet.")

# Helper function to save data to .txt file
def save_to_txt(data):
    try:
        with open(DATA_FILE, "a") as file:
            file.write(f"{data['user']},{data['likes']},{data['shares']},{data['comments']}\n")
    except Exception as e:
        print(f"Error saving data to file: {e}")

# Main entry point
if __name__ == "__main__":
    # Start the dummy HTTP server in a separate thread
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Run the bot
    bot.run(DISCORD_TOKEN)
