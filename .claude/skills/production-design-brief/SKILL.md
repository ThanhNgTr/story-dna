---
name: production-design-brief
description: |
  Generate visual design specifications from production guide. Defines color grading,
  lighting setup, set dressing, costume details, prop continuity, and mood boards
  per scene. Outputs design brief for production designer, costume designer, and
  color grader. Ready for design review or AI video generation. Triggers on:
  "production design", "visual design", "art direction", "costume brief", "color grading".
---

# Production Design Brief: Visual Design & Art Direction

## When to Use

Use this skill after `/direct-video` to specify:
- Color palette + grading (LUT, curves, saturation targets)
- Lighting setup (key, fill, practicals, color temperature)
- Set dressing (furniture, props, background elements)
- Costume details (wardrobe continuity, damage progression, color significance)
- Prop continuity (where objects appear, how they change across shots)
- Mood boards (reference images for tone/style)

**Input**: `production_guide.json` (from `/direct-video`)
**Output**: `design_brief.md` + `design_specifications.json`

## Quick Start

```
/production-design-brief --production-guide data/scripts/generated/production_guide.json \
  --visual-reference "desaturated teal + warm amber practicals" \
  --production-quality "high-gloss AI photoreal"
```

## How It Works

### Color Grading Philosophy

**HOLLOW PINE look**:
- **Desaturation**: 60–70% (moody, sophisticated, premium)
- **Teal shift**: Cool shadows (blue-green color cast)
- **Warm practicals**: Only element at 100% saturation (amber, gold, orange)
- **Contrast**: High (blacks = 10 IRE, whites = 85 IRE; crushed shadows, bright practicals)
- **Clarity**: Soft (slight diffusion on midtones; crispness on practicals)

### Color Palette Rules

| Element | Color Temp (K) | Saturation | Purpose |
|---|---|---|---|
| **Practicals (torch, window)** | 3200K (warm amber) | 100% | Only color in scene, draws eye |
| **Moonlight** | 5600K (cool blue) | 0% (desaturated) | Location (night), emotional distance |
| **Fog** | 5600K | -20% (slightly blue) | Atmosphere, mystery, obscurity |
| **Skin tone** | 5600K | 60% (desaturated) | Ghostly, vulnerable, controlled |
| **Uniforms (navy)** | 5600K | 40% (washed out) | Authority without warmth, institutional |

### Lighting Setup Pattern (Practicals-Only Philosophy)

❌ **No key light from above** — unrealistic, studio look
✅ **Practicals only** — torch held by character, moonlight from off-screen, window light

**Rationale**: In a phone-free school with no electricity (implied), light comes only from torch, moon, and lit windows. This constraint = visual authenticity + visual storytelling (light sources reveal character intent).

---

## Output Format

### Production Design Brief (Markdown)

