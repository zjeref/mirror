"""Terminal chat UI using Rich."""

import asyncio
import json
import signal
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt

from mirror_cli.api_client import load_tokens

console = Console()

DEFAULT_WS_URL = "ws://localhost:8000/api/chat/ws"


async def chat_session(ws_url: str = DEFAULT_WS_URL):
    """Run an interactive chat session with Mirror."""
    try:
        import websockets
    except ImportError:
        console.print("[red]websockets package required. Install with: pip install websockets[/red]")
        return

    tokens = load_tokens()
    if not tokens:
        console.print("[red]Not logged in. Run: mirror login[/red]")
        return

    url = f"{ws_url}?token={tokens['access_token']}"
    console.print(Panel("[dim]Connecting to Mirror...[/dim]", style="blue"))

    try:
        async with websockets.connect(url) as ws:
            console.print("[dim]Connected. Type your message, or 'quit' to exit.[/dim]\n")

            # Handle incoming messages in background
            async def receive():
                async for raw in ws:
                    data = json.loads(raw)
                    if data.get("type") == "pong":
                        continue
                    if data.get("type") == "message":
                        content = data.get("content", "")
                        console.print()
                        console.print(Panel(
                            Markdown(content),
                            title="[bold blue]Mirror[/bold blue]",
                            border_style="blue",
                            padding=(0, 1),
                        ))

                        # Show flow prompt if present
                        flow_prompt = data.get("flow_prompt")
                        if flow_prompt:
                            prompt_text = flow_prompt.get("prompt", "")
                            input_type = flow_prompt.get("input_type", "text")

                            if input_type == "slider":
                                min_v = flow_prompt.get("min_val", 1)
                                max_v = flow_prompt.get("max_val", 10)
                                console.print(f"\n[dim]{prompt_text} ({min_v}-{max_v})[/dim]")
                            elif input_type == "choice":
                                options = flow_prompt.get("options", [])
                                console.print(f"\n[dim]{prompt_text}[/dim]")
                                for i, opt in enumerate(options, 1):
                                    console.print(f"  [cyan]{i}.[/cyan] {opt}")
                            else:
                                console.print(f"\n[dim]{prompt_text}[/dim]")

                        console.print()

            recv_task = asyncio.create_task(receive())

            # Send loop
            try:
                while True:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: Prompt.ask("[bold green]You[/bold green]")
                    )

                    if line.lower() in ("quit", "exit", "q"):
                        break

                    await ws.send(json.dumps({
                        "type": "message",
                        "content": line,
                    }))
            except (KeyboardInterrupt, EOFError):
                pass
            finally:
                recv_task.cancel()

    except Exception as e:
        console.print(f"[red]Connection error: {e}[/red]")

    console.print("\n[dim]Chat ended. Take care.[/dim]")
