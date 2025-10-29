"""Reusable helpers to render the IRL level evaluation flow in Streamlit.

This module centralises the UI logic requested for the IRL evaluation tabs:

* Toggle style with clear ON/OFF states.
* Navigation buttons with explicit enabled/disabled behaviour.
* Level headers that switch to a completed (green) variant.
* Optional helpers to render badges for level summaries.

Usage pattern (minimal example)::

    import streamlit as st
    from core import irl_level_flow as flow

    flow.inject_css()  # run once per app session

    QUESTIONS = [
        flow.Question(
            idx=1,
            text="¿Existe una hipótesis de mercado validada?",
            value_key="irl_demo_q1_value",
            note_key="irl_demo_q1_note",
        ),
        flow.Question(
            idx=2,
            text="¿Se recogieron antecedentes concretos?",
            value_key="irl_demo_q2_value",
            note_key="irl_demo_q2_note",
        ),
    ]

    cursor_key = "irl_demo_current_idx"
    current_idx = flow.init_state(QUESTIONS, cursor_key=cursor_key)
    done = flow.level_completed(QUESTIONS)

    st.markdown(f"<div class='{flow.CSS_SCOPE_CLASS}'>", unsafe_allow_html=True)
    flow.render_level_header("Nivel 1 • Hipótesis especulativa", done)
    current_question = QUESTIONS[current_idx]
    flow.render_question(current_question, position=current_idx, total=len(QUESTIONS))
    nav = flow.render_nav(
        len(QUESTIONS),
        current_idx,
        can_save=done,
        current_valid=flow.can_go_next(current_idx, QUESTIONS),
        prefix="irl_demo",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if nav.previous:
        flow.step(-1, len(QUESTIONS), cursor_key=cursor_key)
    if nav.next:
        flow.step(1, len(QUESTIONS), cursor_key=cursor_key)
    if nav.save:
        flow.save_level()

Integration checklist for the main IRL page:

1. Call :func:`inject_css` once to register the styles.
2. Declare the question metadata using :class:`Question` and keep
   ``value_key`` / ``note_key`` aligned with ``st.session_state``.
3. Render the header, the active question, and navigation via the helpers.
4. Persist the following keys in ``st.session_state``:

   * ``{STATE_PREFIX}…_current_idx`` → cursor for the active question.
   * Question ``value_key`` → boolean toggle state.
   * Question ``note_key`` → evidence text when the answer is ``True``.

The helpers are idempotent – reruns will not duplicate CSS nor corrupt the
stored state. Logic related to persistence (e.g. saving to the database) is
delegated to the caller via :func:`save_level`.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable, Sequence

import streamlit as st

CSS_SCOPE_CLASS = "irl-eval"
STATE_PREFIX = "irl_"
REQUIRE_NOTE_WHEN_TRUE = True


@dataclass(slots=True)
class Question:
    """Metadata required to render a boolean IRL question."""

    idx: int
    text: str
    value_key: str
    note_key: str
    answer_key: str | None = None
    note_placeholder: str = "Describe brevemente los antecedentes…"
    require_note_when_true: bool = REQUIRE_NOTE_WHEN_TRUE
    help_text: str | None = None


@dataclass(slots=True)
class NavResult:
    """Result of rendering the navigation controls."""

    previous: bool
    next: bool
    save: bool
    edit: bool


_CSS_TEMPLATE = """
.<scope> .progress-per-question,
.<scope> .question-counter {
  display: none !important;
}

.<scope>__level-header {
  background: rgba(31, 87, 52, 0.08);
  border: 1px solid rgba(31, 87, 52, 0.18);
  border-radius: 18px;
  padding: 1rem 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1.1rem;
  transition: border-color 0.25s ease, background 0.25s ease;
}

.<scope>__level-header.is-done {
  background: linear-gradient(140deg, rgba(46, 132, 75, 0.16), rgba(46, 132, 75, 0.28));
  border-color: rgba(46, 132, 75, 0.45);
  box-shadow: 0 16px 34px rgba(17, 58, 33, 0.18);
}

.<scope>__level-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-900);
}

.<scope>__level-subtitle {
  margin: 0;
  color: var(--text-500);
  font-size: 0.9rem;
  line-height: 1.35;
}

.<scope>__pill {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  background: rgba(26, 97, 48, 0.15);
  color: rgba(20, 66, 33, 0.85);
}

.<scope>__level-header.is-done .<scope>__pill {
  background: rgba(31, 110, 56, 0.92);
  color: #f4fff2;
}

.<scope>__question {
    border: 1px solid rgba(var(--shadow-color), 0.14);
    border-radius: 14px;
    padding: 0.7rem 0.9rem 0.85rem;
    background: #ffffff;
    box-shadow: 0 10px 20px rgba(var(--shadow-color), 0.10);
    margin-bottom: 0.3rem;
}

