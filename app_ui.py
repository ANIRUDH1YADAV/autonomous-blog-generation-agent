import streamlit as st
import time
import uuid
import sqlite3
import json
from app.graph.workflow import graph


# **************************************** Utility Functions *************************

def generate_blog_id():
    return str(uuid.uuid4())


# ── SQLite helpers (UI database) ──────────────────────────────────────────────
# "blog_sessions.db" stores topic labels + chat bubbles for the sidebar/UI.
# This is SEPARATE from LangGraph's "memory.db" (internal graph state).

DB_PATH = "blog_sessions.db"


def init_db():
    """Create tables on first run. Safe to call on every Streamlit rerun."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # One row per blog session (used for sidebar labels)
    c.execute("""
        CREATE TABLE IF NOT EXISTS blog_sessions (
            blog_id    TEXT PRIMARY KEY,
            topic      TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # One row per chat bubble (user topic + assistant blog)
    c.execute("""
        CREATE TABLE IF NOT EXISTS blog_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            blog_id    TEXT,
            role       TEXT,
            content    TEXT,
            images     TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_session(blog_id, topic):
    """Insert a new session or update its topic label."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO blog_sessions (blog_id, topic)
        VALUES (?, ?)
        ON CONFLICT(blog_id) DO UPDATE SET topic = excluded.topic
    """, (blog_id, topic))
    conn.commit()
    conn.close()


def save_message(blog_id, role, content, images=None):
    """Append one chat bubble to a session."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO blog_messages (blog_id, role, content, images)
        VALUES (?, ?, ?, ?)
    """, (blog_id, role, content, json.dumps(images or [])))
    conn.commit()
    conn.close()


def load_all_sessions():
    """Return all sessions ordered newest first (for sidebar)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT blog_id, topic FROM blog_sessions ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "topic": row[1]} for row in rows]


def load_messages(blog_id):
    """Return all messages for a given session."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT role, content, images
        FROM blog_messages
        WHERE blog_id = ?
        ORDER BY created_at ASC
    """, (blog_id,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "role":    row[0],
            "content": row[1],
            "images":  json.loads(row[2]) if row[2] else []
        }
        for row in rows
    ]


def reset_blog():
    """Start a brand-new blog session."""
    st.session_state['current_blog_id']  = generate_blog_id()
    st.session_state['current_messages'] = []


# **************************************** Initialise DB + Session ****************

init_db()   # CREATE TABLE IF NOT EXISTS — safe on every rerun

if 'current_blog_id' not in st.session_state:
    st.session_state['current_blog_id'] = generate_blog_id()

if 'current_messages' not in st.session_state:
    st.session_state['current_messages'] = []


# **************************************** Sidebar UI *****************************

st.sidebar.title("✍️ AI Blog Generator")
st.sidebar.markdown("---")

if st.sidebar.button("➕ New Blog", use_container_width=True):
    reset_blog()

st.sidebar.markdown("### 📚 Blog History")

# Always read fresh from SQLite — survives page refresh + server restart
for entry in load_all_sessions():
    label = entry['topic'] if entry['topic'] else f"Session {entry['id'][:8]}..."
    if st.sidebar.button(f"📝 {label}", key=entry['id'], use_container_width=True):
        st.session_state['current_blog_id']  = entry['id']
        st.session_state['current_messages'] = load_messages(entry['id'])


# **************************************** Main UI ********************************

st.title("🤖 AI Autonomous Blog Generator")
st.caption("Powered by AI Agents — Enter a topic and watch your blog come to life.")
st.markdown("---")

# Render all messages for the active session
for message in st.session_state['current_messages']:

    if message['role'] == 'user':
        with st.chat_message('user'):
            st.markdown(f"**Topic:** {message['content']}")

    elif message['role'] == 'assistant':
        with st.chat_message('assistant'):
            st.markdown(message['content'])
            if message.get('images'):
                st.subheader("📊 Generated Diagrams")
                for img in message['images']:
                    st.write(img['section'])
                    st.image(img['path'])


# **************************************** Chat Input *****************************

topic = st.chat_input("Enter a blog topic (e.g. 'The Future of AI in Healthcare')...")

if topic:

    blog_id = st.session_state['current_blog_id']

    # ── 1. Save session label + user message to SQLite ────────────────────────
    save_session(blog_id, topic[:40] + ("..." if len(topic) > 40 else ""))
    save_message(blog_id, role="user", content=topic)

    # ── 2. Update in-memory display state ─────────────────────────────────────
    st.session_state['current_messages'].append({'role': 'user', 'content': topic})

    with st.chat_message('user'):
        st.markdown(f"**Topic:** {topic}")

    # ── 3. Run AI agents ───────────────────────────────────────────────────────
    with st.chat_message('assistant'):

        state       = {"topic": topic}
        final_state = None

        # thread_id links this run to LangGraph's SqliteSaver (memory.db)
        CONFIG = {"configurable": {"thread_id": blog_id}}

        status_placeholder = st.empty()

        with st.spinner("AI Agents are working on your blog..."):
            for event in graph.stream(state, config=CONFIG, stream_mode="values"):
                final_state = event

                if "mode" in event:
                    status_placeholder.info("🔀 **Router Agent** — Analysing topic and routing...")

                if "plan" in event:
                    status_placeholder.info("🗂️ **Planner Agent** — Building blog structure and outline...")

                if "written_sections" in event:
                    status_placeholder.info("✍️ **Writer Agent** — Writing blog sections...")

                if "final_blog" in event:
                    status_placeholder.info("🔧 **Reducer Agent** — Compiling and finalising blog...")

        status_placeholder.empty()

        # ── 4. Stream + display the final blog ────────────────────────────────
        if final_state and "final_blog" in final_state:
            blog = final_state["final_blog"]

            st.success("✅ Blog generated successfully!")

            # ChatGPT-style character-by-character streaming
            placeholder = st.empty()
            output = ""
            for char in blog:
                output += char
                placeholder.markdown(output)
                time.sleep(0.002)

            # Show generated diagrams
            images = []
            if "images" in final_state:
                images = final_state["images"]
                st.subheader("📊 Generated Diagrams")
                for img in images:
                    st.write(img['section'])
                    st.image(img['path'])

            # ── 5. Persist assistant message to SQLite ─────────────────────────
            save_message(blog_id, role="assistant", content=blog, images=images)

            # ── 6. Update in-memory display state ──────────────────────────────
            st.session_state['current_messages'].append({
                'role':    'assistant',
                'content': blog,
                'images':  images
            })

        else:
            error_msg = "⚠️ Blog generation did not complete. Please try again."
            st.warning(error_msg)
            save_message(blog_id, role="assistant", content=error_msg)
            st.session_state['current_messages'].append({
                'role':    'assistant',
                'content': error_msg,
                'images':  []
            })