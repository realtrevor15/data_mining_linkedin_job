from flask import Flask, render_template, jsonify, request
import json
import pandas as pd
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# Global variables to store data
candidates_data = []
profile_data = {}
jobs_data = {}

def html_to_string(html_content):
    try:
        # Kiểm tra nếu đầu vào là NaN hoặc không phải chuỗi
        if pd.isna(html_content) or not isinstance(html_content, str):
            return ""
        # Tạo đối tượng BeautifulSoup từ chuỗi HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        # Trích xuất text, loại bỏ thẻ HTML
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        return f"Đã có lỗi xảy ra: {str(e)}"

def load_data():
    """Load data from JSON and CSV files"""
    global candidates_data, profile_data, jobs_data
    
    try:
        # Load recommendations JSON
        if os.path.exists('results.json'):
            with open('results.json', 'r') as f:
                candidates_data = json.load(f)
        
        # Load profile info CSV
        if os.path.exists('data/profile_info_filter.csv'):
            profile_df = pd.read_csv('data/profile_info_filter.csv')
            profile_data = profile_df.set_index('public_id').to_dict('index')
            # candidates_data['name'] = 

        
        # Load job postings CSV
        if os.path.exists('data/job_posting_filter.csv'):
            jobs_df = pd.read_csv('data/job_posting_filter.csv',)
            jobs_df['description'] = jobs_df['description'].apply(html_to_string)
            jobs_data = jobs_df.set_index('id').to_dict('index')
            
    except Exception as e:
        print(f"Error loading data: {e}")

@app.route('/')
def index():
    """Main page showing all candidates"""
    return render_template('index.html', candidates=candidates_data)

@app.route('/candidate/<public_id>')
def candidate_detail(public_id):
    """Show detailed view of a candidate with their job recommendations"""
    candidate = next((c for c in candidates_data if c['public_id'] == public_id), None)
    
    if not candidate:
        return "Candidate not found", 404
    
    profile = profile_data.get(public_id, {})
    
    # Get job details for recommendations
    recommendations = []
    for rec in candidate.get('recommendations', []):
        job_id = rec['job_id']
        job_details = jobs_data.get(job_id, {})
        recommendations.append({
            'job_id': job_id,
            'similarity_score': rec['similarity_score'],
            'job_details': job_details
        })

    return render_template('candidate_detail.html', 
                         candidate=candidate, 
                         profile=profile,
                         recommendations=recommendations)

@app.route('/api/job/<int:job_id>')
def get_job_details(job_id):
    """API endpoint to get job details"""
    job = jobs_data.get(job_id, {})
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

if __name__ == '__main__':
    load_data()
    app.run(debug=True)


# Create templates directory and files
import os
os.makedirs('templates', exist_ok=True)

# Base template
base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Job Recommendations{% endblock %}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .card-hover {
            transition: all 0.3s ease;
            transform: translateY(0);
        }
        .card-hover:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        .similarity-bar {
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        }
        .job-card {
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <nav class="gradient-bg shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/" class="text-white text-xl font-bold">
                        <i class="fas fa-briefcase mr-2"></i>JobMatch Pro
                    </a>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-white opacity-80">AI-Powered Job Recommendations</span>
                </div>
            </div>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/alpinejs/3.10.2/cdn.min.js" defer></script>
</body>
</html>'''

# Index template
index_template = '''{% extends "base.html" %}

{% block content %}
<div class="mb-8">
    <h1 class="text-4xl font-bold text-gray-900 mb-2">Candidate Dashboard</h1>
    <p class="text-gray-600 text-lg">Discover personalized job recommendations for our candidates</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% for candidate in candidates %}
    <div class="card-hover bg-white rounded-xl shadow-md overflow-hidden">
        <div class="p-6">
            <div class="flex items-center mb-4">
                <div class="w-12 h-12 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {{ candidate.public_id[0].upper() }}
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">{{ candidate.public_id }}</h3>
                    <p class="text-gray-600 text-sm">Candidate Profile</p>
                </div>
            </div>
            
            <div class="mb-4">
                <div class="flex items-center text-sm text-gray-600 mb-2">
                    <i class="fas fa-chart-line mr-2 text-blue-500"></i>
                    <span>{{ candidate.recommendations|length }} Job Matches</span>
                </div>
                
                {% if candidate.recommendations %}
                <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-xs text-gray-500 mb-1">Top Match Score</div>
                    <div class="flex items-center">
                        <div class="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                            <div class="similarity-bar h-2 rounded-full" style="width: {{ (candidate.recommendations[0].similarity_score * 100)|round(1) }}%"></div>
                        </div>
                        <span class="text-sm font-medium text-gray-700">{{ (candidate.recommendations[0].similarity_score * 100)|round(1) }}%</span>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <a href="/candidate/{{ candidate.public_id }}" class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200">
                <i class="fas fa-eye mr-2"></i>
                View Recommendations
            </a>
        </div>
    </div>
    {% endfor %}
