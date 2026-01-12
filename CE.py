import streamlit as st
import pandas as pd
import random
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION & MOCK DATA ---
st.set_page_config(page_title="University Schedule Optimizer", layout="wide")

def load_data(file):
    df = pd.read_csv(file)
    return df

# --- 2. GENETIC ALGORITHM FUNCTIONS ---

def calculate_fitness(schedule_df):
    """
    Mengira fitness berdasarkan beberapa kriteria:
    1. **Konflik** - Elakkan pelajar mempunyai dua kelas pada masa yang sama.
    2. **Penalti Slot Masa yang Tidak Seimbang** - Elakkan kelas yang terlalu awal atau lewat.
    3. **Penggunaan Waktu yang Seimbang** - Menggalakkan kelas yang diagihkan secara seimbang sepanjang hari.
    """
    clashes = 0
    imbalance_penalty = 0
    empty_slot_penalty = 0
    
    # Kumpulan data mengikut Pelajar, Hari, dan Slot Masa
    conflicts = schedule_df.groupby(['Student_ID', 'Day_Num', 'TimeSlot']).size()
    clashes = (conflicts > 1).sum()  # Bilangan konflik (pelajar dengan dua kelas pada masa yang sama)
    
    # Penalti untuk kelas yang terlalu awal atau lewat
    for index, row in schedule_df.iterrows():
        # Menilai slot masa untuk keseimbangan
        start_hour = int(row['Start_Time'].split(":")[0])  # Ambil jam sahaja
        if start_hour < 9 or start_hour > 16:  # Penalti untuk kelas awal atau lewat
            imbalance_penalty += 1

    # Penalti untuk slot kosong (jika pelajar mempunyai waktu kosong antara kelas)
    for student_id in schedule_df['Student_ID'].unique():
        student_schedule = schedule_df[schedule_df['Student_ID'] == student_id]
        student_schedule = student_schedule.sort_values(by='Start_Time')
        
        for i in range(1, len(student_schedule)):
            # Mengira jurang masa antara kelas
            prev_end_time = int(student_schedule.iloc[i-1]['End_Time'].split(":")[0])
            next_start_time = int(student_schedule.iloc[i]['Start_Time'].split(":")[0])
            
            # Penalti jika ada jurang besar (lebih dari 2 jam)
            if next_start_time - prev_end_time > 2:
                empty_slot_penalty += 1

    # Fitness adalah 1 / (1 + total penalti dan konflik)
    return 1 / (1 + clashes + imbalance_penalty + empty_slot_penalty)

def mutate(df, mutation_rate=0.1):
    """Menukar slot masa secara rawak untuk mempelbagaikan genetik."""
    
    # TimeSlot (converted from Start_Time and End_Time)
    timeslots = ['08-10', '09-11', '10-12', '11-13', '14-16', '16-18']
    
    # Day mapping based on Day_Num (1 = Monday, 5 = Friday)
    day_mapping = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday'}
    
    new_df = df.copy()
    for i in range(len(new_df)):
        if random.random() < mutation_rate:
            # Mutate day and time slot
            new_df.at[i, 'Day'] = random.choice(list(day_mapping.values()))
            new_df.at[i, 'TimeSlot'] = random.choice(timeslots)
    return new_df

def parse_time(time_value):
    """Convert time string or integer like '08:00' or 8 to an integer hour (e.g., '08' -> 8)."""
    try:
        if isinstance(time_value, int):  # In case the time is in integer format
            hour = f'{time_value:02d}'  # Convert to string with leading zero if needed
        else:
            hour = time_value.split(":")[0]  # Extract the hour part from time string
        return int(hour)
    except Exception as e:
        st.error(f"Error parsing time: {e} - Time value: {time_value}")
        return None

# --- 3. STREAMLIT UI ---
st.title("📅 Study Schedule Optimizer (Evolutionary Algorithm)")
st.write("Muat naik fail CSV anda untuk mengoptimumkan jadual tanpa clash.")

uploaded_file = st.file_uploader("Upload student_schedule.csv", type="csv")

if uploaded_file:
    df_origin = load_data(uploaded_file)
    st.subheader("Data Asal (Input)")
    st.dataframe(df_origin, use_container_width=True)

    # --- Time Parsing ---
    try:
        # Map Day_Num to Day
        df_origin['Day'] = df_origin['Day_Num'].map({1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday'})

        # Create TimeSlot based on Start_Time and End_Time
        df_origin['Start_Hour'] = df_origin['Start_Time'].apply(parse_time)
        df_origin['End_Hour'] = df_origin['End_Time'].apply(parse_time)
        
        # Create TimeSlot as a string: 'StartHour-EndHour'
        df_origin['TimeSlot'] = df_origin.apply(lambda row: f'{row["Start_Hour"]}-{row["End_Hour"]}', axis=1)

    except Exception as e:
        st.error(f"Error processing time columns: {e}")

    # Parameter GA
    with st.sidebar:
        st.header("GA Parameters")
        pop_size = st.slider("Population Size", 10, 100, 50)
        generations = st.slider("Generations", 10, 200, 50)
        mutation_rate = st.slider("Mutation Rate", 0.01, 0.5, 0.1)

    if st.button("🚀 Run Optimization"):
        # Initial Population (Copy of original with slight mutations)
        population = [mutate(df_origin, mutation_rate=0.5) for _ in range(pop_size)]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        best_schedule = None
        best_fitness = 0
        fitness_progress = []  # Track fitness over generations

        # Evolutionary Loop
        for gen in range(generations):
            # Evaluate fitness
            population = sorted(population, key=lambda x: calculate_fitness(x), reverse=True)
            current_best_fitness = calculate_fitness(population[0])
            
            if current_best_fitness > best_fitness:
                best_fitness = current_best_fitness
                best_schedule = population[0]

            # Selection & Crossover (Simple version: Keep top 50%)
            next_gen = population[:pop_size // 2]
            
            # Fill the rest with mutated versions of the best
            while len(next_gen) < pop_size:
                parent = random.choice(next_gen)
                child = mutate(parent, mutation_rate=mutation_rate)
                next_gen.append(child)
            
            population = next_gen
            
            # Update UI
            progress = (gen + 1) / generations
            progress_bar.progress(progress)
            status_text.text(f"Generation {gen+1}/{generations} - Best Fitness: {best_fitness:.4f}")
            
            # Track fitness progression
            fitness_progress.append(best_fitness)

        # --- 4. RESULTS ---
        st.success("Optimasi Selesai!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Final Fitness", f"{best_fitness:.4f}")
        with col2:
            clash_count = (1/best_fitness) - 1
            st.metric("Total Clashes", int(clash_count))

        st.subheader("Jadual Yang Dioptimumkan")
        st.dataframe(best_schedule.sort_values(by=['Student_ID', 'Day']), use_container_width=True)
        
        # --- Plot Fitness Progression Graph ---
        st.subheader("Fitness Progression over Generations")
        plt.plot(fitness_progress, label="Fitness")
        plt.xlabel('Generations')
        plt.ylabel('Fitness')
        plt.title('Fitness Progression (Best Fitness)')
        plt.legend()
        st.pyplot(plt)
        
        # Download Button
        csv = best_schedule.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Optimized Schedule", data=csv, file_name="optimized_schedule.csv", mime="text/csv")
