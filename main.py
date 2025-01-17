from funcs import *

import time
from datetime import datetime, timedelta
import asyncio



async def app():
    while True:
        await wait_until_next_minute()  # Wait for the next minute
        await nav()    # Call your async function

async def wait_until_next_minute():
    now = datetime.now()
    if now.minute < 30:
        next_run = now.replace(minute=30, second=0, microsecond=0)  # Set to the next 30-minute mark
    else:
        next_run = (now + timedelta(hours=1)).replace(minute=0, second=0,
                                                      microsecond=0)  # Set to the top of the next hour
    sleep_time = (next_run - now).total_seconds()
    print(f"Sleeping for {sleep_time:.2f} seconds until {next_run}")
    await asyncio.sleep(sleep_time)  # Use asyncio.sleep for async operations


if __name__ == "__main__":
    asyncio.run(app())