</div>

{% if not candidates %}
<div class="text-center py-12">
    <i class="fas fa-users text-6xl text-gray-300 mb-4"></i>
    <h3 class="text-xl font-medium text-gray-500 mb-2">No candidates found</h3>
    <p class="text-gray-400">Make sure your results.json file is in the correct location.</p>
</div>
{% endif %}
{% endblock %}'''

# Candidate detail template
candidate_detail_template = '''{% extends "base.html" %}

{% block title %}{{ candidate.public_id }} - Job Recommendations{% endblock %}

{% block content %}
<div class="mb-6">
    <a href="/" class="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4">
        <i class="fas fa-arrow-left mr-2"></i>
        Back to Dashboard
    </a>
    
    <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
        <div class="flex items-center mb-6">
            <div class="w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white font-bold text-2xl mr-6">
                {{ candidate.public_id[0].upper() }}
            </div>
            <div>
                <h1 class="text-3xl font-bold text-gray-900">{{ candidate.public_id }}</h1>
                <p class="text-gray-600">Candidate Profile</p>
            </div>
        </div>
        
        {% if profile %}
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
            {% for key, value in profile.items() %}
            {% if key != 'public_id' %}
            <div class="bg-gray-50 rounded-lg p-3">
                <div class="text-xs text-gray-500 uppercase tracking-wide">{{ key.replace('_', ' ') }}</div>
                <div class="text-sm font-medium text-gray-900 mt-1">{{ value }}</div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
        {% endif %}
    </div>
</div>

<div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-900 mb-4">
        <i class="fas fa-star text-yellow-500 mr-2"></i>
        Recommended Jobs ({{ recommendations|length }})
    </h2>
</div>

