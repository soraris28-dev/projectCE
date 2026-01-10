import streamlit as st
import pandas as pd
import random
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="University Schedule Optimizer", layout="wide")

def load_data(file):
    # Membaca fail dengan encoding utf-8-sig untuk mengendalikan BOM (karakter tersembunyi)
    df = pd.read_csv(file, encoding='utf-8-sig')
    
    # MEMBERSIHKAN KOLUM: Buang ruang kosong dan karakter aneh
    df.columns = df.columns.str.strip().str.replace('﻿', '')
    
    # MEMBERSIHKAN DATA: Buang ruang kosong dalam setiap sel string
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    return df

# --- 2. GENETIC ALGORITHM FUNCTIONS ---

def calculate_fitness(schedule_df):
    """
    Fitness Function:
    Mengesan 'Hard Constraint' (Pertembungan/Clash).
    Jika pelajar ada >1 kelas pada Hari & Slot Masa yang sama, fitness berkurang.
    """
    # Pastikan kolum wujud sebelum proses
    required = ['StudentName', 'Day', 'TimeSlot']
    if not all(col in schedule_df.columns for col in required):
        return 0
    
    # Kumpulan data untuk cari clash
    conflicts = schedule_df.groupby(['StudentName', 'Day', 'TimeSlot']).size()
    clashes = (conflicts > 1).sum()
    
    # Formula Fitness: Semakin kurang clash, semakin tinggi nilai (max 1.0)
    return 1 / (1 + clashes)

def mutate(df, mutation_rate=0.1):
    """
    Mutation:
    Menukar Hari dan Slot Masa secara rawak untuk mencari kombinasi terbaik.
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    timeslots = ['08-10', '09-11', '10-12', '11-13', '14-16', '16-18']
    
    new_df = df.copy()
    new_df = new_df.reset_index(drop=True) # Elakkan ralat index
    
    for i in range(len(new_df)):
        if random.random() < mutation_rate:
            new_df.at[i, 'Day'] = random.choice(days)
            new_df.at[i, 'TimeSlot'] = random.choice(timeslots)
    return new_df

# --- 3. STREAMLIT UI ---
st.title("📅 University Study Schedule Optimizer")
st.markdown("""
Aplikasi ini menggunakan **Evolutionary Algorithm** untuk menyusun semula jadual pelajar 
supaya tiada pertembungan waktu kelas (clashes).
""")

uploaded_file = st.file_uploader("Muat naik fail student_schedule.csv", type="csv")

if uploaded_file:
    # Load dan bersihkan data
    df_origin = load_data(uploaded_file)
    
    # Semak jika kolum yang diperlukan ada
    expected_cols = ['StudentName', 'Course', 'Day', 'TimeSlot']
    found_cols = df_origin.columns.tolist()
    
    if not set(['StudentName', 'Day', 'TimeSlot']).issubset(set(found_cols)):
        st.error(f"Ralat: Kolum tidak sepadan! Kolum dikesan: {found_cols}")
        st.info("Pastikan CSV anda mempunyai kolum: StudentName, Course, Day, TimeSlot, Duration")
    else:
        st.subheader("📋 Data Asal (Input)")
        st.dataframe(df_origin, use_container_width=True)

        # Sidebar untuk Parameter
        with st.sidebar:
            st.header("⚙️ Parameter EA")
            pop_size = st.slider("Saiz Populasi", 10, 100, 50)
            generations = st.slider("Bilangan Generasi", 10, 200, 100)
            mutation_rate = st.slider("Kadar Mutasi", 0.01, 0.5, 0.1)
            st.info("Tip: Populasi & Generasi tinggi memberikan hasil lebih baik tetapi lebih lambat.")

        if st.button("🚀 Jalankan Optimasi"):
            # 1. Initialize Population (Populasi Awal)
            population = [mutate(df_origin, mutation_rate=0.6) for _ in range(pop_size)]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            best_schedule = None
            best_fitness = 0

            # 2. Evolutionary Loop
            for gen in range(generations):
                # Kira fitness dan susun mengikut yang terbaik
                population = sorted(population, key=lambda x: calculate_fitness(x), reverse=True)
                
                current_best_fitness = calculate_fitness(population[0])
                
                if current_best_fitness > best_fitness:
                    best_fitness = current_best_fitness
                    best_schedule = population[0].copy()

                # Hentikan jika sudah capai fitness sempurna (1.0)
                if best_fitness == 1.0:
                    break

                # Selection: Ambil 50% terbaik (Elitism)
                next_gen = population[:pop_size // 2]
                
                # Crossover & Mutation: Cipta anak baru dari yang terbaik
                while len(next_gen) < pop_size:
                    parent = random.choice(next_gen)
                    child = mutate(parent, mutation_rate=mutation_rate)
                    next_gen.append(child)
                
                population = next_gen
                
                # Update UI Progress
                perc = (gen + 1) / generations
                progress_bar.progress(perc)
                status_text.text(f"Generasi {gen+1}/{generations} | Fitness Terbaik: {best_fitness:.4f}")

            # --- 4. PAPAR HASIL ---
            st.divider()
            st.success("✅ Proses Optimasi Selesai!")
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Fitness Akhir", f"{best_fitness:.4f}")
            with m2:
                # Kira jumlah clash: (1/fitness) - 1
                total_clashes = int((1/best_fitness) - 1) if best_fitness > 0 else "N/A"
                st.metric("Jumlah Clash", total_clashes)

            if total_clashes == 0:
                st.balloons()

            st.subheader("📅 Jadual Hasil Optimasi")
            # Susun mengikut nama dan hari untuk mudah dibaca
            sorted_best = best_schedule.sort_values(by=['StudentName', 'Day'])
            st.dataframe(sorted_best, use_container_width=True)
            
            # Butang Download
            csv_output = sorted_best.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Muat Turun Jadual (CSV)",
                data=csv_output,
                file_name="jadual_dioptimumkan.csv",
                mime="text/csv"
            )

# --- ARAHAN JALANKAN ---
# Simpan kod ini sebagai 'app.py'
# Jalankan di terminal: streamlit run app.py
