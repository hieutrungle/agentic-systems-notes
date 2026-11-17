"""Animate proposal, measurement, and the incumbent decision."""

from manim import (
    BLUE_B,
    DOWN,
    FadeIn,
    FadeOut,
    GREEN_B,
    RED_B,
    RIGHT,
    RoundedRectangle,
    Scene,
    Text,
    UP,
    VGroup,
)

from labs.autoresearch import run


class AutoResearchLoop(Scene):
    def construct(self):
        report = run(2)
        self.camera.background_color = "#102130"

        title = Text("AutoResearch: one decision per trial", font_size=44).to_edge(UP)
        panels = VGroup()
        for label in ("Proposal", "Validation MAE", "Decision"):
            frame = RoundedRectangle(width=3.8, height=2.0, corner_radius=0.2, color=BLUE_B)
            heading = Text(label, font_size=26).move_to(frame.get_center() + UP * 0.55)
            panels.add(VGroup(frame, heading))
        panels.arrange(RIGHT, buff=0.3)

        incumbent = Text(
            f"Incumbent: {report.baseline}  |  MAE: {report.baseline_validation_mae:g}",
            font_size=30,
        ).next_to(panels, DOWN, buff=0.55)
        self.play(FadeIn(title), FadeIn(panels), FadeIn(incumbent))

        best_error = report.baseline_validation_mae
        for trial in report.trials:
            if trial.accepted:
                best_error = trial.validation_mae
            decision = "Keep" if trial.accepted else "Discard"
            color = GREEN_B if trial.accepted else RED_B
            values = (
                Text(f"Predict {trial.candidate}", font_size=32),
                Text(f"{trial.validation_mae:g}", font_size=32),
                Text(decision, color=color, font_size=32),
            )
            for panel, value in zip(panels, values):
                value.move_to(panel.get_center() + DOWN * 0.35)
                self.play(FadeIn(value), run_time=0.45)

            updated = Text(
                f"Incumbent: {trial.incumbent}  |  MAE: {best_error:g}", font_size=30
            ).move_to(incumbent)
            self.play(FadeOut(incumbent), FadeIn(updated))
            incumbent = updated
            self.wait(1.3)
            self.play(*(FadeOut(value) for value in values), run_time=0.35)
