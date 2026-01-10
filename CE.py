import streamlit as st
import pandas as pd
import random
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="University Schedule Optimizer", layout="wide")

def load_data(file):
    df = pd.read_csv(file)
    # FIX 1: Bersihkan ruang kosong pada nama kolum
    df.columns = df.columns.str.strip()
    # FIX 2: Bersihkan ruang kosong pada data dalam sel
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

# --- 2. GENETIC ALGORITHM FUNCTIONS ---
def calculate_fitness(schedule_df):
    """
    Mengira fitness berdasarkan 'Hard Constraint': 
    Seorang pelajar tidak boleh ada 2 kelas pada hari dan waktu yang sama.
    """
    # Pastikan kolum yang diperlukan wujud
    required_cols = ['StudentName', 'Day', 'TimeSlot']
    if not all(col in schedule_df.columns for col in required_cols):
        return 0
    
    # Kumpulan data mengikut Pelajar, Hari, dan Slot Masa
    conflicts = schedule_df.groupby(['StudentName', 'Day', 'TimeSlot']).size()
    clashes = (conflicts > 1).sum()
    
    return 1 / (1 + clashes)

def mutate(df, mutation_rate=0.1):
    """Menukar slot masa secara rawak untuk mempelbagaikan genetik."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    timeslots = ['08-10', '09-11', '10-12', '11-13', '14-16', '16-18']
    
    new_df = df.copy()
    # FIX 3: Gunakan reset_index untuk memastikan 'at[i]' sentiasa betul
    new_df = new_df.reset_index(drop=True)
    
    for i in range(len(new_df)):
        if random.random() < mutation_rate:
            new_df.at[i, 'Day'] = random.choice(days)
            new_df.at[i, 'TimeSlot'] = random.choice(timeslots)
    return new_df

# --- 3. STREAMLIT UI ---
st.title("📅 Study Schedule Optimizer (Evolutionary Algorithm)")

uploaded_file = st.file_uploader("Upload student_schedule.csv", type="csv")

if uploaded_file:
    df_origin = load_data(uploaded_file)
    
    # Semak jika kolum betul
    if 'StudentName' not in df_origin.columns:
        st.error("Ralat: Fail CSV mesti mempunyai kolum 'StudentName', 'Day', dan 'TimeSlot'. Sila muat naik fail asal (bukan fail numerical).")
    else:
        st.subheader("Data Asal (Input)")
        st.dataframe(df_origin, use_container_width=True)

        # Parameter GA
        with st.sidebar:
            st.header("GA Parameters")
            pop_size = st.slider("Population Size", 10, 100, 50)
            generations = st.slider("Generations", 10, 200, 50)
            mutation_rate = st.slider("Mutation Rate", 0.01, 0.5, 0.1)

        if st.button("🚀 Run Optimization"):
            # Initial Population
            population = [mutate(df_origin, mutation_rate=0.5) for _ in range(pop_size)]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            best_schedule = None
            best_fitness = 0

            # Evolutionary Loop
            for gen in range(generations):
                # Sort by fitness
                population = sorted(population, key=lambda x: calculate_fitness(x), reverse=True)
                current_best_fitness = calculate_fitness(population[0])
                
                if current_best_fitness > best_fitness:
                    best_fitness = current_best_fitness
                    best_schedule = population[0]

                # Selection & Crossover
                next_gen = population[:pop_size // 2]
                while len(next_gen) < pop_size:
                    parent = random.choice(next_gen)
                    child = mutate(parent, mutation_rate=mutation_rate)
                    next_gen.append(child)
                
                population = next_gen
                
                # Update UI
                progress = (gen + 1) / generations
                progress_bar.progress(progress)
                status_text.text(f"Generation {gen+1}/{generations} - Best Fitness: {best_fitness:.4f}")

            # --- 4. RESULTS ---
            st.success("Optimasi Selesai!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Final Fitness", f"{best_fitness:.4f}")
            with col2:
                # Elakkan pembahagian dengan sifar
                clash_count = (1/best_fitness) - 1 if best_fitness > 0 else "N/A"
                st.metric("Total Clashes", int(clash_count) if isinstance(clash_count, float) else clash_count)

            st.subheader("Jadual Yang Dioptimumkan")
            st.dataframe(best_schedule.sort_values(by=['StudentName', 'Day']), use_container_width=True)
            
            csv = best_schedule.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Optimized Schedule", data=csv, file_name="optimized_schedule.csv", mime="text/csv")
