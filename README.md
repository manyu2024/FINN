\# FINN - AI Pentesting Co-pilot



FINN (Forensic Intelligence Network Navigator) is a terminal-based AI assistant built for penetration testers. It combines LLM reasoning, persistent memory, and real-time web search to provide operational, contextual cybersecurity guidance.



\## Features

\- AI-powered pentesting guidance via Llama 3.3-70B (Groq API)

\- Persistent memory across sessions (user profile, goals, projects, findings)

\- Auto web search when AI hits knowledge limits

\- Operational context for commands (runtime, stealth level, prerequisites, alert triggers)

\- Futuristic cyber terminal UI with typewriter effects and ASCII command boxes



\## Tech Stack

\- Python 3.11+

\- Groq API (Llama 3.3-70B)

\- Rich + Colorama (Terminal UI)

\- DuckDuckGo Search (ddgs)

\- JSON persistent storage



\## Setup

```bash

pip install groq colorama rich ddgs

export GROQ\_API\_KEY=your\_key\_here

python finn\_terminal\_2.py

```



\## Commands

| Command | Description |

|---------|-------------|

| /memory | Show stored memory |

| /setgoal | Set career goal |

| /multi | Multi-line input |

| /name | Update your name |

| /forget | Clear all memory |

| /exit | Exit FINN |

