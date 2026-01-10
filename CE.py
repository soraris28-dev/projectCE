import streamlit as st
import pandas as pd
import random

# Algoritma Artificial Bee Colony (ABC)
class Bee:
    def __init__(self, schedule, fitness):
        self.schedule = schedule  # Jadual yang dicadangkan
        self.fitness = fitness    # Kecergasan jadual

def calculate_fitness(schedule):
    """
    Fungsi untuk mengira kecergasan jadual.
    Jadual dianggap lebih baik jika tugas-tugasnya sesuai dengan slot masa yang diberikan.
    """
    fitness = 0
    for task in schedule:
        if task['duration'] <= task['time_slot']:
            fitness += 1  # Menilai jika tempoh tugas sesuai dengan slot masa
    return fitness

def abc_algorithm(tasks, num_bees=10, max_iter=100):
    """
    Fungsi utama untuk implementasi algoritma ABC.
    Algoritma ini mengoptimumkan jadual pelajar dengan mengurangkan konflik tugas.
    """
    bees = []
    best_schedule = None
    best_fitness = -float('inf')

    # Inisialisasi populasi dengan jadual rawak
    for _ in range(num_bees):
        schedule = [{'task': task['course_id'], 'duration': task['duration'], 'time_slot': random.randint(1, 10)} for task in tasks]
        fitness = calculate_fitness(schedule)
        bees.append(Bee(schedule, fitness))

    # Gelung utama algoritma ABC
    for iteration in range(max_iter):
        for bee in bees:
            new_schedule = bee.schedule[:]
            random_task = random.choice(new_schedule)
            new_schedule.remove(random_task)
            new_schedule.append({'task': random_task['task'], 'duration': random.randint(1, 3), 'time_slot': random.randint(1, 10)})
            new_fitness = calculate_fitness(new_schedule)
            
            # Kemas kini jadual jika kecergasan bertambah
            if new_fitness > bee.fitness:
                bee.schedule = new_schedule
                bee.fitness = new_fitness
        
        # Semak jadual terbaik
        for bee in bees:
            if bee.fitness > best_fitness:
                best_fitness = bee.fitness
                best_schedule = bee.schedule
    
    return best_schedule

# Antaramuka pengguna Streamlit
st.title('Study Schedule Optimization for University Students')

# Muat naik fail CSV yang mengandungi data tugas
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    
    # Bersihkan nama-nama kolum dengan .strip() dan tukar huruf kecil untuk keserasian
    data.columns = data.columns.str.strip().str.lower()  # Buang ruang dan tukar huruf kecil
    
    # Paparkan nama kolum untuk penyemakan
    st.write("Column names in the CSV file:", data.columns)  # Display the column names to debug

    # Memproses data untuk menjadi senarai tugas
    try:
        tasks = [{'course_id': row['course_id'], 'duration': row['duration'], 'time_slot': row['start_time']} for _, row in data.iterrows()]
    except KeyError as e:
        st.error(f"KeyError: {e}. Please check the column names in your CSV file.")
    
    # Paparkan butang untuk menjalankan algoritma pengoptimuman
    if st.button('Optimize Schedule'):
        # Jalankan algoritma ABC untuk mendapatkan jadual terbaik
        optimized_schedule = abc_algorithm(tasks)
        
        # Paparkan jadual yang telah dioptimumkan
        st.write("Optimized Schedule:")
        for task in optimized_schedule:
            st.write(f"Course ID: {task['task']}, Duration: {task['duration']}, Time Slot: {task['time_slot']}")
