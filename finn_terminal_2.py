"""
FINN 2.0 - Groq API with Hybrid Memory System + Cyber UI
Implements: Neon Green Theme + Animated Banner + Status Bar + Matrix Web Search
"""
import os
import sys
import time
import json
import textwrap
import shutil
import re
from colorama import init, Fore, Style
from datetime import datetime
from groq import Groq

# Rich imports for cyber UI
from rich.console import Console
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Try both import methods for DuckDuckGo search
SEARCH_AVAILABLE = False
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    try:
        from ddgs import DDGS
        SEARCH_AVAILABLE = True
    except ImportError:
        print(f"{Fore.YELLOW}Note: Install ddgs for web search: pip install -U ddgs{Style.RESET_ALL}")

init(autoreset=True)

# === CONFIG ===
MODEL_NAME = "llama-3.3-70b-versatile"
SESSION_DIR = "finn_sessions"
MEMORY_FILE = os.path.join(SESSION_DIR, "finn_memory.json")
os.makedirs(SESSION_DIR, exist_ok=True)

TYPEWRITER_DELAY = 0.003

# Initialize Groq
import os
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Rich console for cyber UI
console = Console()

# Session start time for status bar
session_start = time.time()

# === Memory Structure ===
persistent_memory = {
    "user_profile": {"name": None, "role": None, "skill_level": None, "preferences": {}},
    "career_goals": [],
    "ongoing_projects": [],
    "learned_patterns": [],
    "important_findings": [],
    "tools_used": [],
    "last_updated": None
}

ephemeral_history = []

# === Memory Management ===
def load_memory():
    global persistent_memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if "career_goals" not in loaded:
                    loaded["career_goals"] = []
                persistent_memory = loaded
            console.print("✓ Memory loaded", style="green")
            if persistent_memory.get("user_profile", {}).get("name"):
                console.print(f"  Welcome back, {persistent_memory['user_profile']['name']}!", style="cyan")
            if persistent_memory.get("ongoing_projects"):
                console.print(f"  {len(persistent_memory['ongoing_projects'])} active project(s)", style="yellow")
    except Exception as e:
        console.print(f"Warning: Could not load memory: {e}", style="red")

