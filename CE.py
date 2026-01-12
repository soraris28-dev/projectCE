import streamlit as st
import pandas as pd
import random
import numpy as np
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="ABC Optimizer Lab", layout="wide")

def calculate_fitness(schedule_df):
    # Mengira pertindihan (clashes)
    conflicts = schedule_df.groupby(['Student_ID', 'Day_Num', 'TimeSlot']).size()
    clashes = (conflicts > 1).sum()
    return 1 / (1 + clashes)

def get_neighbor(df, rate):
    timeslots = ['08-10', '09-11', '10-12', '11-13', '14-16', '16-18']
    new_df = df.copy()
    for i in range(len(new_df)):
        if random.random() < rate:
            new_df.at[i, 'Day_Num'] = random.randint(1, 5)
            new_df.at[i, 'TimeSlot'] = random.choice(timeslots)
    return new_df

def run_abc(df, pop_size, m_rate, iterations, limit):
    # Inisialisasi
    food_sources = [get_neighbor(df, 0.5) for _ in range(pop_size)]
    fitness_values = [calculate_fitness(fs) for fs in food_sources]
    trial_counters = [0] * pop_size
    history = []
    
    for _ in range(iterations):
        # Employed Bees
        for i in range(pop_size):
            candidate = get_neighbor(food_sources[i], m_rate)
            fit = calculate_fitness(candidate)
            if fit > fitness_values[i]:
                food_sources[i], fitness_values[i], trial_counters[i] = candidate, fit, 0
            else:
                trial_counters[i] += 1
        
        # Scout Bees
        for i in range(pop_size):
            if trial_counters[i] > limit:
                food_sources[i] = get_neighbor(df, 0.8)
                fitness_values[i] = calculate_fitness(food_sources[i])
                trial_counters[i] = 0
        
        history.append(max(fitness_values))
    return history, max(fitness_values)

# --- UI STREAMLIT ---
st.title("🐝 ABC Convergence Lab")
st.markdown("Bandingkan prestasi algoritma berdasarkan **Population Size** & **Mutation Rate**.")

uploaded_file = st.file_uploader("Upload Cleaned CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if 'TimeSlot' not in df.columns:
        df['TimeSlot'] = "08-10" # Default fallback

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Konfigurasi A")
        pop_a = st.slider("Pop Size (A)", 5, 50, 20)
        rate_a = st.slider("Mutation Rate (A)", 0.01, 0.5, 0.1)

    with col2:
        st.subheader("Konfigurasi B")
        pop_b = st.slider("Pop Size (B)", 5, 50, 40)
        rate_b = st.slider("Mutation Rate (B)", 0.01, 0.5, 0.3)

    if st.button("🚀 Bandingkan Prestasi"):
        with st.spinner("Sedang memproses perbandingan..."):
            history_a, best_a = run_abc(df, pop_a, rate_a, 50, 10)
            history_b, best_b = run_abc(df, pop_b, rate_b, 50, 10)

            # Graf Perbandingan Convergence
            st.subheader("📈 Graf Convergence (Penyatuan)")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(history_a, label=f"Set A (Pop:{pop_a}, Rate:{rate_a})", color='blue')
            ax.plot(history_b, label=f"Set B (Pop:{pop_b}, Rate:{rate_b})", color='orange')
            ax.set_xlabel("Generations")
            ax.set_ylabel("Fitness Score")
            ax.legend()
            st.pyplot(fig)

            # Rumusan Task
            st.success(f"Analisis Selesai! Set {'B' if best_b > best_a else 'A'} menunjukkan prestasi lebih baik.")
