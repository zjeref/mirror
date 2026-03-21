"""Tiny Habit design flow - helps users create BJ Fogg-style habits."""

from typing import Any

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow
from app.psychology.tiny_habits import (
    COMMON_ANCHORS,
    get_templates_for_area,
)


@register_flow
class TinyHabitFlow(BaseFlow):
    flow_id = "tiny_habit"
    display_name = "Build a Tiny Habit"

    def get_steps(self) -> list[str]:
        return ["choose_area", "choose_habit", "choose_anchor", "set_celebration", "confirm"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        return FlowResult(
            next_step="choose_area",
            response_message=(
                "Let's build a tiny habit. The secret is making it so small "
                "you can't say no — even on your worst day."
            ),
            prompt=FlowPrompt(
                prompt="What area of your life do you want this habit for?",
                input_type="choice",
                options=["physical", "mental", "career", "habits"],
            ),
        )

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        if step == "choose_area":
            area = str(value).strip().lower()
            if area not in ("physical", "mental", "career", "habits"):
                area = "physical"
            self.collected_data["life_area"] = area

            templates = get_templates_for_area(area)
            template_names = [t["name"] for t in templates]
            self.state["templates"] = templates

            return FlowResult(
                next_step="choose_habit",
                response_message=f"Great, let's build a {area} habit.",
                prompt=FlowPrompt(
                    prompt="Which of these resonates? (or type your own)",
                    input_type="choice",
                    options=template_names,
                ),
            )

        elif step == "choose_habit":
            choice = str(value).strip()
            templates = self.state.get("templates", [])

            # Find matching template
            selected = None
            for t in templates:
                if t["name"].lower() == choice.lower():
                    selected = t
                    break

            if selected:
                self.collected_data["template"] = selected
                self.collected_data["habit_name"] = selected["name"]
                self.collected_data["tiny_behavior"] = selected["tiny"]
                self.collected_data["full_behavior"] = selected["full"]
            else:
                # Custom habit
                self.collected_data["habit_name"] = choice
                self.collected_data["tiny_behavior"] = choice
                self.collected_data["full_behavior"] = choice

            tiny = self.collected_data["tiny_behavior"]

            return FlowResult(
                next_step="choose_anchor",
                response_message=(
                    f"The tiniest version: **{tiny}**\n\n"
                    "Now we need an anchor — an existing habit you already do every day."
                ),
                prompt=FlowPrompt(
                    prompt="When should this happen? Pick an anchor or type your own.",
                    input_type="choice",
                    options=COMMON_ANCHORS[:5],  # Show top 5
                ),
            )

        elif step == "choose_anchor":
            anchor = str(value).strip()
            self.collected_data["anchor"] = anchor

            return FlowResult(
                next_step="set_celebration",
                response_message=(
                    f"Your recipe so far:\n\n"
                    f"> {anchor}, I will {self.collected_data['tiny_behavior']}\n\n"
                    "Last piece: a tiny celebration right after. "
                    "This wires the habit into your brain."
                ),
                prompt=FlowPrompt(
                    prompt="How will you celebrate? (fist pump, say 'yes!', smile, etc.)",
                    input_type="text",
                ),
            )

        elif step == "set_celebration":
            celebration = str(value).strip() or "Say 'I did it!'"
            self.collected_data["celebration"] = celebration

            anchor = self.collected_data["anchor"]
            tiny = self.collected_data["tiny_behavior"]

            return FlowResult(
                next_step="confirm",
                response_message=(
                    f"Your Tiny Habit recipe:\n\n"
                    f"> **{anchor}**, I will **{tiny}**, "
                    f"and celebrate by **{celebration}**\n\n"
                    "This should take less than 30 seconds."
                ),
                prompt=FlowPrompt(
                    prompt="Save this habit?",
                    input_type="choice",
                    options=["Yes, save it!", "Let me change something"],
                ),
            )

        elif step == "confirm":
            answer = str(value).strip().lower()
            if "yes" in answer or "save" in answer:
                self.collected_data["confirmed"] = True
            else:
                self.collected_data["confirmed"] = False

            return FlowResult(next_step=None)

        return FlowResult(next_step=None)

    async def on_complete(self, context: UserContext) -> str:
        if self.collected_data.get("confirmed"):
            return (
                "Habit saved! Remember: the goal isn't to do more — "
                "it's to show up consistently. Even the tiniest version counts as a win. "
                "I'll remind you to log it during check-ins."
            )
        else:
            return (
                "No worries, we can redesign it anytime. "
                "Just say 'build a habit' when you're ready."
            )
