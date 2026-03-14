import streamlit as st
import time
from app.graph.workflow import graph

st.title("AI Autonomous Blog Generator")

topic = st.text_input("Enter Blog Topic")

if st.button("Generate Blog"):

    if topic:

        state = {"topic": topic}

        status = st.empty()
        final_state = None

        with st.spinner("AI Agents are working..."):

            for event in graph.stream(state, stream_mode="values"):

                final_state = event

                # show which agent is running
                if "mode" in event:
                    status.write("Running agent: router")

                if "plan" in event:
                    status.write("Running agent: planner")

                if "written_sections" in event:
                    status.write("Running agent: writer")

                if "final_blog" in event:
                    status.write("Running agent: reducer")

        # show final blog
        if final_state and "final_blog" in final_state:

            blog = final_state["final_blog"]

            st.subheader("Generated Blog")

            placeholder = st.empty()
            output = ""

            # ChatGPT style streaming
            for char in blog:
                output += char
                placeholder.markdown(output)
                time.sleep(0.002)

        # show generated images
        if final_state and "images" in final_state:

            st.subheader("Generated Diagrams")

            for img in final_state["images"]:
                st.write(img["section"])
                st.image(img["path"])

    else:
        st.warning("Please enter a topic.")