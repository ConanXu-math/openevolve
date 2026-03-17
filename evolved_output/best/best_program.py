# EVOLVE-BLOCK-START
"""Function minimization example for OpenEvolve"""
import numpy as np
import random


def search_algorithm(iterations=1000, bounds=(-5, 5)):
    """
    An improved hybrid optimization algorithm combining simulated annealing
    with gradient-informed search to escape local minima.
    
    Args:
        iterations: Number of iterations to run
        bounds: Bounds for the search space (min, max)
    
    Returns:
        Tuple of (best_x, best_y, best_value)
    """
    # Initialize with multiple random points
    num_initial = 10
    best_x = np.random.uniform(bounds[0], bounds[1])
    best_y = np.random.uniform(bounds[0], bounds[1])
    best_value = evaluate_function(best_x, best_y)
    
    # Try multiple starting points
    for _ in range(num_initial):
        x = np.random.uniform(bounds[0], bounds[1])
        y = np.random.uniform(bounds[0], bounds[1])
        value = evaluate_function(x, y)
        if value < best_value:
            best_value = value
            best_x, best_y = x, y
    
    # Simulated annealing parameters
    temperature = 1.0
    cooling_rate = 0.995
    step_size = (bounds[1] - bounds[0]) / 10
    
    # Current position for annealing
    current_x, current_y = best_x, best_y
    current_value = best_value
    
    for i in range(iterations):
        # Adaptive step size - smaller as we progress
        adaptive_step = step_size * (1.0 - i/iterations)
        
        # Occasionally make large jumps to escape local minima
        if i % 50 == 0:
            # Random restart
            x = np.random.uniform(bounds[0], bounds[1])
            y = np.random.uniform(bounds[0], bounds[1])
        else:
            # Gradient-informed perturbation
            eps = 1e-6
            grad_x = (evaluate_function(current_x + eps, current_y) - current_value) / eps
            grad_y = (evaluate_function(current_x, current_y + eps) - current_value) / eps
            
            # Move against gradient with some randomness
            x = current_x - adaptive_step * grad_x + np.random.normal(0, adaptive_step/2)
            y = current_y - adaptive_step * grad_y + np.random.normal(0, adaptive_step/2)
        
        # Ensure bounds
        x = np.clip(x, bounds[0], bounds[1])
        y = np.clip(y, bounds[0], bounds[1])
        
        value = evaluate_function(x, y)
        
        # Simulated annealing acceptance criterion
        if value < current_value:
            # Always accept improvements
            current_x, current_y = x, y
            current_value = value
        else:
            # Sometimes accept worse solutions based on temperature
            delta = value - current_value
            acceptance_prob = np.exp(-delta / temperature)
            if random.random() < acceptance_prob:
                current_x, current_y = x, y
                current_value = value
        
        # Update global best
        if current_value < best_value:
            best_value = current_value
            best_x, best_y = current_x, current_y
        
        # Cool down temperature
        temperature *= cooling_rate
        
        # Occasionally do a local search around current best
        if i % 100 == 0 and i > 0:
            for _ in range(20):
                local_x = best_x + np.random.normal(0, adaptive_step/4)
                local_y = best_y + np.random.normal(0, adaptive_step/4)
                local_x = np.clip(local_x, bounds[0], bounds[1])
                local_y = np.clip(local_y, bounds[0], bounds[1])
                local_value = evaluate_function(local_x, local_y)
                if local_value < best_value:
                    best_value = local_value
                    best_x, best_y = local_x, local_y
                    current_x, current_y = local_x, local_y
                    current_value = local_value
    
    return best_x, best_y, best_value


# EVOLVE-BLOCK-END


# This part remains fixed (not evolved)
def evaluate_function(x, y):
    """The complex function we're trying to minimize"""
    return np.sin(x) * np.cos(y) + np.sin(x * y) + (x**2 + y**2) / 20


def run_search():
    x, y, value = search_algorithm()
    return x, y, value


if __name__ == "__main__":
    x, y, value = run_search()
    print(f"Found minimum at ({x}, {y}) with value {value}")