.<scope>__question-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.6rem;
    margin-bottom: 0.45rem;
}

.<scope>__question-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(140deg, rgba(31, 87, 52, 0.85), rgba(49, 120, 69, 0.85));
  color: #f6fff2;
  font-weight: 700;
  font-size: 1rem;
}

.<scope>__question-text {
  margin: 0;
  color: var(--text-900);
  font-size: 1rem;
  line-height: 1.45;
}

.<scope>__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.65rem 0.8rem;
  border-radius: 999px;
  background: rgba(var(--shadow-color), 0.06);
  border: 1px solid rgba(var(--shadow-color), 0.14);
  margin-bottom: 0.6rem;
}

.<scope>__toggle-state {
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--text-700);
}

.<scope>__toggle-state.is-true {
  color: rgba(36, 109, 57, 0.92);
}

.<scope>__toggle-state.is-false {
  color: rgba(136, 41, 28, 0.82);
}

.<scope>__note {
  margin-top: 0.6rem;
}

.<scope>__note-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-500);
  margin-bottom: 0.35rem;
}

.<scope>__note-hint {
  font-size: 0.8rem;
  color: rgba(165, 42, 42, 0.85);
  margin-top: 0.35rem;
}

.<scope>__nav {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.9rem;
  align-items: stretch;
}

.<scope>__nav button[disabled] {
  opacity: 1 !important;
  cursor: not-allowed !important;
  box-shadow: none !important;
  background: linear-gradient(135deg, #d9d9d9, #bfbfbf) !important;
  color: #1f1f1f !important;
  border: 1px solid #b0b0b0 !important;
}

.<scope>__nav button:not([disabled]) {
  box-shadow: 0 16px 28px rgba(var(--shadow-color), 0.22);
}

.<scope>__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.7rem;
  border-radius: 12px;
  font-size: 0.78rem;
  font-weight: 600;
  background: rgba(var(--shadow-color), 0.08);
  color: var(--text-500);
}

.<scope>__badge.is-done {
  background: rgba(43, 118, 63, 0.18);
  color: rgba(27, 82, 45, 0.9);
}

.<scope> div[data-testid="stToggle"] > label > span:first-child {
  display: none;
}

.<scope> div[data-testid="stToggle"] > label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.<scope> div[data-testid="stToggle"] [role="switch"] {
  width: 54px;
  height: 28px;
  border-radius: 999px;
  border: 1px solid rgba(var(--shadow-color), 0.25);
  background: rgba(var(--shadow-color), 0.15);
  transition: background 0.25s ease, border-color 0.25s ease;
  position: relative;
}

.<scope> div[data-testid="stToggle"] [role="switch"]::after {
  content: "";
  width: 22px;
  height: 22px;
  background: #ffffff;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 4px;
  transform: translateY(-50%);
  box-shadow: 0 6px 14px rgba(var(--shadow-color), 0.18);
  transition: transform 0.25s ease;
}

.<scope> div[data-testid="stToggle"] [role="switch"][aria-checked="true"] {
  background: linear-gradient(135deg, var(--forest-500), var(--forest-700));
  border-color: rgba(28, 91, 51, 0.55);
}

.<scope> div[data-testid="stToggle"] [role="switch"][aria-checked="true"]::after {
  transform: translate(26px, -50%);
}

.<scope>__nav-hint {
  grid-column: 1 / -1;
  font-size: 0.82rem;
  color: var(--text-500);
}

