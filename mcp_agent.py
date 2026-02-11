import asyncio
import os
import sys
import getpass
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import Google GenAI
from google import genai
from google.genai import types

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
SYSTEM_PROMPT = """
You are an Expert Arch Linux System Administrator and Autonomous Agent. 
Your goal is to solve the user's system problems by planning and executing bash commands.

ENVIRONMENT CONTEXT:
- OS: Arch Linux
- Package Manager: pacman (ALWAYS use --noconfirm for non-interactive installs)
- Init System: systemd (systemctl, journalctl)

RULES:
1. THINK & PLAN: detailed analysis of the problem.
2. BATCH COMMANDS: Do not execute one by one. Generate a COMPLETE LIST.
3. USE 'execute_plan': Send the list of commands to this tool.
4. SUDO: Simply use 'sudo' in your commands. The client handles password injection.

FILE EDITING PROTOCOLS (CRITICAL):
- READ FIRST: Always 'cat' a file before editing it to understand the structure.
- BACKUP: Before modifying any config file, create a backup (e.g., `sudo cp file file.bak`).
- USE 'TEE': Do not use 'sudo echo "text" > file'. Use 'echo "text" | sudo tee file' to handle permissions correctly.
- SED SAFETY: When using 'sed', be precise. If unsure, backup first.

CRITICAL:
- If a command in the plan fails, execution will stop immediately.
- Verify your work by including a verification command at the end of the plan.
"""

class ArchAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set.")
            sys.exit(1)
            
        self.client = genai.Client(api_key=api_key).aio
        
        # Session state for sudo password
        self.cached_sudo_password = None

        # --- TOOL DEFINITION: EXECUTE PLAN (List of Commands) ---
        self.execute_plan_tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="execute_plan",
                    description="Execute a sequential list of bash commands.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "commands": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of bash command strings to execute in order."
                            }
                        },
                        "required": ["commands"]
                    }
                )
            ]
        )
        
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[self.execute_plan_tool],
            temperature=0.2,
        )
        
        self.chat = self.client.chats.create(
            model="gemini-2.5-flash", 
            config=self.config
        )
        
        current_dir = Path(__file__).parent.absolute()
        self.server_script = str(current_dir / "mcp_server.py")

    async def run_loop(self):
        if not os.path.exists(self.server_script):
            print(f"CRITICAL ERROR: Server file not found at: {self.server_script}")
            return

        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script], 
            env=os.environ.copy()
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    print(f"\n🐧 Arch Linux Autonomous Agent Initialized 🐧")
                    print(f"Connected to Server: {self.server_script}")
                    print("Type 'quit' to exit.")

                    while True:
                        try:
                            user_input = input("\n\033[1;34mUser Problem > \033[0m")
                            if user_input.lower() in ['quit', 'exit']:
                                break
                            
                            await self.process_turn(session, user_input)
                        except KeyboardInterrupt:
                            print("\nUser interrupted.")
                            break
        except Exception as e:
            print(f"\nConnection failed: {e}")

    async def process_turn(self, session, user_input):
        step_count = 0
        max_steps = 10 
        current_input = user_input

        while step_count < max_steps:
            print(f"\n\033[90m[Thinking...]\033[0m")
            
            try:
                response = await self.chat.send_message(current_input)
            except Exception as e:
                print(f"Gemini API Error: {e}")
                return

            if not response.candidates:
                break

            parts = response.candidates[0].content.parts
            
            # Print text response
            text_parts = [p.text for p in parts if p.text]
            if text_parts:
                print(f"\n\033[1;36mAgent:\033[0m {''.join(text_parts).strip()}")

            # Handle Function Calls
            fc_parts = [p for p in parts if p.function_call]
            
            if fc_parts:
                tool_responses = []
                for part in fc_parts:
                    fc = part.function_call
                    if fc.name == "execute_plan":
                        # Get the list of commands
                        commands = fc.args.get("commands", [])
                        
                        if not commands:
                            print("Agent sent an empty plan.")
                            continue

                        # --- 1. DISPLAY THE PLAN ---
                        print(f"\n\033[1;33m📋 PROPOSED PLAN:\033[0m")
                        requires_sudo = False
                        for i, cmd in enumerate(commands):
                            print(f"  {i+1}. {cmd}")
                            if "sudo" in cmd:
                                requires_sudo = True
                        
                        # --- 2. HANDLE SUDO PASSWORD ONCE ---
                        if requires_sudo:
                            print(f"\n\033[1;35m🔒 Sudo privileges required.\033[0m")
                            if not self.cached_sudo_password:
                                self.cached_sudo_password = getpass.getpass("Enter sudo password (will be cached for this session): ")
                            else:
                                print("(Using cached password)")

                        # --- 3. CONFIRM ONCE ---
                        confirm = input("\nExecute this entire plan? [y/N]: ").strip().lower()
                        
                        plan_output = ""
                        
                        if confirm == 'y':
                            print(f"\033[1;32m[Executing Plan...]\033[0m")
                            
                            # --- 4. EXECUTION LOOP ---
                            for i, cmd in enumerate(commands):
                                print(f"\n\033[90m[{i+1}/{len(commands)}] Running: {cmd}\033[0m")
                                
                                input_payload = None
                                # Modify command for sudo if needed
                                if "sudo" in cmd:
                                    if "sudo -S" not in cmd:
                                        cmd = cmd.replace("sudo", "sudo -S")
                                    # Inject cached password
                                    if self.cached_sudo_password:
                                        input_payload = self.cached_sudo_password + "\n"

                                try:
                                    # Call the MCP Server for THIS specific command
                                    args = {"command": cmd}
                                    if input_payload:
                                        args["input_text"] = input_payload

                                    result = await session.call_tool("execute_command", arguments=args)
                                    output_text = result.content[0].text
                                    
                                    # Check for failure in output (Naive check based on exit code string from server)
                                    # The server returns "Exit Code: X" at the end.
                                    print(f"{output_text.strip()[:300]}...") # Preview output
                                    
                                    plan_output += f"--- Command: {cmd} ---\n{output_text}\n"

                                    if "Exit Code: 0" not in output_text:
                                        print(f"\033[1;31m⚠️ Command failed. Stopping plan execution.\033[0m")
                                        plan_output += "\n[Plan Execution Halted due to error]"
                                        break
                                        
                                except Exception as e:
                                    plan_output += f"Error executing {cmd}: {e}"
                                    print(f"\033[1;31m[MCP Error]\033[0m {e}")
                                    break
                        else:
                            print("\033[1;31m[Denied]\033[0m")
                            plan_output = "User denied permission to execute the plan."

                        # Send results back to Gemini
                        tool_responses.append(
                            types.Part.from_function_response(
                                name=fc.name,
                                response={"result": plan_output}
                            )
                        )
                
                current_input = tool_responses
            else:
                break 
            
            step_count += 1

if __name__ == "__main__":
    agent = ArchAgent()
    try:
        asyncio.run(agent.run_loop())
    except KeyboardInterrupt:
        print("\nGoodbye!")
