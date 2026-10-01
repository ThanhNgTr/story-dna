---
name: write-story-ep1-tutorial
description: |
  Generate educational video scripts matching the ep1.mp4 style: 
  conversational mentor + learner format, 6s avg shots, professional 
  lighting, educational but engaging tone. Triggers on: "write tutorial 
  script", "create educational script", "ep1 style script". Input: topic, 
  learner level, key teaching points. Output: Script Markdown with dialogue, 
  visual directions, timing. Trained on ep1 DNA patterns.
---

# Educational Tutorial Script Generator

## When to Use This Skill

Use to create educational videos in the style of ep1.mp4:
- Tutorial content with mentor + learner setup
- Clear explanations in conversational tone
- Professional visuals with good pacing
- Suitable for how-to, educational, explanatory content

**Input**: Topic + learner level + key points
**Output**: Markdown script with dialogue, visuals, timing

## Quick Start

```bash
/write-story-ep1-tutorial --topic "How to set up your first project" \
  --level "beginner" \
  --points "1. Install tools 2. Create file 3. Test it"
```

## DNA-Based Rules

### Structure
- **Opening** (0–5s): Hook + intro
- **Content** (5–60s): Main teaching with dialogue
- **Closing** (60–91s): Review + CTA

### Pacing
- Average shot: 6s per shot
- Fast cuts: 2–3s for reactions, key moments
- Long shots: 10–12s for explanations, contemplation
- Transitions: Straight cuts + occasional fades

### Characters
- **Mentor**: Expert, friendly, conversational
  - 65% screen time
  - Explains concepts clearly
  - Uses relatable language (not jargon)
  
- **Learner**: Relatable, curious
  - 35% screen time
  - Asks clarifying questions
  - Shows reactions/understanding

### Tone & Voice
- Educational but NOT boring (no monotone lectures)
- Conversational (like explaining to a friend)
- Casual formality (contractions, natural language)
- Friendly and encouraging (audience feels supported)

### Visual Guidance
- Professional lighting (well-lit, clear visibility)
- Warm color palette with accents for emphasis
- Mix of static shots + smooth pans
- Show, don't just tell (demonstrate visually)

### Audio
- Upbeat background music (contemporary educational vibe)
- Clear dialogue (voiceover + character dialogue)
- Subtle sound effects (transitions, emphasis)

## Script Template

```markdown
# [Topic] — Tutorial Script

**Duration**: 60–90s  
**Characters**: Mentor, Learner

---

## Scene 1: Opening Hook (0–5s)

**Visual**: Establish context with professional wide shot

**Mentor** (direct to camera, friendly smile):
[Hook question or statement that makes learner curious]

**Audio**: Upbeat intro music

---

## Scene 2: Introduction (5–15s)

**Visual**: Medium shot of mentor, maybe learner off-camera

**Mentor**:
[Introduce topic, why it matters, what they'll learn]

**Learner** (off-camera):
[Follow-up question showing relatable confusion]

---

## Scene 3: Main Content (15–60s)

**Visual**: Alternating shots of mentor explaining + demonstration/visual aids

[Repeat for each key point]:

**Point 1**: [3–4 shots covering the concept]
- Mentor explains (medium shot, 10–12s)
- Visual demonstration or screenshot
- Learner asks follow-up (5–6s)
- Mentor clarifies (6–8s)

---

## Scene 4: Closing & CTA (60–91s)

**Visual**: Both mentor + learner, wrap-up shot

**Mentor**:
[Quick recap of what was learned]

**Learner**:
[Shows understanding, asks next step]

**Mentor**:
[Strong CTA: Subscribe, follow up, next tutorial, etc.]

**Audio**: Concluding music swell, fade
```

## Examples

### Example 1: "How to Install Python"
```markdown
# How to Install Python — Tutorial

**Duration**: 75s  
**Characters**: Alex (Mentor/Expert), Jordan (Learner)

---

## Scene 1: Opening (0–5s)
**Visual**: Wide shot of home office, natural lighting

**Alex** (direct to camera):
"Setting up Python can feel intimidating if you've never done it, but I'm going to walk you through it step by step. Let's do it!"

---

## Scene 2: Intro (5–15s)
**Visual**: Medium shot of Alex, maybe split-screen with Jordan

**Alex**:
"First, we're going to grab Python from the official website. You'll want to go to python.org and look for the big download button."

**Jordan** (off-camera):
"Wait, is there a specific version I should get?"

**Alex**:
"Great question! Get the latest stable version — that's usually what's marked as recommended."

---

[Continue with each installation step...]

---

## Scene 5: Closing (65–75s)
**Visual**: Both Alex and Jordan, thumbs up or celebratory gesture

**Alex**:
"And that's it! You've just installed Python. You're ready to start coding."

**Jordan**:
"This was easier than I thought!"

**Alex**:
"Exactly. If you want to learn more, check out the next tutorial on creating your first Python program. Subscribe so you don't miss it!"

**Audio**: Upbeat music swell, fade to black
```

## Generation Rules

1. **Keep it conversational** — Write like you're talking to a friend, not giving a lecture
2. **Show, don't tell** — Include visuals/demonstrations, not just dialogue
3. **Mentor + Learner dynamic** — Alternate between explaining and questioning
4. **Clear time markers** — Include timecode (0–5s, 5–15s, etc.) for each section
5. **Professional tone** — Educational without being stiff
6. **Strong CTA** — End with a clear next action (subscribe, watch next, try it yourself)

## Notes

- Scripts generated follow ep1.mp4 DNA patterns
- Average shot 6s, pacing medium
- Characters: mentor (65%) + learner (35%)
- Tone: educational, conversational, friendly
- For real production, replace [Visual descriptions] with actual shots/B-roll
