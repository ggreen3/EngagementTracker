import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from playwright.async_api import async_playwright

# Load environment variables
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

# Helper function to save data to .txt file
def save_to_txt(data):
    try:
        with open(DATA_FILE, "a") as file:
            file.write(f"{data['user']},{data['likes']},{data['shares']},{data['comments']}\n")
    except Exception as e:
        print(f"⚠️ Error saving data to file: {e}")

# Scrape engagement metrics using Playwright's Async API
async def scrape_metrics(url):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)  # Launch headless browser
            page = await browser.new_page()

            # Navigate to the URL with a timeout of 30 seconds
            await page.goto(url, timeout=30000)

            # Default values in case scraping fails
            likes = 0
            shares = 0
            comments = 0

            if "twitter.com" in url or "x.com" in url:
                # Scrape Twitter/X metrics
                try:
                    await page.wait_for_selector('div[data-testid="like"]', timeout=10000)
                    like_element = await page.query_selector('div[data-testid="like"]')
                    likes = int((await like_element.inner_text()).strip().replace(",", "")) if like_element else 0
                except Exception:
                    pass

                try:
                    await page.wait_for_selector('div[data-testid="retweet"]', timeout=10000)
                    share_element = await page.query_selector('div[data-testid="retweet"]')
                    shares = int((await share_element.inner_text()).strip().replace(",", "")) if share_element else 0
                except Exception:
                    pass

                try:
                    await page.wait_for_selector('div[data-testid="reply"]', timeout=10000)
                    comment_element = await page.query_selector('div[data-testid="reply"]')
                    comments = int((await comment_element.inner_text()).strip().replace(",", "")) if comment_element else 0
                except Exception:
                    pass

            elif "threads.net" in url:
                # Scrape Threads metrics
                try:
                    await page.wait_for_selector('span:has-text("Likes")', timeout=10000)
                    like_element = await page.query_selector('span:has-text("Likes")')
                    likes = int((await like_element.inner_text()).strip().replace(",", "")) if like_element else 0
                except Exception:
                    pass

                # Threads doesn't have shares or comments in the same way, so set to 0
                shares = 0
                comments = 0

            elif "youtube.com" in url:
                # Scrape YouTube metrics
                try:
                    await page.wait_for_selector('#segmented-like-button > yt-formatted-string', timeout=10000)
                    like_element = await page.query_selector('#segmented-like-button > yt-formatted-string')
                    likes = int((await like_element.inner_text()).strip().replace(",", "")) if like_element else 0
                except Exception:
                    pass

                # YouTube doesn't have "shares" or "comments" easily accessible, so set to 0
                shares = 0
                comments = 0

            elif "tiktok.com" in url:
                # Scrape TikTok metrics
                try:
                    await page.wait_for_selector('strong[data-e2e="like-count"]', timeout=10000)
                    like_element = await page.query_selector('strong[data-e2e="like-count"]')
                    likes = int((await like_element.inner_text()).strip().replace(",", "")) if like_element else 0
                except Exception:
                    pass

                try:
                    await page.wait_for_selector('strong[data-e2e="share-count"]', timeout=10000)
                    share_element = await page.query_selector('strong[data-e2e="share-count"]')
                    shares = int((await share_element.inner_text()).strip().replace(",", "")) if share_element else 0
                except Exception:
                    pass

                try:
                    await page.wait_for_selector('strong[data-e2e="comment-count"]', timeout=10000)
                    comment_element = await page.query_selector('strong[data-e2e="comment-count"]')
                    comments = int((await comment_element.inner_text()).strip().replace(",", "")) if comment_element else 0
                except Exception:
                    pass

            elif "instagram.com" in url:
                # Scrape Instagram metrics
                try:
                    await page.wait_for_selector('section.x9f619 > span > a > span', timeout=10000)
                    like_element = await page.query_selector('section.x9f619 > span > a > span')
                    likes = int((await like_element.inner_text()).strip().replace(",", "")) if like_element else 0
                except Exception:
                    pass

                try:
                    await page.wait_for_selector('span._aauw', timeout=10000)
                    comment_element = await page.query_selector('span._aauw')
                    comments = int((await comment_element.inner_text()).strip().replace(",", "")) if comment_element else 0
                except Exception:
                    pass

                # Instagram doesn't display shares directly, so set to 0
                shares = 0

            else:
                await browser.close()
                return {"error": "❌ Unsupported platform. Please submit a link from Twitter, Threads, YouTube, TikTok, or Instagram."}

            await browser.close()

            return {
                "likes": likes,
                "shares": shares,
                "comments": comments
            }

        except Exception as e:
            return {"error": f"❌ Failed to process submission: {e}"}

# Command: !submit
@bot.command()
async def submit(ctx, url):
    user = ctx.author.name
    await ctx.send(f"🚀 {user}, processing your submission...")

    # Scrape metrics asynchronously
    metrics = await scrape_metrics(url)

    if "error" in metrics:
        await ctx.send(f"⚠️ Oops! {metrics['error']}")
        return

    data = {"user": user, "likes": metrics["likes"], "shares": metrics["shares"], "comments": metrics["comments"]}

    # Save to .txt file
    save_to_txt(data)

    # Send a fun and colorful response
    await ctx.send(
        f"🎉 Submission successful! Here are the stats:\n"
        f"❤️ Likes: {metrics['likes']} | 🔁 Shares: {metrics['shares']} | 💬 Comments: {metrics['comments']}"
    )

# Command: !rankings
@bot.command()
async def rankings(ctx, password):
    if password != PASSWORD:
        await ctx.send("🔒 Access denied. Incorrect password.")
        return

    try:
        with open(DATA_FILE, "r") as file:
            lines = file.readlines()

        if not lines:
            await ctx.send("📊 No data available yet. Be the first to submit!")
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
        response = "🏆 **Rankings** 🏆\n"
        for i, entry in enumerate(rankings, start=1):
            response += (
                f"{i}. **{entry['user']}** - "
                f"❤️ {entry['likes']} Likes | "
                f"🔁 {entry['shares']} Shares | "
                f"💬 {entry['comments']} Comments\n"
            )

        await ctx.send(response)

    except FileNotFoundError:
        await ctx.send("📊 No data available yet. Be the first to submit!")

# Main entry point
if __name__ == "__main__":
    # Start the dummy HTTP server in a separate thread
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Run the bot
    bot.run(DISCORD_TOKEN)
