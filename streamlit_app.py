# streamlit_app.py
import streamlit as st
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpInteger, PULP_CBC_CMD
import math

def generate_patterns(lengths, stock_length, demands):
    patterns = []
    def recurse(i, counts, rem):
        if i == len(lengths):
            if any(counts):
                patterns.append(tuple(counts))
            return
        max_count = min(rem // lengths[i], demands[i])
        for c in range(max_count + 1):
            recurse(i+1, counts + [c], rem - c*lengths[i])
    recurse(0, [], stock_length)
    return patterns

def solve_min_waste(stock_length, piece_lengths, demands):
    patterns = generate_patterns(piece_lengths, stock_length, demands)
    total_required = sum(l*d for l,d in zip(piece_lengths, demands))
    min_bars = math.ceil(total_required / stock_length)
    scrap = [stock_length - sum(p[j]*piece_lengths[j] for j in range(len(piece_lengths)))
             for p in patterns]
    prob = LpProblem("MinScrap", LpMinimize)
    x = {i: LpVariable(f"x_{i}", lowBound=0, cat=LpInteger)
         for i in range(len(patterns))}
    prob += lpSum(scrap[i] * x[i] for i in x)
    for j in range(len(piece_lengths)):
        prob += lpSum(patterns[i][j] * x[i] for i in x) == demands[j]
    prob += lpSum(x[i] for i in x) == min_bars
    prob.solve(PULP_CBC_CMD(msg=False))
    return [(patterns[i], int(x[i].value())) for i in x if x[i].value() > 0]

st.title("Cutting-Stock Calculator")

stock_length = st.number_input("Stock length (mm)", min_value=1, value=2000)
lengths_str  = st.text_input("Piece lengths (comma-sep)", "722,210,140")
demands_str  = st.text_input("Demands (comma-sep)",      "4,4,4")

if st.button("Compute optimal plan"):
    try:
        piece_lengths = [int(x.strip()) for x in lengths_str.split(",")]
        demands       = [int(x.strip()) for x in demands_str.split(",")]
        if len(piece_lengths) != len(demands):
            st.error("❌ Number of lengths must match number of demands.")
        else:
            sol = solve_min_waste(stock_length, piece_lengths, demands)
            st.markdown("### Optimal waste-minimizing plan:")
            for pattern, count in sol:
                used = sum(pattern[j]*piece_lengths[j] for j in range(len(piece_lengths)))
                scrap_amt = stock_length - used
                desc = ", ".join(f"{pattern[j]}×{piece_lengths[j]}mm"
                                 for j in range(len(piece_lengths)) if pattern[j])
                st.write(f"- **{count} bar(s)** → {desc}  (used {used} mm, scrap {scrap_amt} mm)")
    except ValueError:
        st.error("❌ Please enter only integers, separated by commas.")
