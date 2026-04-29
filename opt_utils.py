import numpy as np 
import pandas as pd 
import time

def time_function(func, *args, **kwargs):
    # Wraps any function to return its output and the execution time
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, end - start

# Loads synthetic data and prepares mapping for sector constraints
def load_and_preprocess():
    # read in synthetic bond dataset
    universe = pd.read_csv('data/synthetic_bond_universe.csv')
    # read in covariance matrix
    cov_matrix = pd.read_csv('data/synthetic_covariance_matrix.csv', index_col=0)
    
    # Create sector mapping and return dictionaries
    sectors = universe.groupby('bond_type')['bond_id'].apply(list).to_dict()
    # Note: Assumes 'expected_return' exists or is derived in synthetic_bond_universe
    returns = universe.set_index('bond_id')['expected_annual_return_pct'].to_dict()
    
    return universe, cov_matrix, sectors, returns


