"""Simulador docente de MT para L = {a^n b^n | n >= 1}."""
import html
from copy import deepcopy

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Máquina de Turing | aⁿbⁿ", page_icon="🧠", layout="wide")

BLANK = "□"
ACCEPT = "q_acepta"
REJECT = "q_rechaza"
HALT = {ACCEPT, REJECT}

# (estado, símbolo leído) -> (estado nuevo, símbolo escrito, dirección)
RULES = {
    ("q0", "X"): ("q0", "X", "R"),
    ("q0", "a"): ("q1", "X", "R"),
    ("q0", "Y"): ("q4", "Y", "R"),
    ("q1", "a"): ("q1", "a", "R"),
    ("q1", "Y"): ("q2", "Y", "R"),
    ("q1", "b"): ("q3", "Y", "L"),
    ("q2", "Y"): ("q2", "Y", "R"),
    ("q2", "b"): ("q3", "Y", "L"),
    ("q3", "a"): ("q3", "a", "L"),
    ("q3", "b"): ("q3", "b", "L"),
    ("q3", "X"): ("q3", "X", "L"),
    ("q3", "Y"): ("q3", "Y", "L"),
    ("q3", BLANK): ("q0", BLANK, "R"),
    ("q4", "Y"): ("q4", "Y", "R"),
    ("q4", BLANK): (ACCEPT, BLANK, "R"),
}

ROLE = {
    "q0": "Buscar la siguiente a no marcada",
    "q1": "Buscar una b y detectar el inicio de la zona Y",
    "q2": "Buscar una b después de marcas Y",
    "q3": "Regresar al blanco izquierdo",
    "q4": "Verificar que solo queden Y",
    ACCEPT: "Cadena aceptada",
    REJECT: "Cadena rechazada",
}

# Las combinaciones restantes rechazan con transición explícita.
for q in ("q0", "q1", "q2", "q3", "q4"):
    for symbol in ("a", "b", "X", "Y", BLANK):
        RULES.setdefault((q, symbol), (REJECT, symbol, "R"))


def initial_snapshot(word: str) -> dict:
    return {
        "state": "q0", "head": 0,
        "tape": {i: c for i, c in enumerate(word)},
        "step": 0, "last": None,
    }


def advance(snapshot: dict) -> dict:
    """Una transición determinista, con cinta no acotada en ambos sentidos."""
    if snapshot["state"] in HALT:
        return deepcopy(snapshot)
    result = deepcopy(snapshot)
    state, head = result["state"], result["head"]
    read = result["tape"].get(head, BLANK)
    to, write, movement = RULES[(state, read)]
    if write == BLANK:
        result["tape"].pop(head, None)
    else:
        result["tape"][head] = write
    result["head"] = head + (1 if movement == "R" else -1)
    result["state"] = to
    result["step"] += 1
    result["last"] = (state, read, write, movement, to)
    return result


def initialize(word: str) -> None:
    st.session_state.history = [initial_snapshot(word)]
    st.session_state.cursor = 0
    st.session_state.running = False
    st.session_state.current_word = word


def step_forward() -> None:
    s = st.session_state
    if s.cursor + 1 < len(s.history):
        s.cursor += 1
    elif s.history[-1]["state"] not in HALT and len(s.history) < 1001:
        s.history.append(advance(s.history[-1]))
        s.cursor += 1
    else:
        s.running = False


def step_backward() -> None:
    st.session_state.running = False
    st.session_state.cursor = max(0, st.session_state.cursor - 1)


def reset() -> None:
    initialize(st.session_state.current_word)


def run_to_end() -> None:
    st.session_state.running = False
    for _ in range(1000):
        if st.session_state.history[st.session_state.cursor]["state"] in HALT:
            break
        step_forward()


def tape_html(snap: dict) -> str:
    tape, head = snap["tape"], snap["head"]
    # Se incluye un blanco a cada extremo y el cabezal, incluso fuera de la entrada.
    keys = list(tape) + [head, -1, len(st.session_state.current_word)]
    lo, hi = min(keys) - 1, max(keys) + 1
    cells = []
    for pos in range(lo, hi + 1):
        symbol = tape.get(pos, BLANK)
        color = "#2563eb" if symbol == "X" else "#059669" if symbol == "Y" else "#172554"
        active = pos == head
        cells.append(
            f'<div class="cell-wrap"><div class="head-label">'
            f'{html.escape(snap["state"]) + " ↓" if active else "&nbsp;"}</div>'
            f'<div class="cell {"active" if active else ""}" style="color:{color}">'
            f'{html.escape(symbol)}</div><div class="pos">{pos}</div></div>'
        )
    return '<div class="tape">' + "".join(cells) + '</div>'