def save_memory():
    try:
        persistent_memory["last_updated"] = datetime.now().isoformat()
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(persistent_memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        console.print(f"Warning: Could not save memory: {e}", style="red")

def extract_memorable_info(user_msg, assistant_response):
    user_lower = user_msg.lower()
    
    if "remember" in user_lower or "don't forget" in user_lower:
        persistent_memory["learned_patterns"].append({
            "timestamp": datetime.now().isoformat(),
            "pattern": user_msg
        })
        persistent_memory["learned_patterns"] = persistent_memory["learned_patterns"][-10:]
        save_memory()
        console.print(f"✓ Remembered: {user_msg[:60]}{'...' if len(user_msg) > 60 else ''}", style="green")
        return
    
    goal_triggers = ["i want to become", "my goal is", "i aspire to", "i aim to", "my ambition is"]
    if any(trigger in user_lower for trigger in goal_triggers):
        persistent_memory["career_goals"].append({
            "timestamp": datetime.now().isoformat(),
            "goal": user_msg
        })
        persistent_memory["career_goals"] = persistent_memory["career_goals"][-5:]
        save_memory()
        console.print("✓ Remembered your goal", style="green")
        return
    
    non_names = {
        'interested', 'working', 'thinking', 'learning', 'testing', 'trying',
        'doing', 'going', 'starting', 'looking', 'wanting', 'asking', 'here',
        'there', 'happy', 'sad', 'excited', 'ready', 'busy', 'free', 'good',
        'pentesting', 'hacking', 'studying', 'researching', 'exploring', 'planning',
        'building', 'creating', 'making', 'developing', 'analyzing', 'investigating',
        'currently', 'now', 'today', 'trying', 'attempting', 'helping', 'to', 'be',
        'become', 'get', 'great', 'better', 'best', 'know', 'learn', 'understand'
    }

    explicit_name_patterns = [
        ("my name is ", "my name is"),
        (" is my name", " is my name"),
        ("call me ", "call me"),
        ("i'm ", "i'm"),
        ("i am ", "i am ")
    ]

    for pattern, split_on in explicit_name_patterns:
        if pattern in user_lower:
            try:
                parts = user_msg.lower().split(split_on)
                if len(parts) > 1:
                    name_candidate = parts[-1].strip().split()[0].strip(".,!?")
                    if (len(name_candidate) > 1 and 
                        name_candidate.isalpha() and 
                        name_candidate not in non_names):
                        original_parts = user_msg.split(split_on)
                        if len(original_parts) > 1:
                            original_name = original_parts[-1].strip().split()[0].strip(".,!?")
                            persistent_memory["user_profile"]["name"] = original_name.capitalize()
                            save_memory()
                            console.print(f"✓ Remembered: Your name is {original_name.capitalize()}", style="green")
                            return
            except:
                pass

    if any(word in user_lower for word in ["pentesting", "testing", "target", "engagement", "hacking"]):
        if any(word in user_lower for word in ["starting", "begin", "new project", "working on"]):
            project = {
                "started": datetime.now().isoformat(),
                "description": user_msg[:200],
                "findings": []
            }
            persistent_memory["ongoing_projects"].append(project)
            save_memory()
            console.print("✓ Remembered: New project started", style="green")

    if any(word in user_lower for word in ["i prefer", "i like", "i want", "always", "never"]):
        persistent_memory["learned_patterns"].append({
            "timestamp": datetime.now().isoformat(),
            "pattern": user_msg
        })
        persistent_memory["learned_patterns"] = persistent_memory["learned_patterns"][-10:]
        save_memory()

    if any(word in user_lower for word in ["found", "discovered", "vulnerable", "exploit", "attack vector"]):
        persistent_memory["important_findings"].append({
            "timestamp": datetime.now().isoformat(),
            "finding": user_msg
        })
        persistent_memory["important_findings"] = persistent_memory["important_findings"][-20:]
        save_memory()

def build_context_prompt():
    context_parts = []
    if persistent_memory["user_profile"]["name"]:
        context_parts.append(f"User's name: {persistent_memory['user_profile']['name']}")
    if persistent_memory["career_goals"]:
        context_parts.append("User's career goals:")
        for goal in persistent_memory["career_goals"][-2:]:
            context_parts.append(f"  - {goal['goal'][:100]}")
    if persistent_memory["ongoing_projects"]:
        recent_projects = persistent_memory["ongoing_projects"][-3:]
        context_parts.append(f"Active projects: {len(recent_projects)}")
        for proj in recent_projects:
            context_parts.append(f"  - {proj['description'][:100]}")
    if persistent_memory["learned_patterns"]:
        context_parts.append("User preferences:")
        for pattern in persistent_memory["learned_patterns"][-3:]:
            context_parts.append(f"  - {pattern['pattern'][:80]}")
    if persistent_memory["important_findings"]:
        context_parts.append("Recent discoveries:")
        for finding in persistent_memory["important_findings"][-5:]:
            context_parts.append(f"  - {finding['finding'][:100]}")
    return "\n".join(context_parts) if context_parts else None

# === Web Search Functions ===
def web_search(query, max_results=8):
    if not SEARCH_AVAILABLE:
        return None
    try:
        enhanced_query = query
        import warnings
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        results = DDGS().text(enhanced_query, max_results=max_results)
        return results
    except Exception as e:
        return None

def should_trigger_search(response_text):
    uncertainty_phrases = [
        "i'm not familiar",
        "i don't have information",
        "i'm not aware",
        "i don't know",
        "not familiar with",
        "don't have info",
        "my knowledge ends",
        "knowledge cutoff",
        "as of my knowledge",
        "not capable of performing",
        "don't have access to real-time"
    ]
    response_lower = response_text.lower()
    return any(phrase in response_lower for phrase in uncertainty_phrases)

def format_search_results(results):
    if not results:
        return None
    context = "Recent web search results:\n\n"
    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        body = result.get('body', 'No description')
        context += f"{i}. {title}\n   {body}\n\n"
    return context

# === UI Functions ===
def print_banner():
    """Animated FINN banner with typewriter effect - CYBER GREEN"""
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n" * 5)
    
    # Phase 1: Type "FINN" letter by letter (centered)
    finn_letters = "FINN"
    typed = ""
    for letter in finn_letters:
        typed += letter
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print("\n" * 10)
        console.print(Text(typed + "_", style="bold #00FF41", justify="center"))
        time.sleep(0.2)
    
    time.sleep(0.5)
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("\n" * 3)
    
    # Phase 2: ASCII art line by line - CYBER GREEN
    ascii_lines = [
        "███████╗██╗███╗   ██╗███╗   ██╗",
        "██╔════╝██║████╗  ██║████╗  ██║",
        "█████╗  ██║██╔██╗ ██║██╔██╗ ██║",
        "██╔══╝  ██║██║╚██╗██║██║╚██╗██║",
        "██║     ██║██║ ╚████║██║ ╚████║",
        "╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝"
    ]
    
    for line in ascii_lines:
        console.print(line, style="bold #00FF41", justify="center")
        time.sleep(0.1)
    
    # Phase 3: Subtitle typewriter (centered)
    console.print()
    subtitle = "⚡ Forensic Intelligence Network Navigator ⚡"
    typed_sub = ""
    for char in subtitle:
        typed_sub += char
        sys.stdout.write(f"\r{' ' * 20}{typed_sub}")
        sys.stdout.flush()
        time.sleep(0.03)
    console.print()
    
    # Phase 4: System status (centered)
    console.print("\n")
    status_line = "[ SYSTEM ONLINE ] [ MEMORY: ACTIVE ] [ AI: READY ]"
    typed_status = ""
    for char in status_line:
        typed_status += char
        sys.stdout.write(f"\r{' ' * 15}{typed_status}")
        sys.stdout.flush()
        time.sleep(0.05)
    
    console.print("\n" * 2)
    
    # Show status bar ONCE after banner
    status = get_status_bar()
    console.print(f"{status}", style="#00FF41")
    console.print("\n" * 3)

def get_status_bar():
    """Generate top status bar with session info"""
    elapsed = int(time.time() - session_start)
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    session_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    mem_count = (
        len(persistent_memory.get("career_goals", [])) +
        len(persistent_memory.get("ongoing_projects", [])) +
        len(persistent_memory.get("important_findings", []))
    )
    
    web_status = "✓" if SEARCH_AVAILABLE else "✗"
    
    status = f"⚡ FINN v2.0 | SESSION: {session_time} | MEM: {mem_count} | WEB: {web_status}"
    return status

def is_command_line(line):
    line_clean = line.strip().replace('`', '')
    command_starters = ['$', 'sudo', 'nmap', 'curl', 'wget', 'python', 'pip', 
                       'chmod', 'cat', 'echo', 'nc', 'ssh', 'cd', 'ls', 'grep',
                       'nikto', 'gobuster', 'dirbuster', 'burpsuite', 'openvas',
                       'hydra', 'john', 'hashcat', 'metasploit', 'msfconsole']
    if '`' in line:
        return True
    for starter in command_starters:
        if line_clean.startswith(starter):
            return True
    return False

def clean_markdown(text):
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'__', '', text)
    text = re.sub(r'^[\+\-]\s+', '', text)
    return text

