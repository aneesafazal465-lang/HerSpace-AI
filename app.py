import streamlit as st
import joblib
import pandas as pd
import numpy as np

# Title
st.title("My Data Science Model Predictor")

# Load model
model = joblib.load(r"D:\my code\model.pkl")






# User Input Interface (Add fields matching your model's input features)
feature1 = st.number_input("Enter Feature 1 Value", value=0.0)
feature2 = st.selectbox("Select Feature 2 Option", options=['Option A', 'Option B'])

# Predict Button
if st.button("Predict"):
    # Format inputs into a DataFrame or 2D array matching training format
    input_data = pd.DataFrame([[feature1, feature2]], columns=['feature1', 'feature2'])
    
    # Preprocess input_data here if needed (e.g., using saved scaler/encoder)
    prediction = model.predict(input_data)
    
    st.success(f"Prediction Output: {prediction[0]}")