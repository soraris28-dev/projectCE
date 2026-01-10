import streamlit as st
import pandas as pd
from abc_algorithm import abc_algorithm

# Fungsi untuk memuat naik data tugas dari fail CSV
def load_task_data(file):
    data = pd.read_csv(file)
    tasks = [{'name': row['Task'], 'duration': row['Duration'], 'time_slot': row['Time Slot']} for _, row in data.iterrows()]
    return tasks

# Antaramuka pengguna Streamlit
st.title('Study Schedule Optimization for University Students')

# Muat naik fail CSV yang mengandungi data tugas
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
if uploaded_file is not None:
    tasks = load_task_data(uploaded_file)
    
    # Paparkan butang untuk menjalankan algoritma pengoptimuman
    if st.button('Optimize Schedule'):
        # Jalankan algoritma ABC untuk mendapatkan jadual terbaik
        optimized_schedule = abc_algorithm(tasks)
        
        # Paparkan jadual yang telah dioptimumkan
        st.write("Optimized Schedule:")
        for task in optimized_schedule:
            st.write(f"Task: {task['task']}, Duration: {task['duration']}, Time Slot: {task['time_slot']}")
