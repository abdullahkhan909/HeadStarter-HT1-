from flask import Flask, request, jsonify, render_template
import pandas as pd
from flask_cors import CORS
from fuzzywuzzy import fuzz

app = Flask(__name__)
CORS(app)

# Load and preprocess datasets
def load_and_clean_data():
    recipes = pd.read_csv('data/RAW_recipes.csv')

    # Drop unnecessary columns
    recipes = recipes.drop(columns=['contributor_id', 'submitted', 'tags', 'nutrition', 'n_steps', 'description', 'n_ingredients'])

    # Drop duplicate rows
    recipes = recipes.drop_duplicates(subset=['id', 'name'])

    # Convert to smaller data types
    recipes['id'] = recipes['id'].astype('int32')

    return recipes

recipes = load_and_clean_data()

# Reduce dataset size for memory efficiency
def reduce_dataset_size(recipes, recipe_sample_size=1000):
    # Sample a subset of recipes
    reduced_recipes = recipes.sample(recipe_sample_size, random_state=42)
    return reduced_recipes

# Reduce dataset size
recipes = reduce_dataset_size(recipes)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    user_ingredients = request.form.get('ingredients').split(',')
    user_ingredients = [ingredient.strip().lower() for ingredient in user_ingredients]

    def contains_minimum_ingredients(recipe_ingredients, user_ingredients, threshold=3):
        recipe_ingredients = [ingredient.strip().lower() for ingredient in recipe_ingredients.split(',')]
        match_count = 0
        for user_ingredient in user_ingredients:
            if any(fuzz.partial_ratio(user_ingredient, recipe_ingredient) >= 80 for recipe_ingredient in recipe_ingredients):
                match_count += 1
        return match_count >= threshold

    filtered_recipes = recipes[recipes['ingredients'].apply(lambda x: contains_minimum_ingredients(x, user_ingredients))]
    recommended_recipes = filtered_recipes[['id', 'name']].sample(5).to_dict(orient='records') if not filtered_recipes.empty else [{"id": None, "name": "No recipes found with the given ingredients."}]

    return jsonify({'recipes': recommended_recipes})

@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe_steps(recipe_id):
    recipe = recipes[recipes['id'] == recipe_id]
    if recipe.empty:
        return jsonify({'steps': 'Recipe not found.'})
    steps = recipe['steps'].values[0]
    return jsonify({'steps': steps})

if __name__ == '__main__':
    app.run(debug=True, port=5500)
