import streamlit as st
from app.graph.workflow import graph

st.title("AI Autonomous Blog Generator")

topic = st.text_input("Enter Blog Topic")

result = None

if st.button("Generate Blog"):

    if topic:

        state = {
            "topic": topic
        }

        with st.spinner("AI Agents are writing your blog..."):

            result = graph.invoke(state)

        blog = result["final_blog"]

        st.markdown(blog)

    else:
        st.warning("Please enter a topic.")

# safe check
if result and "images" in result:

    st.subheader("Generated Diagrams")

    for img in result["images"]:

        st.write(img["section"])

        st.image(img["path"])