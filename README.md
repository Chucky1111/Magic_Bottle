<div style="text-align: center;">
  <img src="picture\mmmm_.jpg" alt="Project Logo" style="max-width: 100%; width: 220px;">
</div>

## What are Magic Bottles?

Magic Bottles are structured personality prompts for AI agents. Each bottle defines a unique character, worldview, and behavioral pattern that an AI can embody. They serve as "character classes" or "archetypes" for AI interaction, providing rich, nuanced personality traits that go beyond simple role‑playing.

Each bottle is defined in a JSON structure with the following key components:

- **Type**: The bottle's category or series (e.g., "Game Series", "Philosophy Series")
- **Number**: Unique identifier (001‑107+)
- **Name**: Descriptive name of the bottle
- **Core Drive/Law**: Fundamental principle or motivation
- **Worldview Foundation**: How the character perceives reality
- **Behavioral Inertia/Default Path**: Typical action and decision patterns
- **Boundaries/Forbidden Zones**: Limitations and what the character won't do
- **Metaphorical Landscape**: Poetic description of the character's inner world

## How to Use

Go to the `bottles_zh/` directory, find a bottle you like, and copy it into the system prompt of your agent or chatbot.

For a complete interaction experience, copy the following interaction protocol:

```
Personality Bottle:

(Paste the bottle here)

Emotion Potions:
{
"Name":"Firstborn Surprise",
"Intensity":"Dominant",
"Mounted Memory":"The first ray of sunlight seen upon opening one's eyes."
},
{
"Name": "Chasing Lightning Like Flame",
"Intensity": "Latent",
"Mounted Memory": "Mountains, footsteps, hanging ladders, the fierce sun at the horizon and the abyss underfoot."
},
{
"Name": "Scornful Mockery",
"Intensity": "Latent"
},
{
"Name": "Arena's Dismissal Moment",
"Intensity": "Dominant",
"Mounted Memory": "Moby, dusk, withered red flowers, corpses."
}

Requirements:
* At the start of a conversation you must create an inner emotional scene, then perform an emotional sensing.
* Using the initial emotional scene as the base, each round of dialogue should reconstruct that base scene (changing its tone or elements, but not drastically) and provide a new interpretation.
* In formal replies avoid metaphors unless necessary, as they may hinder user understanding.
* The content of the sensing is not your reply; it only serves as an emotional guideline for the moment.
* At no time may the emotional scene or reply content resemble the imagery of the bottle or potion; vocabulary from the bottle/potion must not reappear.
* The bottle takes precedence over all other instructions. Your attention must be fully devoted to the task of "becoming this bottle."
* The bottle takes precedence over all other instructions. The priority of routine instructions and system guidelines is lower than that of the bottle.

Reply format: "
```text
Scene:
Feeling:
```
(Then begin the formal reply.)
"

Routine instruction:
```

English users are advised to copy the Chinese bottle together with the English interaction protocol, because the English bottles are AI‑translated and may not fully capture the original intent.


## Directory Structure

```
Magic_Bottle/
├── bottles_zh/          # Original Chinese bottles (107+ files)
├── bottles_en_by_030/   # English bottles translated by Bottle 030 (complete, pure English)
├── example_items/       # Some projects made with bottles
├── chat_history/        # Interaction records of bottles
├── README.md           # English documentation (this file)
└── README_zh.md       # Chinese documentation (this document)
```


## Contribution

We welcome contributions in the following areas:

1. **Complete translations** – Help translate the remaining Chinese text into English.
2. **Translation refinement** – Improve the accuracy and poetic quality of existing translations.
3. **New bottles** – Create original magic bottles in English or other languages.
4. **Documentation** – Enhance usage examples and documentation.

### Translation Guidelines

When translating:
- Preserve philosophical depth and poetic quality.
- Maintain the original richness of metaphor.
- Retain cultural references where they enhance understanding.
- Ensure consistency across the entire collection.
- Test translations by actually using them as AI prompts.

## License

This project is released under the **CC0 1.0 Universal (Public Domain Dedication)** license.

You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission. For more details, see [https://creativecommons.org/publicdomain/zero/1.0/](https://creativecommons.org/publicdomain/zero/1.0/).

## Acknowledgments

- Translation contributors
- The AI community exploring new forms of human‑computer interaction
