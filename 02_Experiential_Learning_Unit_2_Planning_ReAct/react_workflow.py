"""
react_workflow.py — ReAct Travel Planner for a 3-day Mumbai business trip.

Uses the Thought → Action → Observation loop with dynamic replanning when
the first hotel availability check fails (sold out).
"""

import os
import json
from typing import Any


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class TravelToolError(Exception):
    pass


# ---------------------------------------------------------------------------
# Mock tools (no external APIs needed)
# ---------------------------------------------------------------------------

_hotel_check_count = 0


def reset_travel_tool_state():
    global _hotel_check_count
    _hotel_check_count = 0


def search_flights(origin: str, destination: str, date: str) -> dict:
    return {
        "status": "success",
        "flights": [
            {"flight": "AI-665", "from": origin, "to": destination,
             "date": date, "price_rs": 6800, "duration": "2h 15m", "seats": 12},
            {"flight": "6E-204", "from": origin, "to": destination,
             "date": date, "price_rs": 5950, "duration": "2h 30m", "seats": 4},
        ],
        "cheapest_rs": 5950,
    }


def check_hotel_availability(hotel_name: str, checkin: str, checkout: str) -> dict:
    """First call is always sold out; second call succeeds with alternate hotel."""
    global _hotel_check_count
    _hotel_check_count += 1

    if _hotel_check_count == 1:
        raise TravelToolError(
            f"ERR_SOLD_OUT: {hotel_name} is fully booked for {checkin} to {checkout}. "
            "No rooms available."
        )

    # Second call — alternate hotel
    return {
        "status": "available",
        "hotel": "Ibis Mumbai Airport",
        "checkin": checkin,
        "checkout": checkout,
        "price_per_night_rs": 2800,
        "total_rs": 8400,
        "confirmation_code": "IBZ-20261103",
    }


def check_meeting_calendar(attendees: list, date: str, time: str) -> dict:
    return {
        "status": "confirmed",
        "date": date,
        "time": time,
        "attendees": attendees,
        "meeting_room": "Conference Room B – Tata BKC Tower",
        "notes": "Client confirmed; dial-in link sent",
    }


def book_transport(type: str, route: str, date: str) -> dict:
    fares = {"airport_cab": 850, "daily_cab": 650, "metro_pass": 200}
    return {
        "status": "booked",
        "type": type,
        "route": route,
        "date": date,
        "fare_rs": fares.get(type, 500),
        "booking_ref": f"OLA-{hash(route) & 0xFFFF:04X}",
    }


def calculate_budget(components: dict) -> dict:
    total = sum(components.values())
    return {
        "status": "within_budget" if total <= 25000 else "over_budget",
        "components": components,
        "total_rs": total,
        "budget_rs": 25000,
        "remaining_rs": 25000 - total,
    }


# ---------------------------------------------------------------------------
# ReAct Travel Planner
# ---------------------------------------------------------------------------

DIVIDER = "=" * 70


def _box(label: str, text: str) -> str:
    return f"{DIVIDER}\n  {label}\n{DIVIDER}\n  {text}\n"


