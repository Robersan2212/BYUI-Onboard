import streamlit as st
from src.database import add_note, get_notes_by_user, get_all_notes

def notes():
    st.title("📝 Employee Notes")

    # Get current user (you might need to implement user authentication)
    current_user = st.session_state.get('user', 'Anonymous')

    # Create new note
    st.header("Create a New Note")
    note_content = st.text_area("Enter your note here")
    if st.button("Save Note"):
        if note_content:
            add_note(current_user, note_content)
            st.success("Note saved successfully!")
        else:
            st.error("Please enter some content for your note.")

    # View user's notes
    st.header("Your Notes")
    user_notes = get_notes_by_user(current_user)
    for note in user_notes:
        st.text(f"Date: {note['date']}")
        st.text(note['content'])
        st.markdown("---")

    # View all notes
    st.header("All Notes")
    show_all = st.checkbox("Show notes from all users")
    if show_all:
        all_notes = get_all_notes()
        for note in all_notes:
            st.text(f"User: {note['user']}")
            st.text(f"Date: {note['date']}")
            st.text(note['content'])
            st.markdown("---")

if __name__ == "__main__":
    notes()