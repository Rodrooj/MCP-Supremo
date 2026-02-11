import asyncio
import logging
import os
from mcp.server.fastmcp import FastMCP

# Initialize the Server
mcp = FastMCP("ArchLinux-Admin-Server")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@mcp.tool()
async def execute_command(command: str, input_text: str = None) -> str:
    """
    Executes a Bash command. Supports input injection (for passwords/sudo).
    """
    logger.info(f"Received request to execute: {command}")

    # Safety: Block reckless commands
    forbidden = ["rm -rf /", ":(){ :|:& };:"]
    if any(f in command for f in forbidden):
        return "Error: Command blocked by safety filter."

    try:
        # Prepare input data if provided (e.g. sudo password)
        stdin_data = input_text.encode() if input_text else None

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if stdin_data else None
        )
        
        stdout, stderr = await process.communicate(input=stdin_data)
        
        output = ""
        if stdout:
            output += f"STDOUT:\n{stdout.decode().strip()}\n"
        if stderr:
            output += f"STDERR:\n{stderr.decode().strip()}\n"
        
        output += f"\nExit Code: {process.returncode}"
        
        return output

    except Exception as e:
        return f"System Error executing command: {str(e)}"

if __name__ == "__main__":
    mcp.run()