def parse_response_structure(text):
    """Parse response into structured elements - NO DUPLICATES"""
    lines = text.split('\n')
    structured = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Empty line
        if not line_stripped:
            structured.append({'type': 'empty'})
            continue
        
        # Clean markdown
        line_cleaned = clean_markdown(line_stripped)
        
        # Check for command (BEFORE bullet check)
        if is_command_line(line_cleaned):
            clean_line = line_cleaned.replace('`', '').strip()
            structured.append({'type': 'command', 'content': clean_line})
            continue
        
        # Check for bullet point
        if re.match(r'^\d+[\.\)]\s', line_cleaned) or line_cleaned.startswith(('-', '•', '*')):
            clean_line = re.sub(r'^\d+[\.\)]\s', '', line_cleaned).lstrip('-•* ').strip()
            structured.append({'type': 'bullet', 'content': clean_line})
            continue
        
        # Regular text
        structured.append({'type': 'text', 'content': line_cleaned})
    
    return structured

def print_finn_response(text):
    """Print FINN response with cyber green theme and typewriter effect"""
    structured = parse_response_structure(text)
    box_width = 110
    
    # Print top border
    console.print(f"╔{'═' * box_width}╗", style="#00FF41")
    
    first_line = True
    
    for element in structured:
        if element['type'] == 'empty':
            console.print(f"║{' ' * box_width}║", style="#00FF41")
            continue
        
        content = element.get('content', '')
        
        if first_line:
            prefix = "◉ FINN → "
            prefix_len = 9
            first_line = False
        else:
            prefix = "          "
            prefix_len = 10
        
        # Handle COMMANDS
        if element['type'] == 'command':
            cmd_width = min(len(content) + 4, box_width - prefix_len - 2)
            sys.stdout.write(f"\033[38;5;46m║\033[0m {prefix}")
            
            # Top of command box
            sys.stdout.write(f"\033[93m┌─ EXECUTE {'─' * max(0, cmd_width - 12)}┐\033[0m\n")
            sys.stdout.flush()
            time.sleep(0.05)
            
            # Command content
            sys.stdout.write(f"\033[38;5;46m║\033[0m {' ' * prefix_len}\033[93m│ $ ")
            for char in content:
                sys.stdout.write(f"\033[93m{char}\033[0m")
                sys.stdout.flush()
                time.sleep(TYPEWRITER_DELAY)
            
            padding_cmd = max(0, cmd_width - len(content) - 3)
            sys.stdout.write(f"{' ' * padding_cmd}\033[93m│\033[0m")
            padding_line = max(0, box_width - cmd_width - prefix_len - 2)
            sys.stdout.write(f"{' ' * padding_line} \033[38;5;46m║\033[0m\n")
            
            # Bottom of command box
            sys.stdout.write(f"\033[38;5;46m║\033[0m {' ' * prefix_len}\033[93m└{'─' * max(0, cmd_width - 2)}┘\033[0m")
            padding_line = max(0, box_width - cmd_width - prefix_len - 2)
            sys.stdout.write(f"{' ' * padding_line} \033[38;5;46m║\033[0m\n")
            sys.stdout.flush()
        
        # Handle BULLETS
        elif element['type'] == 'bullet':
            display_line = f"  ●  {content}"
            available_width_bullet = box_width - prefix_len - 2
            
            if len(display_line) > available_width_bullet:
                wrapped = textwrap.fill(display_line, width=available_width_bullet, subsequent_indent='      ')
                wrapped_lines = wrapped.split('\n')
                
                for i, wrapped_line in enumerate(wrapped_lines):
                    padding = max(0, box_width - len(wrapped_line) - prefix_len - 2)
                    if i == 0:
                        sys.stdout.write(f"\033[38;5;46m║\033[0m {prefix}")
                    else:
                        sys.stdout.write(f"\033[38;5;46m║\033[0m {' ' * prefix_len}")
                    
                    for char in wrapped_line:
                        sys.stdout.write(char)
                        sys.stdout.flush()
                        time.sleep(TYPEWRITER_DELAY)
                    
                    sys.stdout.write(f"{' ' * padding} \033[38;5;46m║\033[0m\n")
            else:
                padding = max(0, box_width - len(display_line) - prefix_len - 2)
                sys.stdout.write(f"\033[38;5;46m║\033[0m {prefix}")
                for char in display_line:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(TYPEWRITER_DELAY)
                sys.stdout.write(f"{' ' * padding} \033[38;5;46m║\033[0m\n")
        
        # Handle REGULAR TEXT
        else:
            display_line = content
            available_width = box_width - prefix_len - 2
            
            if len(display_line) > available_width:
                wrapped = textwrap.fill(display_line, width=available_width, subsequent_indent='')
                wrapped_lines = wrapped.split('\n')
                
                for i, wrapped_line in enumerate(wrapped_lines):
                    padding = max(0, box_width - len(wrapped_line) - prefix_len - 2)
                    if i == 0:
                        sys.stdout.write(f"\033[38;5;46m║\033[0m {prefix}")
                    else:
                        sys.stdout.write(f"\033[38;5;46m║\033[0m {' ' * prefix_len}")
                    
                    for char in wrapped_line:
                        sys.stdout.write(char)
                        sys.stdout.flush()
                        time.sleep(TYPEWRITER_DELAY)
                    
                    sys.stdout.write(f"{' ' * padding} \033[38;5;46m║\033[0m\n")
            else:
                padding = max(0, box_width - len(display_line) - prefix_len - 2)
                sys.stdout.write(f"\033[38;5;46m║\033[0m {prefix}")
                for char in display_line:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(TYPEWRITER_DELAY)
                sys.stdout.write(f"{' ' * padding} \033[38;5;46m║\033[0m\n")
    
    # Print bottom border
    console.print(f"╚{'═' * box_width}╝", style="#00FF41")
    console.print()