```markdown
# PRODUCTION DESIGN BRIEF: Episode Title
**Visual Language** Desaturated teal + warm amber practicals
**Production Quality** High-gloss photoreal AI
**Aspect Ratio** 9:16 vertical

---

## COLOR PALETTE

### Master LUT (Lookup Table)

**Curves (Post-Production Grading)**:
- **Shadows**: Lift to 70 IRE (clean blacks, moody but not crushed)
- **Midtones**: Desaturate to 60% (reduce warmth, increase distance)
- **Highlights**: Push to 100% on practicals only; reduce to 85% on ambient (hot spots on torch, windows; soften on faces)

**Color Shift**:
- **Blue channel**: +15 in shadows (cool moonlight), +5 in midtones (teal cast)
- **Red channel**: -10 overall (remove warmth), +30 on practicals only (torch isolation)
- **Green channel**: -5 (reduce vibrancy)

**Saturation Curve**:
- **Shadows**: 0% (desaturated blacks, pure grey-blue)
- **Midtones**: 60% (significant desaturation)
- **Highlights**: 100% on practicals (torch, window light), 70% on skin (controlled)

**Result**: Scene looks like **underwater prison** — cool, distant, unreal. Practicals pop (torch = only warmth, only hope).

### Reference Mood Board

*[Visual reference images would show]*:
- Close-up of torch flame (warm amber, detailed)
- Fog-covered pine forest at night (cool, hazy)
- Wet uniforms clinging to bodies (fabric texture, fabric detail)
- Window with silhouette and interior light (backlit, silhouette unreadable)
- Rain on glass (water droplets, refraction)
- Faces lit by torch glow (harsh, dramatic, one side lit)

---

## SCENE 1: COLD OPEN (00:00–00:10, 10s)

### Lighting Setup

**Location**: EXT. FOREST — NIGHT

**Light Sources** (practicals only):
- **Key**: Handheld torch (held by character, moving with protagonist)
- **Fill**: Moonlight (from off-screen, diffused through fog; very dim, ~20% of torch intensity)
- **Rim**: Moonlit fog edges (backlit haze, subtle)
- **Special**: None (no additional rigs)

**Intensity**:
- **Torch**: 100 foot-candles (bright, focused, high contrast)
- **Moonlight**: 5 foot-candles (dim, fill only)
- **Ratio**: 20:1 (torch:moonlight) = high contrast, dramatic shadows

**Color Temperature**:
- **Torch**: 3200K (warm amber)
- **Moonlight**: 5600K (cool blue)
- **Result**: Warm/cool split. Torch side warm, shadow side cool. Creepy asymmetry.

**Fog Characteristics**:
- **Density**: 40% opacity (torch visible through fog, but atmosphere present)
- **Color**: Slight blue tint (moonlight diffusion)
- **Movement**: Slow drift (wind effect; subtle, not theatrical)

### Set Dressing

**Foreground**:
- Dead leaves, moss, ferns (texture, location)
- Fallen branches (obstacle for footsteps, sound design)
- Overgrown ferns obscuring frame edges (depth, confinement)

**Midground**:
- Pine tree trunks (many, creating maze/claustrophobia)
- Sparse undergrowth (not jungle; sparse, Gothic)

**Background**:
- Distant trees (obscured by fog, threatening)
- Possible structure edge (building, gate outline) — where she's running from

**Lighting on Set Elements**:
- **Torch side (left)**: Faces glow with amber; shadows on far side harsh (eye sockets black)
- **Moonlight side (right)**: Cool blue rim on hair/shoulders; face side away from camera dark (mystery)
- **Fog**: Edges of torch beam visible (volumetric light, dramatic)

### Costume & Continuity

**Protagonist Wardrobe** (evolving damage):
- **Cold open state**: Navy blazer (wet, torn sleeve visible), white shirt (muddied), navy tie (crooked), grey skirt (muddy hem)
- **Hair**: Wet, tangled, leaves/twigs caught
- **Accessories**: Ring pendant (silver, glints in torch light; visible in CU), ring on hand (visible)

**Damage progression** (across episode):
- 00:00–00:10 (cold open): Damaged from running
- 10:12 (title card): "48 HOURS EARLIER" — sudden cut to pristine uniform (clean, dry, neat)
- 67:73 (emotional peak): Same uniform, now muddy again (suggests parallel to cold open)
- 83:91 (final hold): Uniform torn at same spots as cold open (visual callback)

**Purpose**: Wardrobe damage is **visual echo** of cold-open terror, appearing again at story climax.

### Color Grading (Scene 1)

**Torch light areas**: Warm amber (3200K), 100% saturation on torch flame, 80% on illuminated fabric
**Moonlight areas**: Cool blue (5600K), 0% saturation (desaturated blue-grey)
**Fog**: Slightly blue (5600K), -20% saturation (neutral, diffused)
**Skin**: 60% saturation (ghostly, vulnerable)

**Contrast**: Crushed shadows (blacks at 10 IRE); torch at 95 IRE (hot, bright); moonlit areas at 40–50 IRE (dim, threatening)

**Visual Effect**: Protagonist is **trapped in low contrast world** (moonlight dim), but torch reveals (hot, bright). Torch = only hope, only clarity. When torch moves away (implied), she's in darkness.

---

## SCENE 7: GROUP ARGUMENT (01:07–01:27, 20s)

### Lighting Setup

**Location**: EXT. COURTYARD — NIGHT, FOG

**Light Sources** (practicals only):
- **Key**: Character-held torches (2–3 torches, moving, held by different characters)
- **Fill**: Moonlight (very dim, fog-diffused)
- **Rim**: Windowlight from distant building (very dim backlight, silhouettes)
- **Special**: None

**Intensity**:
- **Torch**: 80 foot-candles per torch (multiple torches, cumulative light ~150 foot-candles in center; softer than cold open's single torch)
- **Moonlight**: 5 foot-candles (dim fill)
- **Window backlight**: <1 foot-candle (just silhouette, edge-lighting)

**Ratio**: 30:1 (torches:moonlight) = group is lit, but individually shadowed (each character partially in torch light, partially in shadow; psychological: each is alone despite group)

**Color Temperature**:
- **Torches**: 3200K (warm)
- **Moonlight**: 5600K (cool blue)
- **Window backlight**: 4500K (neutral)

**Fog Characteristics**:
- **Density**: 50% (thicker than cold open; torches glow through haze dramatically)
- **Color**: Blue-tinted (moonlight diffusion, cool)
- **Movement**: Slow drift (wind, atmosphere)

### Set Dressing

**Courtyard Elements**:
- **Foreground**: Fog bank (thick, obscures feet; characters emerge from/recede into fog)
- **Left side**: Chain-link fence (where students escape)
- **Right side**: Building wall (where window light comes from, silhouette watching)
- **Center**: Open space (group standing, no furniture, exposed, vulnerable)

**Lighting on Set Elements**:
- **Fence**: Rim-lit by torches (highlights chain pattern, draws attention to escape)
- **Building wall**: Dark, featureless (threat's home)
- **Fog**: Torch light creates visible beams (volumetric, cinematic)
- **Ground**: Wet (rain suggestion; reflective; torches bounce off puddles)

### Costume Continuity

**All characters**:
- Navy blazers, white shirts, ties (institutional uniformity)
- Varying damage levels (protagonist most damaged; allies slightly; agitators less)
- Torch-light creates harsh shadows on faces (expressionistic, emotional)

**Protagonist** (mid-episode state):
- Blazer: Torn sleeve (from cold open), partially dried mud
- Shirt: Disheveled, partially untucked
- Hair: Still tangled, partially dry
- Accessories: Ring pendant visible (glints in torch light); clutches it during tension moments

**Progression**: Uniform state mirrors emotional state (damage = vulnerability).

### Color Grading (Scene 7)

**Torch-lit areas**: Warm amber (3200K), 90% saturation (torches still dominant color)
**Moonlit areas**: Cool desaturated blue (5600K), 0% saturation
**Window backlight**: Neutral cool (4500K), -10% saturation (barely visible, just silhouette)
**Fog**: Blue-tinted (5600K), -20% saturation (cool, diffused)
**Skin**: 55% saturation (more desaturated than cold open; characters are mentally/emotionally more disconnected)

**Contrast**: Moderate (not crushed like cold open; more visible due to multiple torches). Shadows at 30 IRE; highlights at 90 IRE (less extreme than cold open).

**Visual Effect**: **Group is more visible than protagonist alone** (multiple light sources), but **each character is psychologically isolated** (partially in shadow, partially lit; no one fully illuminated). Visual metaphor: together but apart.

---

## SCENE 9: FINAL HOLD (01:23–01:31, 8s)

### Lighting Setup

**Location**: COURTYARD/BUILDING EDGE — NIGHT

**Light Sources** (practicals only):
- **Key**: Torch (handheld, but now stationary or very slow movement)
- **Fill**: Moonlight (dim)
- **Backlight**: Window light (now more prominent; character watching from inside)
- **Rim**: Torch edge-lighting

**Intensity**:
- **Torch**: 100 foot-candles (focused, sharp lighting for defiant stare)
- **Moonlight**: 5 foot-candles
- **Window**: 10 foot-candles (more visible now; threat is present, not implied)

**Ratio**: 10:1 (torch:moonlight; widest ratio yet) = protagonist is brightest thing in frame (her defiance is lit)

**Color Temperature**:
- **Torch**: 3200K (warm on her face)
- **Moonlight**: 5600K (cool rim)
- **Window**: 4500K (neutral interior, watching)

**Fog**: Light (20% density; clear sightline to protagonist and window)

### Set Dressing

**Foreground**:
- Protagonist centered, sharp focus
- Classmates at frame edges (partially visible, less lit)

**Background**:
- Building wall with window (backlit interior glow; silhouette visible in window)
- Fog clearing (threat is visible, no longer obscured)
- No escape visible (implies trap)

**Lighting on Set Elements**:
- **Protagonist face**: High-key torch light, sharp shadows (defiant, resolved)
- **Classmates**: Darker, less lit (supporting, not central)
- **Window**: Glow from inside (warm interior light, contrasts with cool exterior)
- **Silhouette in window**: Rim-lit by interior light (defined, visible, but still faceless)

### Costume State

**Protagonist** (final state):
- Blazer: Torn, mud-caked (full damage from cold open now visible)
- Shirt: Disheveled, torn collar (suggests restraint/struggle)
- Hair: Wet, tangled (full echo of cold open)
- Ring pendant: Clearly visible in torch light (glints with resolve)

**Classmates**:
- Flanking her, gripping arms (visible in frame edge)
- Uniforms obscured by darkness (faceless, not individuals)

**Visual callback**: Protagonist's wardrobe damage now matches cold-open damage perfectly (visual echo: beginning = ending).

### Color Grading (Scene 9)

**Protagonist face**: Warm torch light (3200K), 100% saturation on torch flame, 85% on skin (more saturated than mid-episode; her resolve brings warmth back)
**Window interior**: Neutral (4500K), 70% saturation (warm inside, cold outside = threat is warm, inviting?)
**Moonlight rim**: Cool (5600K), 0% saturation
**Fog**: Almost clear (blue-tinted, minimal)

**Contrast**: High (torch at 95 IRE; moonlight at 40 IRE; window at 70 IRE; blacks at 15 IRE)

**Visual Effect**: **Protagonist is brightest element** (her defiance is lit). Window watcher visible but not dominant. **Threat is present, but she is not afraid** (defiant stare, no clutching pendant in fear — she's resolved).

---

## COSTUME EVOLUTION (Full Episode)

| Scene | Blazer | Shirt | Hair | Pendant | Emotional State |
|---|---|---|---|---|---|
| Cold open (00–10) | Torn, wet | Muddied, torn | Wet, tangled | Clutched (fear) | Terror |
| Title/setup (10–22) | Clean, dry, pressed | White, neat | Dry, combed | Not visible (pristine) | Calm, guarded |
| Authority (22–38) | Clean | Clean | Neat | Barely visible | Wary |
| Mystery object (38–47) | Clean | Clean | Neat | Visible (curiosity) | Curious |
| Escape (47–57) | Increasingly muddy | Dirty hem | Messy | Clutched (urgency) | Determined |
| Conflict (57–67) | Muddied, torn sleeve | Disheveled, untucked | Tangled | Clutched (tension) | Conflicted |
| Peak (67–73) | Torn, muddy | Torn, blood(?), disheveled | Tangled, wet | Clutched hard (grief) | Grief, resolution |
| Watched (73–83) | Damaged state | Damaged state | Damaged state | Visible, resolute | Watched, defiant |
| Final hold (83–91) | Full damage (cold-open mirror) | Full damage | Full damage | Clearly visible | Defiant, trapped |

**Visual storytelling**: Her uniform goes from **pristine** (setup) → **progressively damaged** (through conflict) → **full damage** (mirrors cold open exactly). The wardrobe itself is a **visual narrative arc** (order → chaos → resolution, but no escape).

---

## PROP CONTINUITY & SIGNIFICANCE

| Prop | Appearance | Significance | Evolution |
|---|---|---|---|
| **Ring pendant** | Visible always (worn at throat) | Character tell (clutches when afraid) | Clutch frequency increases: cold open (often) → calm scenes (rare) → peak (constant) → final hold (visible, resolute, not clutching) |
| **Torch** | Practical light source | Reveals/conceals (on/off shows truth/danger) | Held by different characters (who controls light = power dynamic) |
| **ELI portrait** | One scene (38–47) | Central mystery object | Scratched "STILL HERE"; protagonist touches it with ally watching (shared responsibility) |
| **RULES board** | One scene (22–38) | World exposition (rules are illegible on screen — mystery) | Text unreadable (authority without explanation) |
| **Window** | Multiple scenes (backlit silhouette) | Threat presence | Appears in cold open (background), argument (background), final hold (prominent). Gradual reveal. |
| **Torch flame** | Every practical torch scene | Warmth amid darkness; only color | Torch near protagonist = safety; torch away = danger; torch out = death |

**Prop storytelling**: Objects evolve in significance (pendant goes from clutch to resolve; window goes from background to foreground; torch is always present but meaning shifts).

---

## GRADING SPECIFICATIONS (For Color Grader)

### LUT Settings

**Primary Grade** (base look):
- **Desaturation**: -40 points (global, reduce saturation 40%)
- **Shadows**: Lift 20 points (reduce crush, increase visibility in shadows)
- **Midtones**: -10 saturation (greyish, cool)
- **Highlights**: Clamp to 90 IRE (avoid blown-out whites)

**Color Shift**:
- **Shadows**: +Blue 20 points, -Red 5 points (cool shadows)
- **Midtones**: +Blue 10 points, -Red 10 points, -Green 5 points (cool, desaturated)
- **Highlights**: +Red 15 points (practicals pop warm)

**Secondary Grade** (practicals isolation):
- **Torch areas**: Desaturate background -60 points, keep torch at +100 saturation (torch pops)
- **Window areas**: Keep interior warm (+20 red), exterior cool (+20 blue)

### Delivery

**Final format**:
- Rec. 709 (broadcast) + LOG (Higgsfield/AI processing)
- 10-bit color (for shadow detail retention)
- Slog2 curve (if shooting RAW)

---

## Implementation Notes

### For Production Designer
- Source: Practical torches (battery-powered, safe for AI/human shoot)
- Set dressing: Sparse, Gothic (Gothic school aesthetic, not cluttered)
- Fog machine: High-output, slow-drift movement
- Props: Ring pendant (silver, reflective), ELI portrait (sepia, cracked glass), RULES board (illegible text)

### For Costume Designer
- Navy uniform: Specific shade (dark navy, not black)
- Damage progression: Plan tear/mud placement; must be consistent across scenes
- Pendant chain: Thin silver, drapes at throat (visible in torch light, CU's)
- Ring: Simple, silver, grey-green stone (matches pendant metal)

### For Color Grader
- LUT provided above (desaturation, cool shadows, warm practicals isolation)
- Key deliverable: Practicals must be ONLY saturated element
- Skin tone: Desaturated, ghostly (not healthy)
- Window backlight: Neutral interior (no color cast decision yet)

### For AI Video Generation (Higgsfield)
- Color palette: "desaturated teal shadows, warm amber practicals (only saturated color), high contrast"
- Lighting: "practicals only — torch (3200K), moonlight (5600K), window backlight; no key light from above"
- Special: "volumetric fog, torch glow through haze, rain reflections on ground"
- Costume evolution: Provide wardrobe state per scene (clean → damaged progression)
