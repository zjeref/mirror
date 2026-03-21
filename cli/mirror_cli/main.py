"""Mirror CLI - Terminal client for personal growth."""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mirror_cli import api_client

app = typer.Typer(
    name="mirror",
    help="Mirror - Your personal growth companion",
    no_args_is_help=True,
)
console = Console()


@app.command()
def register(
    email: str = typer.Option(..., prompt=True),
    name: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Create a new Mirror account."""
    try:
        api_client.register(email, name, password)
        console.print(f"\n[green]Welcome to Mirror, {name}![/green]")
        console.print("[dim]Run 'mirror chat' to start talking.[/dim]")
    except Exception as e:
        console.print(f"[red]Registration failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def login(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Log in to your Mirror account."""
    try:
        api_client.login(email, password)
        console.print("[green]Logged in successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logout():
    """Log out and clear saved tokens."""
    api_client.clear_tokens()
    console.print("[dim]Logged out.[/dim]")


@app.command()
def chat():
    """Start an interactive chat session with Mirror."""
    from mirror_cli.chat import chat_session

    asyncio.run(chat_session())


@app.command()
def status():
    """Show your dashboard summary."""
    try:
        data = api_client.get_dashboard()
    except Exception as e:
        console.print(f"[red]Failed to load dashboard: {e}[/red]")
        raise typer.Exit(1)

    # Quick stats
    mood = data.get("current_mood")
    energy = data.get("current_energy")
    checkins = data.get("total_check_ins", 0)
    days = data.get("days_active", 0)

    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="dim")
    stats_table.add_column(style="bold")
    stats_table.add_row("Mood", _color_score(mood))
    stats_table.add_row("Energy", _color_score(energy))
    stats_table.add_row("Check-ins", str(checkins))
    stats_table.add_row("Days active", str(days))

    console.print(Panel(stats_table, title="[bold]Mirror Dashboard[/bold]", border_style="blue"))

    # Life areas
    areas = data.get("life_area_scores", [])
    if areas:
        area_table = Table(title="Life Areas", show_lines=False)
        area_table.add_column("Area", style="cyan")
        area_table.add_column("Score", justify="right")
        area_table.add_column("Trend")

        trend_icons = {"improving": "[green]↑[/green]", "declining": "[red]↓[/red]", "stable": "[dim]→[/dim]"}
        for area in areas:
            area_table.add_row(
                area["area"].capitalize(),
                _color_score(area["score"]),
                trend_icons.get(area["trend"], ""),
            )
        console.print(area_table)

    # Habits
    habits = data.get("active_habits", [])
    if habits:
        console.print()
        habit_table = Table(title="Habits", show_lines=False)
        habit_table.add_column("Habit", style="cyan")
        habit_table.add_column("Streak", justify="right", style="bold yellow")
        habit_table.add_column("Total", justify="right", style="dim")

        for h in habits:
            habit_table.add_row(h["name"], str(h["streak"]), str(h["total_completions"]))
        console.print(habit_table)

    # Patterns
    patterns = data.get("recent_patterns", [])
    if patterns:
        console.print()
        console.print("[bold]Detected Patterns[/bold]")
        for p in patterns:
            conf = int(p["confidence"] * 100)
            console.print(f"  [dim]{conf}%[/dim] {p['description']}")
            if p.get("actionable_insight"):
                console.print(f"      [italic dim]{p['actionable_insight']}[/italic dim]")


@app.command()
def habits():
    """List your active habits."""
    try:
        habit_list = api_client.get_habits()
    except Exception as e:
        console.print(f"[red]Failed to load habits: {e}[/red]")
        raise typer.Exit(1)

    if not habit_list:
        console.print("[dim]No habits yet. Start one in chat: mirror chat[/dim]")
        return

    table = Table(title="Your Habits")
    table.add_column("#", style="dim", width=3)
    table.add_column("Habit", style="cyan")
    table.add_column("Streak", justify="right", style="bold yellow")
    table.add_column("Total", justify="right", style="dim")

    for i, h in enumerate(habit_list, 1):
        table.add_row(str(i), h["name"], str(h["streak"]), str(h["total_completions"]))

    console.print(table)


@app.command(name="habit-done")
def habit_done(
    habit_number: int = typer.Argument(..., help="Habit number from 'mirror habits' list"),
):
    """Log a habit completion."""
    try:
        habit_list = api_client.get_habits()
    except Exception as e:
        console.print(f"[red]Failed to load habits: {e}[/red]")
        raise typer.Exit(1)

    if habit_number < 1 or habit_number > len(habit_list):
        console.print(f"[red]Invalid habit number. You have {len(habit_list)} habits.[/red]")
        raise typer.Exit(1)

    habit = habit_list[habit_number - 1]
    try:
        result = api_client.log_habit(habit["id"], True)
        console.print(f"[green]Logged '{habit['name']}'![/green] Streak: {result['streak']}")
    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def patterns():
    """Show detected behavioral patterns."""
    try:
        pattern_list = api_client.get_patterns()
    except Exception as e:
        console.print(f"[red]Failed to load patterns: {e}[/red]")
        raise typer.Exit(1)

    if not pattern_list:
        console.print("[dim]No patterns detected yet. Keep checking in — they emerge after 5+ data points.[/dim]")
        return

    for p in pattern_list:
        conf = int(p["confidence"] * 100)
        console.print(Panel(
            f"{p['description']}\n\n[italic dim]{p.get('actionable_insight', '')}[/italic dim]",
            title=f"[bold]{p['pattern_type']}[/bold] [dim]({conf}% confidence)[/dim]",
            border_style="blue",
        ))


def _color_score(score) -> str:
    if score is None:
        return "[dim]—[/dim]"
    s = float(score)
    if s >= 7:
        return f"[green]{s:.1f}[/green]"
    elif s >= 4:
        return f"[yellow]{s:.1f}[/yellow]"
    else:
        return f"[red]{s:.1f}[/red]"


if __name__ == "__main__":
    app()