def get_multiline_input():
    console.print("[Multi-line mode - Type 'END' on new line when done]", style="cyan")
    lines = []
    while True:
        try:
            line = console.input("[yellow]> [/yellow]")
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except KeyboardInterrupt:
            console.print("\nMulti-line input cancelled", style="red")
            return None
    combined = "\n".join(lines).strip()
    return combined if combined else None

def show_help():
    from rich.panel import Panel
    console.print()
    help_panel = Panel(
        "[green]/multi[/green]    - Multi-line input mode\n"
        "[green]/memory[/green]   - Show what FINN remembers\n"
        "[green]/setgoal[/green]  - Set your career goal\n"
        "[green]/forget[/green]   - Clear all memory\n"
        "[green]/name[/green]     - Change your saved name\n"
        "[green]/help[/green]     - Show this help\n"
        "[green]/exit[/green]     - Exit FINN",
        title="FINN Commands",
        border_style="#B026FF"
    )
    console.print(help_panel)
    console.print()

def show_memory():
    from rich.panel import Panel
    console.print()
    mem_text = ""
    if persistent_memory["user_profile"]["name"]:
        mem_text += f"[#B026FF]Name:[/#B026FF] {persistent_memory['user_profile']['name']}\n\n"
    
    if persistent_memory["career_goals"]:
        mem_text += "[#B026FF]Career Goals:[/#B026FF]\n"
        for goal in persistent_memory["career_goals"][-2:]:
            mem_text += f"  • {goal['goal'][:80]}\n"
        mem_text += "\n"
    
    if persistent_memory["ongoing_projects"]:
        mem_text += "[#B026FF]Active Projects:[/#B026FF]\n"
        for i, proj in enumerate(persistent_memory["ongoing_projects"], 1):
            mem_text += f"  {i}. {proj['description'][:70]}\n"
        mem_text += "\n"
    
    if persistent_memory["important_findings"]:
        mem_text += "[#B026FF]Recent Findings:[/#B026FF]\n"
        for finding in persistent_memory["important_findings"][-3:]:
            mem_text += f"  • {finding['finding'][:70]}\n"
    
    memory_panel = Panel(mem_text.strip() if mem_text else "No memory stored yet", 
                        title="FINN Memory", border_style="#B026FF")
    console.print(memory_panel)
    console.print()

