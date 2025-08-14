"""
Critic module for evaluating actions and providing feedback
"""

from typing import Any

from ..operator.action import Action, action
from ..operator.types import State


class Critic:
    """
    Evaluates actions and their outcomes to provide feedback
    Inspired by actor-critic reinforcement learning patterns
    """

    def __init__(self, model_provider: str | None = None):
        self.model_provider = model_provider
        self.evaluation_history = []

    async def evaluate_action(
        self,
        action: Action,
        state_before: State,
        state_after: State,
        goal: str | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        """
        Evaluate if an action was successful and provide feedback

        Returns:
            - success: Whether the action achieved its intended effect
            - reason: Explanation of the evaluation
            - suggestions: Dict with improvement suggestions
        """
        evaluation = {
            "action": action,
            "state_change": self._analyze_state_change(state_before, state_after),
            "goal_alignment": self._check_goal_alignment(action, goal)
            if goal
            else None,
        }

        # Determine success based on state change
        success = evaluation["state_change"]["changed"]

        # Generate reason
        if success:
            reason = "Action executed successfully with observable state change"
        else:
            reason = "No observable state change detected"

        # Generate suggestions
        suggestions = self._generate_suggestions(evaluation)

        # Store in history
        self.evaluation_history.append(
            {
                "action": action,
                "success": success,
                "reason": reason,
                "suggestions": suggestions,
            }
        )

        return success, reason, suggestions

    async def critique_plan(
        self, plan: list[Action], current_state: State, goal: str
    ) -> dict[str, Any]:
        """
        Critique a plan before execution

        Returns:
            Dict with critique including potential issues and improvements
        """
        critique = {
            "feasibility": self._assess_feasibility(plan, current_state),
            "efficiency": self._assess_efficiency(plan),
            "risks": self._identify_risks(plan),
            "improvements": [],
        }

        # Generate improvement suggestions
        if not critique["feasibility"]["is_feasible"]:
            critique["improvements"].append(
                {
                    "type": "feasibility",
                    "suggestion": "Revise plan to address feasibility issues",
                }
            )

        if critique["efficiency"]["score"] < 0.7:
            critique["improvements"].append(
                {
                    "type": "efficiency",
                    "suggestion": "Consider optimizing action sequence",
                }
            )

        return critique

    async def suggest_correction(
        self, failed_action: Action, error: str, state: State
    ) -> Action | None:
        """
        Suggest a corrected action after failure
        """
        # Analyze the failure
        failure_analysis = self._analyze_failure(failed_action, error, state)

        # Generate correction based on failure type
        if failure_analysis["type"] == "parameter_error":
            # Adjust parameters
            corrected_params = self._adjust_parameters(
                failed_action.params, failure_analysis["details"]
            )
            return action(failed_action['type'], **corrected_params)

        return None

    def _analyze_state_change(self, before: State, after: State) -> dict[str, Any]:
        """Analyze differences between states"""
        return {
            "changed": before != after,
            "timestamp_diff": after.timestamp - before.timestamp
            if after.timestamp and before.timestamp
            else 0,
        }

    def _check_goal_alignment(self, action: Action, goal: str) -> bool:
        """Check if action aligns with goal"""
        # Simplified check - would use LLM in production
        return True

    def _generate_suggestions(self, evaluation: dict[str, Any]) -> dict[str, Any]:
        """Generate improvement suggestions based on evaluation"""
        suggestions = {}

        if not evaluation["state_change"]["changed"]:
            suggestions["retry"] = "Consider retrying with adjusted parameters"
            suggestions["alternative"] = "Try a different action type"

        return suggestions

    def _assess_feasibility(self, plan: list[Action], state: State) -> dict[str, Any]:
        """Assess if a plan is feasible given current state"""
        return {
            "is_feasible": True,  # Simplified
            "issues": [],
        }

    def _assess_efficiency(self, plan: list[Action]) -> dict[str, Any]:
        """Assess plan efficiency"""
        return {
            "score": 0.8,  # Simplified scoring
            "redundant_actions": [],
        }

    def _identify_risks(self, plan: list[Action]) -> list[dict[str, Any]]:
        """Identify potential risks in plan"""
        risks = []

        # Check for potentially destructive actions
        for action in plan:
            if action.type in ["delete", "remove", "clear"]:
                risks.append(
                    {"action": action, "risk_type": "data_loss", "severity": "high"}
                )

        return risks

    def _analyze_failure(
        self, action: Action, error: str, state: State
    ) -> dict[str, Any]:
        """Analyze why an action failed"""
        # Simplified analysis
        if "parameter" in error.lower():
            return {"type": "parameter_error", "details": {"error": error}}

        return {"type": "unknown", "details": {"error": error}}

    def _adjust_parameters(
        self, params: dict[str, Any], details: dict[str, Any]
    ) -> dict[str, Any]:
        """Adjust action parameters based on failure analysis"""
        # Simplified adjustment
        adjusted = params.copy()

        # Example adjustments
        if "x" in adjusted and "y" in adjusted:
            # Slightly adjust coordinates
            adjusted["x"] = adjusted["x"] + 5
            adjusted["y"] = adjusted["y"] + 5

        return adjusted
