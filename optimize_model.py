import pickle
import numpy as np

# Load the large similarity matrix
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Check current data type
print(f"Original data type: {similarity.dtype}")
print(f"Original shape: {similarity.shape}")

# Convert to float32 (half the size of float64)
similarity_small = similarity.astype(np.float32)

# Save the optimization
pickle.dump(similarity_small, open('similarity.pkl', 'wb'))

print(f"New data type: {similarity_small.dtype}")
print("File optimized and saved.")
