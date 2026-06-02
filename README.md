# 🏙️ Emergent City

> A beautiful 2D emergent behavior simulation of a living city — 100–200 agents with personalities, needs, factions, economy, crime, cults, and stories that emerge on their own. No scripted plot. Just people, in a world.

**Inspired by:** Dwarf Fortress · The Sims · Black & White · RimWorld · Streets of Rogue · Disco Elysium

![Status](https://img.shields.io/badge/status-active%20development-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## ✨ What is this?

Emergent City is a city simulator where nothing is scripted. Each citizen has:
- A name, age, gender, and a **Big Five personality** + 2–3 unique traits
- Needs: hunger, fatigue, safety, money, social status, meaning/fun, belonging
- A memory of important events
- Current goals and long-term ambitions
- Relationships with others (love, hate, debt, fear)

You drop 150 of them into a procedurally-generated city, press play, and **stories happen on their own.**

After a few in-game weeks you'll see:
- 🏚️ Slums forming on the city edge as poor citizens cluster
- 💎 Wealthy districts forming around the center
- 🔪 Gangs emerging from unemployed young men with low agreeableness
- ⛪ Cults forming around charismatic citizens with high openness + low conscientiousness
- 💔 Affairs, betrayals, marriages, murders
- 📰 Celebrities — citizens whose social status snowballs
- 📉 Economic crises when supply chains break
- 🗣️ Rumors and ideas spreading through the social graph

You watch. You don't direct. (Unless you turn on God Mode.)

---

## 🧠 Architecture: Hybrid AI

The hardest problem in 200-agent simulation is **cost**. Calling an LLM for every agent every tick = bankruptcy in 5 minutes.

So Emergent City uses a **hybrid system**:

| Layer | What it does | When it runs | Cost |
|---|---|---|---|
| **Rule-based / Utility AI** | 80–85% of behavior. Walk to job. Eat when hungry. Sleep when tired. Avoid danger. Score actions by need-weighted utility. | Every tick, for every agent | Free |
| **LLM (OpenRouter)** | 15–20% of decisions. Important, narrative moments: "should I betray my friend?", "should I start a cult?", "do I fall in love?" Triggered by life events. | Only on big events, with strict rate-limiting and caching | A few cents per hour |

Models: `google/gemini-2.5-flash`, `qwen/qwen-3-8b`, `google/gemma-3-12b-it`. Cheap, fast, narratively decent.

---

## 🎨 Visuals

- **Top-down tile map** with depth shading (toggleable isometric projection planned)
- **Day/night cycle** with dynamic lighting and warm window glow at night
- **Mood-tinted sprites** — citizens visibly carry their emotional state (green = happy, red = angry, blue = sad, gray = numb)
- **Particle effects**: smoke from factories, fire when buildings burn, graffiti on slum walls, growing vegetation in parks, trash in poor districts
- **Camera**: smooth pan + zoom + follow-citizen mode

---

## 📦 Project Structure

```
emergent_city/
├── main.py                   # Entry point, game loop
├── config.py                 # All tunables in one place
├── requirements.txt
├── world/
│   ├── __init__.py
│   ├── world.py              # Main world container
│   ├── tile_map.py           # Tile grid + biomes (slum, residential, downtown, park, industrial)
│   ├── buildings.py          # Houses, shops, factories, parks
│   ├── economy.py            # Goods, prices, supply/demand
│   ├── time_system.py        # Day/night, calendar, seasons
│   └── events.py             # World events: fires, crimes, deaths, births
├── agents/
│   ├── __init__.py
│   ├── agent.py              # The Agent class
│   ├── personality.py        # Big Five + unique traits
│   ├── needs.py              # Need decay + satisfaction
│   ├── memory.py             # Important events
│   ├── relationships.py      # Social graph
│   ├── utility_ai.py         # Action scoring
│   ├── actions.py            # All possible actions (eat, sleep, work, socialize, fight, ...)
│   ├── factions.py           # Gangs, cults, companies
│   └── name_generator.py     # Procedural names
├── rendering/
│   ├── __init__.py
│   ├── renderer.py           # Pygame draw orchestrator
│   ├── camera.py             # Pan, zoom, follow
│   ├── sprites.py            # Sprite cache + mood tinting
│   ├── lighting.py           # Day/night overlay + window glow
│   ├── particles.py          # Smoke, fire, growth
│   └── tile_renderer.py      # Optimized tile blitting
├── llm/
│   ├── __init__.py
│   ├── openrouter_client.py  # Async OpenRouter client w/ rate limiting
│   ├── prompts.py            # All prompt templates
│   ├── decision_router.py    # Decides WHEN to call the LLM
│   └── cache.py              # LRU cache for decisions
├── ui/
│   ├── __init__.py
│   ├── hud.py                # Time controls, speed, paused state
│   ├── event_feed.py         # Scrolling feed of narrative events
│   ├── agent_panel.py        # Click an agent → see everything about them
│   ├── god_mode.py           # Cheats / spawning / disasters
│   └── save_load.py          # Persist/restore world
├── data/
│   ├── names_male.txt
│   ├── names_female.txt
│   ├── surnames.txt
│   └── saves/                # World snapshots
├── utils/
│   ├── __init__.py
│   ├── pathfinding.py        # A* with caching
│   ├── spatial_hash.py       # Fast neighbor queries
│   ├── logger.py             # Structured event log
│   └── random_utils.py       # Seeded RNG helpers
└── README.md
```

---

## 🚀 Getting Started

### 1. Install

```bash
git clone https://github.com/leatag/emergent-city.git
cd emergent-city
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure (optional)

Copy `.env.example` to `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

If you don't add a key, the simulation still runs — it just won't use the LLM for narrative decisions (rule-based fallback kicks in).

### 3. Run

```bash
python main.py
```

---

## 🎮 Controls

| Key | Action |
|---|---|
| `Space` | Pause / play |
| `1` / `2` / `3` | Speed: 1x / 5x / 20x |
| `Mouse drag` | Pan camera |
| `Scroll wheel` | Zoom |
| `Click agent` | Open agent panel |
| `F` | Follow selected agent |
| `G` | Toggle God Mode |
| `Tab` | Toggle event feed |
| `Ctrl+S` / `Ctrl+L` | Save / load world |
| `Esc` | Menu |

---

## 🔧 Tuning

Almost everything is in `config.py`:
- World size, agent count, tick rate
- Need decay rates
- Crime/cult/faction emergence thresholds
- LLM model + when to call it
- Render scale, color palettes, lighting

---

## 🧪 Performance

Target: **150–200 agents at 60 FPS** on a modern laptop.

- Spatial hash for O(1) neighbor lookup
- Pathfinding cached per (origin, destination, tile-map-hash)
- Utility AI scoring vectorized where possible
- LLM calls async, never blocking the game loop
- Sprite blitting batched per tile chunk

---

## 🛣️ Roadmap

- [x] Tile map + buildings + day/night
- [x] Agents with Big Five, needs, memory
- [x] Utility AI + action system
- [x] Relationships + social graph
- [x] Economy + jobs
- [x] LLM integration via OpenRouter
- [x] Factions: gangs, cults, companies
- [x] Event feed UI
- [x] Save/load
- [ ] Isometric projection mode
- [ ] More biomes (waterfront, industrial wasteland)
- [ ] Generational time: marriages → children → aging → death → inheritance
- [ ] Mod loader for custom traits / events / buildings

---

## 📜 License

MIT. Build whatever you want with this.

---

## 🙏 Credits

Built with love by a developer who wanted to watch a city live and die on its own. Inspired by every emergent narrative game ever made.
