"""Animate the transfer of control from a fixed workflow to a bounded policy."""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Create,
    FadeIn,
    FadeOut,
    Line,
    RoundedRectangle,
    Scene,
    Text,
    VGroup,
)


BACKGROUND = "#102130"
TEXT = "#ecf1f6"
BLUE = "#a9c4ef"
GOLD = "#e2bd6f"


def panel(label, detail, width, color=BLUE):
    frame = RoundedRectangle(
        width=width, height=1.32, corner_radius=0.15, color=color, stroke_width=2
    )
    heading = Text(label, font_size=29, color=color)
    description = Text(detail, font_size=20, color=TEXT)
    contents = VGroup(heading, description).arrange(DOWN, buff=0.17)
    contents.move_to(frame)
    return VGroup(frame, contents)


def connect(left, right):
    return Arrow(
        left.get_right(), right.get_left(), buff=0.08, color=BLUE, stroke_width=3
    )


class AgentControlLoop(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND

        title = Text("1. One model call", color=TEXT, font_size=43).to_edge(UP, buff=0.6)
        request = panel("Input", "request", 2.3)
        model = panel("Model", "generate", 2.3)
        answer = panel("Answer", "return a value", 2.3)
        VGroup(request, model, answer).arrange(RIGHT, buff=0.7).shift(UP * 0.45)
        single_call = VGroup(
            request, model, answer, connect(request, model), connect(model, answer)
        )
        role = Text("The caller decides what happens next.", font_size=28, color=GOLD)
        role.next_to(single_call, DOWN, buff=0.55)
        self.add(title, single_call, role)
        self.wait(3)
        self.play(FadeOut(title), FadeOut(single_call), FadeOut(role), run_time=0.45)

        title = Text("2. Fixed workflow", color=TEXT, font_size=43).to_edge(UP, buff=0.6)
        draft = panel("Draft", "model writes", 2.6)
        check = panel("Check", "code checks", 2.6)
        format_result = panel("Format", "code formats", 2.6)
        VGroup(draft, check, format_result).arrange(RIGHT, buff=0.7).shift(UP * 0.45)
        fixed_workflow = VGroup(
            draft, check, format_result, connect(draft, check), connect(check, format_result)
        )
        role = Text("The program owns the order: draft, check, format.", font_size=28, color=GOLD)
        role.next_to(fixed_workflow, DOWN, buff=0.55)
        self.play(FadeIn(title), FadeIn(fixed_workflow), FadeIn(role))
        self.wait(2.4)
        self.play(FadeOut(title), FadeOut(fixed_workflow), FadeOut(role), run_time=0.45)

        title = Text("3. Feedback-conditioned control", color=TEXT, font_size=43)
        title.to_edge(UP, buff=0.6)
        policy = panel("Model policy", "proposes an action", 3.5)
        runtime = panel("Runtime gate", "checks and dispatches", 3.5, GOLD)
        environment = panel("Environment", "runs the trial", 3.3)
        VGroup(policy, runtime, environment).arrange(RIGHT, buff=0.59).shift(UP * 0.65)
        forward = VGroup(connect(policy, runtime), connect(runtime, environment))

        feedback_height = -1.14
        feedback_start = environment.get_bottom()
        feedback_right = [feedback_start[0], feedback_height, 0]
        feedback_left = [policy.get_center()[0], feedback_height, 0]
        feedback = VGroup(
            Line(feedback_start, feedback_right, color=GOLD, stroke_width=3),
            Line(feedback_right, feedback_left, color=GOLD, stroke_width=3),
            Arrow(feedback_left, policy.get_bottom(), buff=0, color=GOLD, stroke_width=3),
        )

        self.play(FadeIn(title), FadeIn(policy), FadeIn(runtime), FadeIn(environment))
        self.play(Create(forward), run_time=0.6)

        trials = (
            ("Propose trial", "Run authorized", "Small gain, high variance", "Observe uncertainty"),
            ("Propose replication", "New seed authorized", "Gain still uncertain", "Update the run state"),
        )
        for index, (proposal, authorization, result, observation) in enumerate(trials):
            proposed = Text(proposal, font_size=25, color=BLUE).next_to(policy, UP, buff=0.25)
            authorized = Text(authorization, font_size=25, color=GOLD).next_to(runtime, UP, buff=0.25)
            observed = Text(result, font_size=25, color=BLUE).next_to(environment, UP, buff=0.25)
            returned = Text(observation, font_size=26, color=GOLD).move_to(LEFT * 0.3 + DOWN * 1.55)
            self.play(FadeIn(proposed), run_time=0.55)
            self.play(FadeIn(authorized), run_time=0.55)
            self.play(FadeIn(observed), run_time=0.55)
            if index == 0:
                self.play(Create(feedback), FadeIn(returned), run_time=0.85)
            else:
                self.play(FadeIn(returned), run_time=0.7)
            self.wait(2.2)
            self.play(FadeOut(VGroup(proposed, authorized, observed, returned)), run_time=0.4)

        takeaway = Text(
            "The architectural shift is delegated\ncontrol over a trajectory.",
            font_size=43,
            color=TEXT,
            line_spacing=1.1,
        ).move_to(DOWN * 0.05)
        self.play(FadeOut(VGroup(title, policy, runtime, environment, forward, feedback)))
        self.play(FadeIn(takeaway))
        self.wait(3)
