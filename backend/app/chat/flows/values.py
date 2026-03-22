"""Values clarification flow.

Helps users identify what matters most to them across life areas.
Based on ACT values clarification — the compass that guides BA activities.
"""

from typing import Any, Optional

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow


LIFE_AREAS = [
    "relationships", "health", "career", "creativity",
    "personal_growth", "fun_recreation",
]

AREA_LABELS = {
    "relationships": "Relationships & Connection",
    "health": "Physical & Mental Health",
    "career": "Work & Career",
    "creativity": "Creativity & Expression",
    "personal_growth": "Learning & Growth",
    "fun_recreation": "Fun & Recreation",
}

AREA_PROMPTS = {
    "relationships": "What kind of friend / partner / family member do you want to be? Not what you think you SHOULD be — what genuinely matters to you.",
    "health": "When it comes to your body and mind — what matters to you? Not society's version of healthy. Yours.",
    "career": "What do you want your work to mean? Not job title or salary — what kind of impact or experience do you want?",
    "creativity": "Is there anything you'd create, build, or express if nothing was stopping you?",
    "personal_growth": "What would you like to understand better — about yourself or the world?",
    "fun_recreation": "What actually brings you joy — not what's supposed to, but what genuinely does?",
}


@register_flow
class ValuesFlow(BaseFlow):
    flow_id = "values"
    display_name = "Values Exploration"

    def get_steps(self) -> list[str]:
        return ["pick_area", "explore_value", "confirm", "another"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        return FlowResult(
            next_step="pick_area",
            response_message=(
                "Let's figure out what actually matters to you — not what you think "
                "you *should* care about, but what genuinely pulls at you.\n\n"
                "Which area of life do you want to explore first?"
            ),
            prompt=FlowPrompt(
                prompt="Pick a life area:",
                input_type="choice",
                options=[AREA_LABELS[a] for a in LIFE_AREAS],
            ),
        )

    async def handle_input(self, step: str, value: Any, context: UserContext) -> FlowResult:
        if step == "pick_area":
            # Map display label back to key
            area_key = None
            value_str = str(value).lower()
            for key, label in AREA_LABELS.items():
                if label.lower() in value_str or key in value_str:
                    area_key = key
                    break
            if not area_key:
                area_key = LIFE_AREAS[0]

            self.collected_data["current_area"] = area_key
            prompt_text = AREA_PROMPTS.get(area_key, "What matters to you in this area?")

            return FlowResult(
                next_step="explore_value",
                response_message=prompt_text,
                prompt=FlowPrompt(prompt="Take your time..."),
            )

        elif step == "explore_value":
            area = self.collected_data.get("current_area", "general")
            self.collected_data.setdefault("values", {})[area] = str(value)

            return FlowResult(
                next_step="confirm",
                response_message=(
                    f"So in **{AREA_LABELS.get(area, area)}**, what matters to you is:\n\n"
                    f"> {value}\n\n"
                    "That's real. I'll remember this — it'll help me suggest actions "
                    "that actually align with who you want to be.\n\n"
                    "Want to explore another life area?"
                ),
                prompt=FlowPrompt(
                    prompt="Explore another area?",
                    input_type="choice",
                    options=["Yes, another area", "That's enough for now"],
                ),
            )

        elif step == "confirm":
            if "yes" in str(value).lower() or "another" in str(value).lower():
                # Pick areas not yet explored
                explored = list(self.collected_data.get("values", {}).keys())
                remaining = [a for a in LIFE_AREAS if a not in explored]
                if remaining:
                    return FlowResult(
                        next_step="pick_area",
                        response_message="Which area next?",
                        prompt=FlowPrompt(
                            prompt="Pick a life area:",
                            input_type="choice",
                            options=[AREA_LABELS[a] for a in remaining],
                        ),
                    )

            # Done
            return FlowResult(next_step=None)

        return FlowResult(next_step=None)

    async def on_complete(self, context: UserContext) -> str:
        from app.models.activity import UserValues

        values_data = self.collected_data.get("values", {})

        # Save to DB
        existing = await UserValues.find_one(UserValues.user_id == context.user_id)
        if existing:
            existing.values.update(values_data)
            await existing.save()
        else:
            uv = UserValues(user_id=context.user_id, values=values_data)
            await uv.insert()

        areas_explored = len(values_data)
        return (
            f"You just mapped {areas_explored} area{'s' if areas_explored > 1 else ''} "
            "of what matters to you. That's the compass — when I suggest actions, "
            "they'll be connected to what you actually care about, not generic advice."
        )