st.markdown("""
<style>
.stApp {background:linear-gradient(140deg,#eff6ff 0%,#f8fafc 53%,#ecfeff 100%)}
.tape {display:flex;overflow-x:auto;gap:0;padding:12px 0 16px;align-items:flex-end}
.cell-wrap {flex:0 0 57px;text-align:center}
.cell {height:57px;display:flex;align-items:center;justify-content:center;border:1.5px solid #94a3b8;
       font-family:ui-monospace,monospace;font-size:26px;font-weight:700;background:white;margin-left:-1.5px}
.cell.active {background:#bfdbfe;border:3px solid #2563eb;border-radius:3px}
.head-label {height:25px;font-size:13px;color:#1d4ed8;font-weight:800}
.pos {font-size:11px;color:#64748b;margin-top:5px}
.topic {font-weight:650;color:#0f172a}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Simulador de Máquina de Turing")
st.markdown(r"**Lenguaje:** $L=\{a^n b^n\mid n\geq 1\}$ · **Entrada:** $\Sigma=\{a,b\}$ · **Cinta:** $\Gamma=\{a,b,X,Y,\square\}$")
st.caption("X representa una 'a' emparejada; Y representa una 'b' emparejada. El cabezal puede desplazarse a izquierda o derecha.")

if "history" not in st.session_state:
    initialize("aabb")

with st.sidebar:
    st.header("Configurar entrada")
    examples = ["aabb", "ab", "aaabbb", "aab", "abb", "abab", "", "ba"]
    chosen = st.selectbox("Ejemplos", examples, index=0, format_func=lambda s: s or "ε (vacía)")
    word = st.text_input("Cadena (solo a y b)", value=chosen, max_chars=16)
    if st.button("Cargar cadena", use_container_width=True, type="primary"):
        if any(c not in "ab" for c in word):
            st.error("La cadena debe contener exclusivamente a y b.")
        else:
            initialize(word)
    st.divider()
    st.markdown("**Significado de estados**")
    for state, description in ROLE.items():
        st.caption(f"**{state}:** {description}")

# El fragmento permite una reproducción automática sin bloquear la interfaz.
@st.fragment(run_every=st.session_state.get("speed", 0.8) if st.session_state.get("running", False) else None)
def simulator():
    if st.session_state.running:
        step_forward()
    s = st.session_state.history[st.session_state.cursor]
    state = s["state"]
    if state in HALT:
        st.session_state.running = False

    st.subheader("Cinta y cabezal")
    st.markdown(tape_html(s), unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Estado actual", state)
    col2.metric("Transiciones ejecutadas", s["step"])
    col3.metric("Símbolo leído", s["tape"].get(s["head"], BLANK) if state not in HALT else "—")
    st.info(ROLE[state])

    if s["last"]:
        q, read, write, move, dest = s["last"]
        st.markdown(f"**Última transición:** `δ({q}, {read}) = ({dest}, {write}, {move})`")
    else:
        st.markdown("**Última transición:** inicio (ninguna regla ejecutada todavía).")

    if state == ACCEPT:
        st.success(f"✅ ACEPTADA: '{st.session_state.current_word or 'ε'}' pertenece al lenguaje.")
    elif state == REJECT:
        st.error(f"❌ RECHAZADA: '{st.session_state.current_word or 'ε'}' no pertenece al lenguaje.")

    a, b, c, d, e = st.columns(5)
    with a:
        if st.button("⬅ Anterior", use_container_width=True, disabled=s["step"] == 0):
            step_backward()
            st.rerun(scope="fragment")
    with b:
        if st.button("Siguiente ➡", use_container_width=True, disabled=state in HALT):
            st.session_state.running = False
            step_forward()
            st.rerun(scope="fragment")
    with c:
        if st.button("⏯ Pausar" if st.session_state.running else "▶ Reproducir", use_container_width=True, disabled=state in HALT):
            st.session_state.running = not st.session_state.running
            st.rerun()  # Reconfigurar run_every del fragmento.
    with d:
        if st.button("⏮ Reiniciar", use_container_width=True):
            reset()
            st.rerun()
    with e:
        if st.button("⏭ Final", use_container_width=True, disabled=state in HALT):
            run_to_end()
            st.rerun(scope="fragment")

    st.markdown("#### Historial de transiciones")
    rows = []
    for snap in st.session_state.history[1:st.session_state.cursor+1]:
        q, read, write, move, dest = snap["last"]
        rows.append({"Paso": snap["step"], "Estado": q, "Lee": read, "Escribe": write,
                     "Movimiento": move, "Nuevo estado": dest})
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=min(300, 37 * len(rows) + 40))
    else:
        st.caption("Todavía no se han ejecutado transiciones.")

st.select_slider("Velocidad de reproducción", options=[1.5, 1.0, 0.8, 0.5, 0.25], value=0.8,
                 format_func=lambda x: f"{x:g} segundos por transición", key="speed")
simulator()

with st.expander("📘 Tabla completa de transiciones"):
    labels = {"q0": "Buscar a", "q1": "Buscar b", "q2": "Buscar b tras Y", "q3": "Regresar", "q4": "Verificar"}
    selected = st.selectbox("Estado", list(labels), format_func=lambda q: f"{q} — {labels[q]}")
    table = []
    for symbol in ("a", "b", "X", "Y", BLANK):
        dest, write, move = RULES[(selected, symbol)]
        table.append({"Lee": symbol, "Escribe": write, "Mueve": move, "Nuevo estado": dest})
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

with st.expander("🎓 Actividad para clase"):
    st.markdown("""**Práctica:** use `aabb` y avance hasta encontrar una `Y` en `q₃`.
    Explique por qué la máquina necesita reconocer `X` e `Y` aunque la entrada original solo tenga `a` y `b`.
    Después pruebe `abab` y localice la transición que ocasiona el rechazo.""")
