import streamlit as st
import time
from app.graph.workflow import graph

st.title("AI Autonomous Blog Generator")

topic = st.text_input("Enter Blog Topic")

final_state = None

if st.button("Generate Blog"):

    if topic:

        state = {"topic": topic}

        status = st.empty()

        with st.spinner("AI Agents are working..."):

            for event in graph.stream(state):

                node = list(event.keys())[0]

                status.write(f"Running agent: {node}")

                final_state = event[node]

        if final_state and "final_blog" in final_state:

            blog = final_state["final_blog"]

        st.subheader("Generated Blog")

        placeholder = st.empty()

        output = ""
        for char in blog:

          output += char

          placeholder.markdown(output)

          time.sleep(0.002)

        else:

          st.warning("Please enter a topic.")