class ReActTravelPlanner:
    """
    ReAct planner for a 3-day Mumbai business trip.
    Handles hotel-sold-out failure with dynamic replanning.
    """

    goal = "Plan 3-day business trip to Mumbai within budget Rs 25,000 with client meetings"

    def __init__(self):
        self.plan: list[str] = [
            "Step 1: Search flights DEL→BOM",
            "Step 2: Check hotel availability – Hotel Trident BKC",
            "Step 3: Check meeting calendar with client",
            "Step 4: Book airport transport",
            "Step 5: Calculate total budget",
            "Step 6: Confirm itinerary",
        ]
        self.step_index: int = 0
        self.history: list[dict] = []
        self.state: dict[str, Any] = {}
        self.replan_count: int = 0

    # ------------------------------------------------------------------

    def think(self) -> str:
        thoughts = {
            0: ("I should start by searching for flights from Delhi to Mumbai on Nov 3. "
                "I need to stay within Rs 25,000 total, so finding the cheapest flight first "
                "will help me allocate the remaining budget to hotel and transport."),
            1: ("Flights found — cheapest is Rs 5,950. Now I must check hotel availability "
                "near BKC where the client meetings are. My target hotel is Hotel Trident BKC "
                "at Rs 4,000/night. If sold out I will need to replan and try an alternative."),
            2: ("Hotel booked. Next I must confirm the client meeting calendar to make sure "
                "all attendees are available on Nov 4 at 10am."),
            3: ("Meetings confirmed. I need to book airport cab for arrival on Nov 3 and a "
                "daily cab pass for meeting days."),
            4: ("Transport booked. Time to calculate the total trip budget to ensure we are "
                "within Rs 25,000."),
            5: ("Budget looks good. Final step is to confirm the itinerary — summarise everything "
                "and mark the trip as planned."),
            # Replanned hotel step
            6: ("Hotel Trident BKC was sold out. I need to replan and try Ibis Mumbai Airport "
                "which is cheaper at Rs 2,800/night and should still be within budget. "
                "It's slightly further from BKC but manageable with a cab."),
        }
        return thoughts.get(self.step_index, f"Proceeding with: {self.plan[self.step_index]}")

    def act(self, thought: str) -> tuple[str, dict]:
        step_label = self.plan[self.step_index]

        if self.step_index == 0:
            action_str = "search_flights(origin='DEL', destination='BOM', date='2026-11-03')"
            obs = search_flights("DEL", "BOM", "2026-11-03")
            self.state["flight"] = obs["flights"][0]
            self.state["flight_cost_rs"] = obs["cheapest_rs"]
            return action_str, obs

        elif self.step_index == 1:
            # First call raises TravelToolError; replanned step uses same index
            hotel = self.state.get("preferred_hotel", "Hotel Trident BKC")
            action_str = f"check_hotel_availability(hotel_name='{hotel}', checkin='2026-11-03', checkout='2026-11-06')"
            obs = check_hotel_availability(hotel, "2026-11-03", "2026-11-06")
            self.state["hotel"] = obs["hotel"]
            self.state["hotel_cost_rs"] = obs["total_rs"]
            return action_str, obs

        elif self.step_index == 2:
            action_str = "check_meeting_calendar(attendees=['Rajiv Kumar', 'Priya Sharma'], date='2026-11-04', time='10:00')"
            obs = check_meeting_calendar(["Rajiv Kumar", "Priya Sharma"], "2026-11-04", "10:00")
            self.state["meeting"] = obs
            return action_str, obs

        elif self.step_index == 3:
            action_str = "book_transport(type='airport_cab', route='BOM Airport → BKC Hotel', date='2026-11-03')"
            obs = book_transport("airport_cab", "BOM Airport → BKC Hotel", "2026-11-03")
            obs2 = book_transport("daily_cab", "BKC Hotel → Tata Offices", "2026-11-04")
            self.state["transport_cost_rs"] = obs["fare_rs"] + obs2["fare_rs"]
            combined = {"airport_cab": obs, "daily_cab": obs2}
            return action_str, combined

        elif self.step_index == 4:
            components = {
                "flight_rs": self.state.get("flight_cost_rs", 0),
                "hotel_rs": self.state.get("hotel_cost_rs", 0),
                "transport_rs": self.state.get("transport_cost_rs", 0),
                "meals_rs": 3600,
                "misc_rs": 500,
            }
            action_str = f"calculate_budget(components={json.dumps(components)})"
            obs = calculate_budget(components)
            self.state["budget"] = obs
            return action_str, obs

        elif self.step_index == 5:
            obs = {
                "status": "ITINERARY_CONFIRMED",
                "trip": "3-day Mumbai Business Trip",
                "dates": "Nov 3–6, 2026",
                "flight": self.state.get("flight", {}).get("flight"),
                "hotel": self.state.get("hotel"),
                "meetings": self.state.get("meeting", {}).get("date"),
                "total_cost_rs": self.state.get("budget", {}).get("total_rs"),
                "message": "Trip fully planned and confirmed. All bookings complete.",
            }
            self.state["itinerary"] = obs
            return "confirm_itinerary()", obs

        else:
            raise RuntimeError(f"Unhandled step index {self.step_index}")

    def replan(self, error_observation: dict) -> None:
        self.replan_count += 1
        error_msg = error_observation.get("error", "Unknown error")
        print(f"\n{'!' * 70}")
        print(f"  ⚠  REPLANNING EVENT #{self.replan_count}")
        print(f"{'!' * 70}")
        print(f"  Failed step : {self.plan[self.step_index]}")
        print(f"  Error       : {error_msg}")
        print(f"  Strategy    : Try alternate hotel — Ibis Mumbai Airport")
        print(f"{'!' * 70}\n")

        self.plan.pop(self.step_index)
        self.plan.insert(
            self.step_index,
            "Step 2b [REPLANNED]: Check hotel availability – Ibis Mumbai Airport (fallback)",
        )
        self.state["preferred_hotel"] = "Ibis Mumbai Airport"

    # ------------------------------------------------------------------

    def run(self) -> None:
        print(DIVIDER)
        print("  ReAct Travel Planner — Mumbai Business Trip")
        print(f"  Goal: {self.goal}")
        print(DIVIDER)
        print(f"\nInitial plan ({len(self.plan)} steps):")
        for s in self.plan:
            print(f"  • {s}")
        print()

        trace_lines: list[str] = []

        def record(label: str, content: str):
            block = _box(label, content)
            print(block)
            trace_lines.append(block)

        while self.step_index < len(self.plan):
            print(f"\n{'─' * 70}")
            print(f"  {self.plan[self.step_index]}")
            print(f"{'─' * 70}")

            thought = self.think()
            record("===THOUGHT===", thought)

            try:
                action_str, observation = self.act(thought)
                record("===ACTION===", action_str)
                record("===OBSERVATION===", json.dumps(observation, indent=2, ensure_ascii=False))
                self.history.append({"thought": thought, "action": action_str, "observation": observation})
                self.step_index += 1

            except TravelToolError as e:
                err_obs = {"error": str(e), "status": "FAILED"}
                record("===ACTION===", f"check_hotel_availability(hotel_name='Hotel Trident BKC', ...)")
                record("===OBSERVATION===", json.dumps(err_obs, indent=2))
                self.history.append({"thought": thought, "action": "check_hotel_availability(...)", "observation": err_obs})
                self.replan(err_obs)

        summary = (
            "\n" + DIVIDER + "\n"
            "  ✅  TRIP PLANNING COMPLETE\n"
            + DIVIDER + "\n"
            f"  Steps executed   : {len(self.history)}\n"
            f"  Replanning events: {self.replan_count}\n"
            f"  Hotel booked     : {self.state.get('hotel')}\n"
            f"  Total cost       : Rs {self.state.get('budget', {}).get('total_rs')}\n"
            f"  Budget status    : {self.state.get('budget', {}).get('status')}\n"
            + DIVIDER
        )
        print(summary)
        trace_lines.append(summary)

        traces_dir = os.path.join(os.path.dirname(__file__), "traces")
        os.makedirs(traces_dir, exist_ok=True)
        with open(os.path.join(traces_dir, "react_trace.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(trace_lines))
        print(f"\n  Full trace saved → traces/react_trace.txt")

        return {
            "completed_successfully": True,
            "steps_taken": len(self.history),
            "replan_count": self.replan_count,
        }


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    reset_travel_tool_state()
    planner = ReActTravelPlanner()
    planner.run()