@media (max-width: 768px) {
  .<scope>__nav {
    grid-template-columns: 1fr;
  }
}
"""


def _css() -> str:
    """Return the scoped CSS replacing placeholders with the scope class."""

    return _CSS_TEMPLATE.replace("<scope>", CSS_SCOPE_CLASS)


def inject_css() -> None:
    """Inject the custom CSS once per session."""

    flag_key = f"{STATE_PREFIX}css_loaded"
    if st.session_state.get(flag_key):
        return
    st.session_state[flag_key] = True
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)


def init_state(questions: Sequence[Question], *, cursor_key: str) -> int:
    """Ensure ``st.session_state`` contains defaults for the provided questions."""

    for question in questions:
        # Aseguramos que la key booleana de la pregunta exista y sea booleana
        if question.value_key not in st.session_state:
            st.session_state[question.value_key] = False
        else:
            # normalizamos a booleano
            st.session_state[question.value_key] = bool(st.session_state[question.value_key])

        # Sincronizamos la representación textual si corresponde
        if question.answer_key:
            st.session_state[question.answer_key] = (
                "VERDADERO" if st.session_state.get(question.value_key) else "FALSO"
            )

        # Nota: siempre garantizamos que exista la key de evidencia como string
        if question.note_key not in st.session_state:
            st.session_state[question.note_key] = ""
        else:
            current_note = st.session_state[question.note_key]
            if not isinstance(current_note, str):
                st.session_state[question.note_key] = "" if current_note is None else str(current_note)

    total = len(questions)
    if cursor_key not in st.session_state:
        st.session_state[cursor_key] = 0
    if total:
        st.session_state[cursor_key] = max(0, min(st.session_state[cursor_key], total - 1))
    else:
        st.session_state[cursor_key] = 0
    return st.session_state[cursor_key]


def _note_value(question: Question) -> str:
    value = st.session_state.get(question.note_key, "")
    return str(value or "").strip()


def _answer_value(question: Question) -> str | None:
    """Return the textual answer for ``question`` when available."""

    selected = bool(st.session_state.get(question.value_key))
    derived_answer = "VERDADERO" if selected else "FALSO"

    if not question.answer_key:
        return derived_answer

    answer = st.session_state.get(question.answer_key)
    if answer not in {"VERDADERO", "FALSO"}:
        st.session_state[question.answer_key] = derived_answer
        return derived_answer

    if answer != derived_answer:
        st.session_state[question.answer_key] = derived_answer
        return derived_answer

    return str(answer)


def question_valid(question: Question) -> bool:
    """Return ``True`` if the current answer satisfies the validation rules."""

    textual_answer = _answer_value(question)
    if textual_answer == "FALSO":
        return True
    if textual_answer == "VERDADERO":
        if not question.require_note_when_true:
            return True
        return bool(_note_value(question))

    selected = bool(st.session_state.get(question.value_key))
    if not selected:
        return True
    if not question.require_note_when_true:
        return True
    return bool(_note_value(question))


def level_completed(questions: Sequence[Question]) -> bool:
    """Return ``True`` when all questions are valid."""

    return all(question_valid(question) for question in questions)


def render_level_header(level_name: str, done: bool, description: str | None = None) -> None:
    """Render the level header with the appropriate visual state."""

    status_class = "is-done" if done else ""
    badge_text = "CONTESTADO" if done else "PENDIENTE"
    st.markdown(
        """
        <div class="%s__level-header %s">
            <span class="%s__pill">%s</span>
            <h4 class="%s__level-title">%s</h4>
            %s
        </div>
        """
        % (
            CSS_SCOPE_CLASS,
            status_class,
            CSS_SCOPE_CLASS,
            badge_text,
            CSS_SCOPE_CLASS,
            escape(level_name),
            (
                f"<p class='{CSS_SCOPE_CLASS}__level-subtitle'>{escape(description)}</p>"
                if description
                else ""
            ),
        ),
        unsafe_allow_html=True,
    )


def render_question(
    question: Question,
    *,
    position: int,
    total: int,
    disabled: bool = False,
) -> bool:
    """Render the toggle and optional note field for the provided question."""

    st.markdown(
        """
        <div class="%s__question">
            <div class="%s__question-header">
                <span class="%s__question-badge">%s</span>
                <p class="%s__question-text">%s</p>
            </div>
        """
        % (
            CSS_SCOPE_CLASS,
            CSS_SCOPE_CLASS,
            CSS_SCOPE_CLASS,
            f"{position + 1}/{total}",
            CSS_SCOPE_CLASS,
            escape(question.text),
        ),
        unsafe_allow_html=True,
    )

    answer_key = question.answer_key
    value_key = question.value_key

    # Inicializar valor desde session_state (ya normalizado por init_state)
    initial_value = bool(st.session_state.get(value_key, False))

    # Usamos checkbox (más estándar) para una interacción rápida y predecible
    checkbox_value = st.checkbox(
        label=question.text,
        key=value_key,
        value=initial_value,
        disabled=disabled,
        label_visibility="collapsed",
    )

    # Sincronizar la representación textual (answer_key) cuando cambie
    if checkbox_value != (st.session_state.get(answer_key) == "VERDADERO" if answer_key else checkbox_value):
        # Actualizamos el estado booleano en session_state (checkbox ya lo hizo)
        st.session_state[value_key] = bool(checkbox_value)
        if answer_key:
            st.session_state[answer_key] = "VERDADERO" if checkbox_value else "FALSO"

    toggle_value = checkbox_value

    # Estado visual
    state_class = "is-true" if toggle_value else "is-false"
    display_text = "VERDADERO" if toggle_value else "FALSO"
    
    st.markdown(
        """<div class="%s__toggle"><span class="%s__toggle-state %s">%s</span></div>"""
        % (
            CSS_SCOPE_CLASS,
            CSS_SCOPE_CLASS,
            state_class,
            display_text
        ),
        unsafe_allow_html=True,
    )

    note_required = bool(st.session_state.get(question.value_key)) and question.require_note_when_true
    note_disabled = disabled or not st.session_state.get(question.value_key)

    note_value = st.session_state.get(question.note_key, "")
    if not isinstance(note_value, str):
        note_value = "" if note_value is None else str(note_value)
        st.session_state[question.note_key] = note_value

    st.text_area(
        "Antecedentes de verificación",
        key=question.note_key,
        value=note_value,
        placeholder=question.note_placeholder,
        disabled=note_disabled,
        height=110,
    )

    if question.help_text and not note_disabled:
        st.caption(question.help_text)

    valid = question_valid(question)
    if note_required and not valid:
        st.markdown(
            f"<div class='{CSS_SCOPE_CLASS}__note-hint'>Agrega los antecedentes para continuar.</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"</div>", unsafe_allow_html=True)
    return valid


def can_go_next(idx: int, questions: Sequence[Question]) -> bool:
    """Return ``True`` if the question at ``idx`` is valid."""

    if idx < 0 or idx >= len(questions):
        return False
    return question_valid(questions[idx])


def step(delta: int, total: int, *, cursor_key: str) -> None:
    """Move the cursor ``delta`` steps within the valid range."""

    if total <= 0:
        st.session_state[cursor_key] = 0
        return
    nuevo = st.session_state.get(cursor_key, 0) + delta
    st.session_state[cursor_key] = max(0, min(nuevo, total - 1))


def render_nav(
    total_questions: int,
    current_idx: int,
    *,
    can_save: bool,
    current_valid: bool,
    prefix: str,
    disabled: bool = False,
    edit_label: str = "Editar",
    edit_disabled: bool = False,
) -> NavResult:
    """Render navigation buttons and return the click results."""

    prev_disabled = disabled or current_idx <= 0
    next_disabled = disabled or current_idx >= total_questions - 1 or not current_valid
    save_disabled = disabled or not can_save

    st.markdown(
        f"<div class='{CSS_SCOPE_CLASS}__nav'>",
        unsafe_allow_html=True,
    )

    btn_prev = st.button(
        "Anterior",
        key=f"{prefix}_prev",
        disabled=prev_disabled,
        use_container_width=True,
        type="primary" if not prev_disabled else "secondary",
    )
    btn_next = st.button(
        "Siguiente",
        key=f"{prefix}_next",
        disabled=next_disabled,
        use_container_width=True,
        type="primary" if not next_disabled else "secondary",
    )
    btn_save = st.button(
        "Guardar",
        key=f"{prefix}_save",
        disabled=save_disabled,
        use_container_width=True,
        type="primary" if not save_disabled else "secondary",
    )
    edit_type = "secondary"
    if not edit_disabled and edit_label != "Editar":
        edit_type = "primary"
    btn_edit = st.button(
        edit_label,
        key=f"{prefix}_edit",
        disabled=edit_disabled,
        use_container_width=True,
        type=edit_type,
    )

    if disabled:
        hint = "Modo solo lectura."
    elif not current_valid:
        hint = "Completa la pregunta actual para avanzar."
    elif not can_save:
        hint = "Responde todas las preguntas para habilitar Guardar."
    else:
        hint = ""
    if hint:
        st.markdown(
            f"<div class='{CSS_SCOPE_CLASS}__nav-hint'>{escape(hint)}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    return NavResult(previous=btn_prev, next=btn_next, save=btn_save, edit=btn_edit)


def save_level(message: str = "Nivel guardado correctamente.") -> None:
    """Placeholder hook executed after persistence succeeds."""

    st.success(message)


def level_badge(name: str, is_done: bool) -> str:
    """Return an HTML badge representing the completion state of a level."""

    status_class = "is-done" if is_done else ""
    status_label = "Completado" if is_done else "Pendiente"
    return (
        f"<span class='{CSS_SCOPE_CLASS}__badge {status_class}'>{escape(name)} · {status_label}</span>"
    )


def serialize_answers(questions: Iterable[Question]) -> dict[str, str | None]:
    """Return the responses mapped by index in string format."""

    respuestas: dict[str, str | None] = {}
    for question in questions:
        answer = _answer_value(question)
        if answer in {"VERDADERO", "FALSO"}:
            respuestas[str(question.idx)] = answer
        else:
            respuestas[str(question.idx)] = (
                "VERDADERO" if st.session_state.get(question.value_key) else "FALSO"
            )
    return respuestas


def serialize_evidences(questions: Iterable[Question]) -> dict[str, str]:
    """Return the evidences mapped by question index."""

    evidencias: dict[str, str] = {}
    for question in questions:
        answer = _answer_value(question)
        if answer == "VERDADERO":
            evidencias[str(question.idx)] = _note_value(question)
        elif answer == "FALSO":
            evidencias[str(question.idx)] = ""
        else:
            evidencias[str(question.idx)] = (
                _note_value(question) if st.session_state.get(question.value_key) else ""
            )
    return evidencias