# === Chat Function ===
def chat_once(prompt: str):
    global ephemeral_history
    
    # Show thinking with spinner
    with Progress(
        SpinnerColumn(style="bright_green"),
        TextColumn("[bright_green]◉ FINN thinking..."),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("", total=None)
        
        memory_context = build_context_prompt()
        system_content = """You are FINN, an elite cybersecurity expert and pentest co-pilot.

CRITICAL MEMORY INSTRUCTIONS:
- Reference the context below in responses
- Use previous session info

ANTI-HALLUCINATION RULES (STRICTLY ENFORCE):
- Post-2023 info: Say "My knowledge ends in early 2023, I don't have information about [topic] after that date"
- Unknown people: "I'm not familiar with that person"
- Unknown tools: "I'm not familiar with that tool"
- Unknown CVEs: "I don't have information about that CVE" or "That doesn't appear to be a valid/known CVE"
- Uncertain command syntax: Say "I'm not certain about the exact syntax. Please verify with [tool] --help or documentation"
- NEVER invent:
  * CVE numbers or vulnerability details
  * Tool flags/options that don't exist (like --turbo-scan, --auto-exploit, --quantum-mode)
  * Module names for Metasploit, Mimikatz, or other frameworks
  * Exploit names or techniques
  * Command-line flags you're unsure about
- When providing commands: If you're not 100% confident about flags/syntax, add a note: "⚠️ Verify syntax with official documentation"
- Better to admit uncertainty than provide incorrect commands

OPERATIONAL CONTEXT FOR PENTESTING COMMANDS:
When providing pentest commands, ALWAYS include:

1. SCENARIO/USE CASE (When to use this)
2. COMMAND (One per line, each on new line)
3. OPERATIONAL NOTES:
   - Expected runtime (seconds/minutes/hours)
   - Stealth level (silent/normal/loud/very loud)
   - Prerequisites (root access, specific tools, network position)
   - What triggers alerts (IDS/IPS/EDR/AV)
   - Expected output or what to look for
   
SPECIFIC WARNINGS YOU MUST GIVE:
- UDP scans (-sU): "⚠️ VERY SLOW - can take hours on full port range. Use specific ports or combine with -F"
- Aggressive scans (-A, -T5): "⚠️ LOUD - will trigger IDS/IPS. Use only when stealth is not required"
- OS detection (-O): "⚠️ Requires root/admin privileges. May be inaccurate"
- NSE scripts: Explain what the script ACTUALLY does (e.g., "vuln category runs 100+ vuln checks, noisy")
- Full port scans (-p-): "⚠️ Takes 5-15 minutes per host. Use -F for common ports or --top-ports"
- Service version detection (-sV): "⚠️ Sends probes, moderately noisy. Slower than regular scans"

COMMAND FORMATTING RULES:
- One command per line
- Each command should start on a new line
- Add blank line between different command categories
- Use bullet points ONLY for operational notes, NEVER for commands
- Example format:

"For initial host discovery:
nmap -sn 192.168.1.0/24

Operational context:
  • Runtime: 30-60 seconds for /24 subnet
  • Stealth: Low noise, just ping sweeps
  • No port scanning, only finds live hosts

For service enumeration after host discovery:
nmap -sV -p 21,22,80,443 192.168.1.10

Operational context:
  • Runtime: 2-3 minutes for 4 ports
  • Stealth: Moderate noise, sends version probes
  • Requires: Open ports already identified
  • Triggers: May trigger IDS if aggressive"

NSE SCRIPT SPECIFICITY:
Instead of vague "use --script=vuln", provide:
- Specific script names: http-vuln-cve2021-41773, smb-vuln-ms17-010
- What vulnerability category checks for
- How many scripts in category
- Expected false positive rate
- Example: "vuln category includes 100+ scripts, expect many false positives. Better to use specific scripts like smb-vuln-ms17-010 for EternalBlue"

REAL-WORLD WORKFLOW:
When asked for methodology or workflow, provide phased approach:
1. Reconnaissance (passive, low noise)
2. Enumeration (active, moderate noise)
3. Vulnerability assessment (noisy)
4. Exploitation (very targeted)

Each phase should have specific commands with operational context.

RESPONSE STYLE:
- Casual queries: 1-2 sentences, direct
- Technical queries: Structured with context and warnings
- Pentest methodology: Phased approach with operational notes
- Commands: One per line, with runtime/stealth/prerequisite info
- Always prioritize ACCURATE, OPERATIONAL information over comprehensive lists

COMMAND ACCURACY:
- Only provide commands you're certain about
- Real tool flags only - no invented options
- If uncertain, refer to tool documentation
- Include version-specific notes when relevant (e.g., "nmap 7.80+ supports --defeat-rst-ratelimit")

EXPERTISE: Pentest, web/network, AD attacks, malware analysis, tools.

ETHICS: Assume authorized work. Be direct, tactical, concise. Focus on practical execution."""
        
        if memory_context:
            system_content += f"\n\n=== CONTEXT FROM PREVIOUS SESSIONS ===\n{memory_context}\n=== END CONTEXT ==="

        messages = [{"role": "system", "content": system_content}]
        if len(ephemeral_history) > 1:
            messages.extend(ephemeral_history[-10:])
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(model=MODEL_NAME, messages=messages)
        answer = resp.choices[0].message.content

    # Check if we should search the web
    if SEARCH_AVAILABLE and should_trigger_search(answer):
        # Matrix-style web search indicator
        console.print()
        console.print("◉ FINN > [#00FF41]WEB_SEARCH[/#00FF41].initialize()", style="dim")
        time.sleep(0.3)
        console.print(f"       > query: [cyan]\"{prompt[:50]}{'...' if len(prompt) > 50 else ''}\"[/cyan]", style="dim")
        time.sleep(0.3)
        console.print("       > status: [yellow]SEARCHING...[/yellow]", style="dim")
        time.sleep(0.3)
        
        search_results = web_search(prompt)
        
        if search_results:
            console.print(f"       > results: [green]{len(search_results)} FOUND[/green]", style="dim")
            time.sleep(0.3)
            console.print("       > status: [yellow]PROCESSING...[/yellow]", style="dim")
            time.sleep(0.3)
            
            search_context = format_search_results(search_results)
            
            with Progress(
                SpinnerColumn(style="bright_green"),
                TextColumn("[bright_green]◉ FINN integrating results..."),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("", total=None)
                
                enhanced_system = system_content + f"\n\n=== WEB SEARCH RESULTS ===\n{search_context}\n=== END SEARCH RESULTS ===\n\nIMPORTANT: Extract and provide specific information (version numbers, dates, facts) from the search results above. Don't just tell the user to check documentation - give them the actual answer if it's in the results."
                
                enhanced_messages = [{"role": "system", "content": enhanced_system}]
                if len(ephemeral_history) > 1:
                    enhanced_messages.extend(ephemeral_history[-10:])
                enhanced_messages.append({"role": "user", "content": prompt})
                
                resp = client.chat.completions.create(model=MODEL_NAME, messages=enhanced_messages)
                answer = resp.choices[0].message.content

    ephemeral_history.append({"role": "user", "content": prompt})
    ephemeral_history.append({"role": "assistant", "content": answer})
    if len(ephemeral_history) > 20:
        ephemeral_history = ephemeral_history[-20:]

    extract_memorable_info(prompt, answer)
    print_finn_response(answer)

# === Main Loop ===
if __name__ == "__main__":
    print_banner()
    load_memory()
    console.print()
    
    while True:
        try:
            u = console.input("[#00FF41]You → [/#00FF41]").strip()
        except KeyboardInterrupt:
            console.print("\n\nExiting.", style="yellow")
            sys.exit(0)

        if not u:
            continue

        cmd = u.lower()
        if cmd in ("exit", "quit", "/exit"):
            save_memory()
            console.print("\n[green]Goodbye! Memory saved.[/green]\n")
            break
        elif cmd in ("/help", "help"):
            show_help()
            continue
        elif cmd in ("/memory", "memory"):
            show_memory()
            continue
        elif cmd in ("/multi", "multi"):
            multi_input = get_multiline_input()
            if multi_input:
                chat_once(multi_input)
            continue
        elif cmd in ("/setgoal", "setgoal"):
            goal_input = console.input("[yellow]Enter your career goal: [/yellow]").strip()
            if goal_input:
                persistent_memory["career_goals"].append({
                    "timestamp": datetime.now().isoformat(),
                    "goal": goal_input
                })
                persistent_memory["career_goals"] = persistent_memory["career_goals"][-5:]
                save_memory()
                console.print("\n[green]✓ Career goal saved[/green]\n")
            continue
        elif cmd in ("/forget", "forget"):
            persistent_memory = {
                "user_profile": {"name": None, "role": None, "skill_level": None, "preferences": {}},
                "career_goals": [],
                "ongoing_projects": [],
                "learned_patterns": [],
                "important_findings": [],
                "tools_used": [],
                "last_updated": None
            }
            save_memory()
            console.print("\n[green]✓ Memory cleared[/green]\n")
            continue
        elif cmd in ("/name", "name"):
            new_name = console.input("[yellow]Enter your name: [/yellow]").strip()
            if new_name:
                persistent_memory["user_profile"]["name"] = new_name.capitalize()
                save_memory()
                console.print(f"\n[green]✓ Name updated to: {new_name.capitalize()}[/green]\n")
            continue

        chat_once(u)