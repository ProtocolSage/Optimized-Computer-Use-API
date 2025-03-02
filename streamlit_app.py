import streamlit as st

st.title("Claude Computer Use API")
st.write("This is a test app to verify Streamlit is working correctly.")

st.write("If you can see this, the Streamlit server is running properly in the container.")

st.success("All services have started successfully!")

# Add a button to test interactivity
if st.button("Click me!"):
    st.write("Button clicked!")
    
# Display some container status info
st.subheader("Container Information")
st.code("""
Container: claude-computer-api
Ports:
  - VNC: 5900
  - NoVNC web access: 6080
  - Streamlit interface: 8501
  - Combined interface: 8080
""")