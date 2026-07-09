import curses

DEFAULT_BINDINGS = {
    "play_pause": ord(" "),
    "stop": ord("s"),
    "next": ord("n"),
    "prev": ord("b"),
    "volume_up": ord("+"),
    "volume_down": ord("-"),
    "shuffle": ord("r"),
    "repeat": ord("R"),
    "help": ord("?"),
    "sleep_timer": ord("t"),
    "mute": ord("m"),
}

BINDABLE_ACTIONS = list(DEFAULT_BINDINGS.keys())

RESERVED_KEYS = {
    ord("0"), ord("1"), ord("2"), ord("3"), ord("4"),
    ord("q"),
    27,  # Esc
    10, 13,  # Enter
    127, curses.KEY_BACKSPACE,
    curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT,
    curses.KEY_NPAGE, curses.KEY_PPAGE,
    ord("~"), ord("g"), ord("G"), ord("a"), ord("A"), ord("d"), ord("x"),
    ord("C"), ord("c"), ord("e"), ord("D"), ord("["), ord("]"), ord("/"),
    ord("V"), ord("I"), ord("T"), ord("M"), ord("R"),
    ord("j"), ord("k"), ord("h"), ord("l"),
    ord(" "),
    curses.KEY_F1, curses.KEY_F2, curses.KEY_F3,
    curses.KEY_F4, curses.KEY_F5, curses.KEY_F6,
    curses.KEY_F7, curses.KEY_F8, curses.KEY_F9, curses.KEY_F10,
}

# Keys that are only valid in normal mode (not input mode)
# Printable keys (32-126) are handled by input modes


def validate(bindings: dict) -> list[str]:
    errors = []
    key_to_actions = {}
    for action, keycode in bindings.items():
        if action not in BINDABLE_ACTIONS:
            errors.append(f"Acción desconocida: {action}")
            continue
        if keycode in RESERVED_KEYS:
            errors.append(f"Tecla {keycode} reservada para {action}, se usará default")
            continue
        if keycode in key_to_actions:
            other = key_to_actions[keycode]
            errors.append(f"Colisión: {action} y {other} usan tecla {keycode}")
        key_to_actions[keycode] = action
    return errors


def resolve_conflicts(bindings: dict) -> dict:
    result = {}
    seen_keys = set()
    for action in BINDABLE_ACTIONS:
        keycode = bindings.get(action)
        if keycode is None or keycode in RESERVED_KEYS:
            keycode = DEFAULT_BINDINGS[action]
        if keycode in seen_keys:
            keycode = DEFAULT_BINDINGS[action]
            if keycode in seen_keys:
                for a in BINDABLE_ACTIONS:
                    k = DEFAULT_BINDINGS[a]
                    if k not in seen_keys:
                        keycode = k
                        break
        result[action] = keycode
        seen_keys.add(keycode)
    return result


def build_lookup(bindings: dict) -> dict:
    return {keycode: action for action, keycode in bindings.items()}


def key_name(keycode: int) -> str:
    if keycode == ord(" "):
        return "Space"
    if keycode == ord("\t"):
        return "Tab"
    if keycode == 27:
        return "Esc"
    if keycode == curses.KEY_UP:
        return "↑"
    if keycode == curses.KEY_DOWN:
        return "↓"
    if keycode == curses.KEY_LEFT:
        return "←"
    if keycode == curses.KEY_RIGHT:
        return "→"
    if keycode == curses.KEY_NPAGE:
        return "PgDn"
    if keycode == curses.KEY_PPAGE:
        return "PgUp"
    if keycode == curses.KEY_BACKSPACE:
        return "Bksp"
    if curses.KEY_F1 <= keycode <= curses.KEY_F12:
        return f"F{keycode - curses.KEY_F1 + 1}"
    if 32 <= keycode <= 126:
        return chr(keycode)
    return f"\\x{keycode:02x}"