<div class="space-y-6" x-data="{ openJob: null }">
    {% for rec in recommendations %}
    <div class="job-card rounded-xl shadow-md overflow-hidden">
        <div class="p-6">
            <div class="flex justify-between items-start mb-4">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <h3 class="text-xl font-semibold text-gray-900 mr-4">
                            Job ID: {{ rec.job_id }}
                        </h3>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            <i class="fas fa-check-circle mr-1"></i>
                            {{ (rec.similarity_score * 100)|round(1) }}% Match
                        </span>
                    </div>
                    
                    {% if rec.job_details %}
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        {% if rec.job_details.get('title') %}
                        <div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Position</div>
                            <div class="text-sm font-medium text-gray-900 mt-1">{{ rec.job_details.title }}</div>
                        </div>
                        {% endif %}
                        
                        {% if rec.job_details.get('company') %}
                        <div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Company</div>
                            <div class="text-sm font-medium text-gray-900 mt-1">{{ rec.job_details.company }}</div>
                        </div>
                        {% endif %}
                        
                        {% if rec.job_details.get('location') %}
                        <div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Location</div>
                            <div class="text-sm font-medium text-gray-900 mt-1">
                                <i class="fas fa-map-marker-alt text-red-500 mr-1"></i>
                                {{ rec.job_details.location }}
                            </div>
                        </div>
                        {% endif %}
                        
                        {% if rec.job_details.get('employment_type') %}
                        <div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">Type</div>
                            <div class="text-sm font-medium text-gray-900 mt-1">{{ rec.job_details.employment_type }}</div>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    <div class="mb-4">
                        <div class="text-xs text-gray-500 mb-2">Match Score</div>
                        <div class="flex items-center">
                            <div class="flex-1 bg-gray-200 rounded-full h-3 mr-3">
                                <div class="similarity-bar h-3 rounded-full" style="width: {{ (rec.similarity_score * 100)|round(1) }}%"></div>
                            </div>
                            <span class="text-sm font-bold text-gray-700">{{ (rec.similarity_score * 100)|round(1) }}%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="flex justify-between items-center pt-4 border-t border-gray-200">
                <button 
                    @click="openJob = openJob === {{ rec.job_id }} ? null : {{ rec.job_id }}"
                    class="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                    <i class="fas fa-info-circle mr-2"></i>
                    <span x-text="openJob === {{ rec.job_id }} ? 'Hide Details' : 'View Details'"></span>
                </button>
                
                {% if rec.job_details.get('apply_url') or rec.job_details.get('url') %}
                <a href="{{ rec.job_details.get('apply_url', rec.job_details.get('url', '#')) }}" 
                   target="_blank"
                   class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white font-medium rounded-lg hover:from-green-600 hover:to-green-700 transition-all duration-200">
                    <i class="fas fa-external-link-alt mr-2"></i>
                    Apply Now
                </a>
                {% endif %}
            </div>
            
            <!-- Job Details Expandable Section -->
            <div x-show="openJob === {{ rec.job_id }}" 
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0 transform scale-95"
                 x-transition:enter-end="opacity-100 transform scale-100"
                 x-transition:leave="transition ease-in duration-200"
                 x-transition:leave-start="opacity-100 transform scale-100"
                 x-transition:leave-end="opacity-0 transform scale-95"
                 class="mt-6 pt-6 border-t border-gray-200">
                
                {% if rec.job_details %}
                <div class="space-y-4">
                    {% if rec.job_details.get('description') %}
                    <div>
                        <h4 class="text-lg font-semibold text-gray-900 mb-2">
                            <i class="fas fa-file-alt text-blue-500 mr-2"></i>
                            Job Description
                        </h4>
                        <div class="text-gray-700 bg-gray-50 rounded-lg p-4">
                            {{ rec.job_details.description[:500] }}
                            {% if rec.job_details.description|length > 500 %}...{% endif %}
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if rec.job_details.get('requirements') %}
                    <div>
                        <h4 class="text-lg font-semibold text-gray-900 mb-2">
                            <i class="fas fa-list-check text-green-500 mr-2"></i>
                            Requirements
                        </h4>
                        <div class="text-gray-700 bg-gray-50 rounded-lg p-4">
                            {{ rec.job_details.requirements }}
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if rec.job_details.get('salary_range') %}
                    <div>
                        <h4 class="text-lg font-semibold text-gray-900 mb-2">
                            <i class="fas fa-dollar-sign text-green-500 mr-2"></i>
                            Salary Range
                        </h4>
                        <div class="text-gray-700 bg-green-50 rounded-lg p-4 font-medium">
                            {{ rec.job_details.salary_range }}
                        </div>
                    </div>
                    {% endif %}
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for key, value in rec.job_details.items() %}
                        {% if key not in ['job_id', 'title', 'company', 'location', 'employment_type', 'description', 'requirements', 'salary_range', 'apply_url', 'url'] and value %}
                        <div class="bg-gray-50 rounded-lg p-3">
                            <div class="text-xs text-gray-500 uppercase tracking-wide">{{ key.replace('_', ' ') }}</div>
                            <div class="text-sm font-medium text-gray-900 mt-1">{{ value }}</div>
                        </div>
                        {% endif %}
                        {% endfor %}
                    </div>
                </div>
                {% else %}
                <div class="text-center py-8">
                    <i class="fas fa-info-circle text-gray-400 text-2xl mb-2"></i>
                    <p class="text-gray-500">No additional details available for this job.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% if not recommendations %}
<div class="text-center py-12">
    <i class="fas fa-briefcase text-6xl text-gray-300 mb-4"></i>
    <h3 class="text-xl font-medium text-gray-500 mb-2">No job recommendations found</h3>
    <p class="text-gray-400">This candidate doesn't have any job recommendations yet.</p>
</div>
{% endif %}
{% endblock %}'''

# Write template files
with open('templates/base.html', 'w') as f:
    f.write(base_template)

with open('templates/index.html', 'w') as f:
    f.write(index_template)

with open('templates/candidate_detail.html', 'w') as f:
    f.write(candidate_detail_template)

print("Flask application created successfully!")
print("\nTo run the application:")
print("1. Make sure you have Flask and pandas installed: pip install flask pandas")
print("2. Place your data files (results.json, profile_info.csv, job_posting.csv) in the same directory")
print("3. Run: python app.py")
print("4. Open http://localhost:5000 in your browser")