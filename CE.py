import streamlit as st
import pandas as pd
import random
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="University Schedule Optimizer (ABC)", layout="wide")

def load_data(file):
    return pd.read_csv(file)

def calculate_fitness(schedule_df):
    conflicts = schedule_df.groupby(['Student_ID', 'Day_Num', 'TimeSlot']).size()
    clashes = (conflicts > 1).sum()
    return 1 / (1 + clashes)

def get_neighbor(df, mutation_rate=0.2):
    timeslots = ['08-10', '09-11', '10-12', '11-13', '14-16', '16-18']
    day_mapping = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday'}
    
    new_df = df.copy()
    for i in range(len(new_df)):
        if random.random() < mutation_rate:
            new_df.at[i, 'Day_Num'] = random.choice(list(day_mapping.keys()))
            new_df.at[i, 'TimeSlot'] = random.choice(timeslots)
    return new_df

st.title("🐝 Study Schedule Optimizer (Artificial Bee Colony)")
st.write("Using the Bee Colony Algorithm to find a clash-free schedule.")

uploaded_file = st.file_uploader("Upload student_schedule_cleaned.csv", type="csv")

if uploaded_file:
    df_origin = load_data(uploaded_file)
    
    if 'TimeSlot' not in df_origin.columns:
        df_origin['TimeSlot'] = df_origin.apply(lambda row: f"{int(row['Start_Time'])}-{int(row['End_Time'])}", axis=1)

    with st.sidebar:
        st.header("ABC Parameters")
        n_food_sources = st.slider("Number of Food Sources (Population)", 10, 100, 30)
        max_iter = st.slider("Max Iterations", 10, 200, 50)
        limit = st.slider("Abandonment Limit (Scout Bee Threshold)", 5, 50, 10)

    if st.button("🚀 Start Optimization"):
        food_sources = [get_neighbor(df_origin, mutation_rate=0.5) for _ in range(n_food_sources)]
        fitness_values = [calculate_fitness(fs) for fs in food_sources]
        trial_counters = [0] * n_food_sources
        
        best_fitness = max(fitness_values)
        best_schedule = food_sources[fitness_values.index(best_fitness)]
        history = []

        progress_bar = st.progress(0)

        for iteration in range(max_iter):
            for i in range(n_food_sources):
                new_source = get_neighbor(food_sources[i])
                new_fit = calculate_fitness(new_source)
                
                if new_fit > fitness_values[i]:
                    food_sources[i] = new_source
                    fitness_values[i] = new_fit
                    trial_counters[i] = 0
                else:
                    trial_counters[i] += 1

            total_fitness = sum(fitness_values)
            if total_fitness != 0:
                prob = [f/total_fitness for f in fitness_values]
                for i in range(n_food_sources):
                    if random.random() < prob[i]:
                        new_source = get_neighbor(food_sources[i])
                        new_fit = calculate_fitness(new_source)
                        if new_fit > fitness_values[i]:
                            food_sources[i] = new_source
                            fitness_values[i] = new_fit
                            trial_counters[i] = 0
                        else:
                            trial_counters[i] += 1

            for i in range(n_food_sources):
                if trial_counters[i] > limit:
                    food_sources[i] = get_neighbor(df_origin, mutation_rate=0.8)
                    fitness_values[i] = calculate_fitness(food_sources[i])
                    trial_counters[i] = 0

            current_max = max(fitness_values)
            if current_max > best_fitness:
                best_fitness = current_max
                best_schedule = food_sources[fitness_values.index(best_fitness)]
            
            history.append(best_fitness)
            progress_bar.progress((iteration + 1) / max_iter)

        st.success("Optimization complete!")
        
        c1, c2 = st.columns(2)
        c1.metric("Final Fitness", f"{best_fitness:.4f}")
        c2.metric("Total Clashes", int((1/best_fitness)-1) if best_fitness > 0 else "N/A")

        st.subheader("Optimized Schedule")
        st.dataframe(best_schedule.sort_values(by=['Student_ID', 'Day_Num']), use_container_width=True)

        fig, ax = plt.subplots()
        ax.plot(history, color='orange', linewidth=2)
        ax.set_title("ABC Optimization Progress")
        ax.set_xlabel("Iterations")
        ax.set_ylabel("Best Fitness")
        st.pyplot(fig)
