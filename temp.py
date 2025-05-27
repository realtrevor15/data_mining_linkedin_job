from flask import Flask, render_template, jsonify, request
import json
import pandas as pd
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# Global variables to store data
jobs_data = []
profile_data = {}
job_details_data = {}

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
    global jobs_data, profile_data, job_details_data
    
    try:
        # Load job-candidate recommendations JSON
        if os.path.exists('job_candidate.json'):
            with open('job_candidate.json', 'r') as f:
                jobs_data = json.load(f)
        
        # Load job postings CSV first
        if os.path.exists('data/job_posting_filter.csv'):
            job_df = pd.read_csv('data/job_posting_filter.csv')
            job_df['description'] = job_df['description'].apply(html_to_string)
            job_details_data = job_df.set_index('id').to_dict('index')
            
            # Add title to jobs_data
            for job in jobs_data:
                job_id = job['job_id']
                if job_id in job_details_data:
                    job['title'] = job_details_data[job_id].get('title', 'N/A')
                else:
                    job['title'] = 'N/A'
        
        # Load profile info CSV
        if os.path.exists('data/profile_info_filter.csv'):
            profile_df = pd.read_csv('data/profile_info_filter.csv')
            profile_data = profile_df.set_index('public_id').to_dict('index')
            
    except Exception as e:
        print(f"Error loading data: {e}")

@app.route('/')
def index():
    """Main page showing all jobs with candidate recommendations"""
    return render_template('index.html', jobs=jobs_data)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Show detailed view of a job with its candidate recommendations"""
    job = next((j for j in jobs_data if j['job_id'] == job_id), None)
    
    if not job:
        return "Job not found", 404
    
    job_details = job_details_data.get(job_id, {})
    
    # Get candidate details for recommendations
    recommendations = []
    for rec in job.get('recommended_candidates', []):
        candidate_id = rec['public_id']
        candidate_profile = profile_data.get(candidate_id, {})
        recommendations.append({
            'public_id': candidate_id,
            'similarity_score': rec['similarity_score'],
            'profile': candidate_profile
        })

    return render_template('job_detail.html', 
                         job=job, 
                         job_details=job_details,
                         recommendations=recommendations)

@app.route('/api/candidate/<public_id>')
def get_candidate_details(public_id):
    """API endpoint to get candidate details"""
    candidate = profile_data.get(public_id, {})
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404
    return jsonify(candidate)

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
    <title>{% block title %}Candidate Recommendations{% endblock %}</title>
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
        .candidate-card {
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
                        <i class="fas fa-users mr-2"></i>CandidateMatch Pro
                    </a>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-white opacity-80">AI-Powered Candidate Recommendations</span>
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
    <h1 class="text-4xl font-bold text-gray-900 mb-2">Jobs Dashboard</h1>
    <p class="text-gray-600 text-lg">Discover the best candidates for each job position</p>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% for job in jobs %}
    <div class="card-hover bg-white rounded-xl shadow-md overflow-hidden">
        <div class="p-6">
            <div class="flex items-center mb-4">
                <div class="w-12 h-12 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    <i class="fas fa-briefcase"></i>
                </div>
                <div class="ml-4">
                    <h3 class="text-lg font-semibold text-gray-900">Job ID: {{ job.job_id }}</h3>
                    <p class="text-gray-600 text-sm">Position Available</p>
                </div>
            </div>
            
            <div class="mb-4">
                <div class="flex items-center text-sm text-gray-600 mb-2">
                    <i class="fas fa-user-friends mr-2 text-green-500"></i>
                    <span>{{ job.recommended_candidates|length }} Candidate Matches</span>
                </div>
                
                {% if job.recommended_candidates %}
                <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-xs text-gray-500 mb-1">Top Candidate Score</div>
                    <div class="flex items-center">
                        <div class="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                            <div class="similarity-bar h-2 rounded-full" style="width: {{ (job.recommended_candidates[0].similarity_score * 100)|round(1) }}%"></div>
                        </div>
                        <span class="text-sm font-medium text-gray-700">{{ (job.recommended_candidates[0].similarity_score * 100)|round(1) }}%</span>
                    </div>
                </div>
                {% endif %}
            </div>
            
            <a href="/job/{{ job.job_id }}" class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200">
                <i class="fas fa-eye mr-2"></i>
                View Candidates
            </a>
        </div>
    </div>
    {% endfor %}
</div>

{% if not jobs %}
<div class="text-center py-12">
    <i class="fas fa-briefcase text-6xl text-gray-300 mb-4"></i>
    <h3 class="text-xl font-medium text-gray-500 mb-2">No jobs found</h3>
    <p class="text-gray-400">Make sure your job_candidate.json file is in the correct location.</p>
</div>
{% endif %}
{% endblock %}'''

# Job detail template
job_detail_template = '''{% extends "base.html" %}

{% block title %}Job {{ job.job_id }} - Candidate Recommendations{% endblock %}

{% block content %}
<div class="mb-6">
    <a href="/" class="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4">
        <i class="fas fa-arrow-left mr-2"></i>
        Back to Dashboard
    </a>
    
    <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
        <div class="flex items-center mb-6">
            <div class="w-16 h-16 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center text-white font-bold text-2xl mr-6">
                <i class="fas fa-briefcase"></i>
            </div>
            <div>
                <h1 class="text-3xl font-bold text-gray-900">Job: {{ job.title }}</h1>
                <p class="text-gray-600">Job Position</p>
            </div>
        </div>
        
        {% if job_details %}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
            {% if job_details.get('title') %}
            <div class="bg-gray-50 rounded-lg p-3">
                <div class="text-xs text-gray-500 uppercase tracking-wide">Position</div>
                <div class="text-sm font-medium text-gray-900 mt-1">{{ job_details.title }}</div>
            </div>
            {% endif %}
            
            {% if job_details.get('company') %}
            <div class="bg-gray-50 rounded-lg p-3">
                <div class="text-xs text-gray-500 uppercase tracking-wide">Company</div>
                <div class="text-sm font-medium text-gray-900 mt-1">{{ job_details.company }}</div>
            </div>
            {% endif %}
            
            {% if job_details.get('location') %}
            <div class="bg-gray-50 rounded-lg p-3">
                <div class="text-xs text-gray-500 uppercase tracking-wide">Location</div>
                <div class="text-sm font-medium text-gray-900 mt-1">
                    <i class="fas fa-map-marker-alt text-red-500 mr-1"></i>
                    {{ job_details.location }}
                </div>
            </div>
            {% endif %}
            
            {% if job_details.get('employment_type') %}
            <div class="bg-gray-50 rounded-lg p-3">
                <div class="text-xs text-gray-500 uppercase tracking-wide">Type</div>
                <div class="text-sm font-medium text-gray-900 mt-1">{{ job_details.employment_type }}</div>
            </div>
            {% endif %}
        </div>
        
        {% if job_details.get('description') %}
        <div class="mt-6 pt-6 border-t border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
                <i class="fas fa-file-alt text-blue-500 mr-2"></i>
                Job Description
            </h3>
            <div class="text-gray-700 bg-gray-50 rounded-lg p-4">
                {{ job_details.description[:300] }}
                {% if job_details.description|length > 300 %}...{% endif %}
            </div>
        </div>
        {% endif %}
        {% endif %}
    </div>
</div>

<div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-900 mb-4">
        <i class="fas fa-star text-yellow-500 mr-2"></i>
        Recommended Candidates ({{ recommendations|length }})
    </h2>
</div>

<div class="space-y-6" x-data="{ openCandidate: null }">
    {% for rec in recommendations %}
    <div class="candidate-card rounded-xl shadow-md overflow-hidden">
        <div class="p-6">
            <div class="flex justify-between items-start mb-4">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <div class="w-10 h-10 bg-gradient-to-r from-green-400 to-blue-400 rounded-full flex items-center justify-center text-white font-bold text-sm mr-4">
                            {{ rec.public_id[0].upper() }}
                        </div>
                        <h3 class="text-xl font-semibold text-gray-900 mr-4">
                            {{ rec.public_id }}
                        </h3>
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            <i class="fas fa-check-circle mr-1"></i>
                            {{ (rec.similarity_score * 100)|round(1) }}% Match
                        </span>
                    </div>
                    
                    {% if rec.profile %}
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        {% for key, value in rec.profile.items() %}
                        {% if key not in ['public_id'] and value and loop.index <= 4 %}
                        <div>
                            <div class="text-xs text-gray-500 uppercase tracking-wide">{{ key.replace('_', ' ') }}</div>
                            <div class="text-sm font-medium text-gray-900 mt-1">{{ value }}</div>
                        </div>
                        {% endif %}
                        {% endfor %}
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
                    @click="openCandidate = openCandidate === '{{ rec.public_id }}' ? null : '{{ rec.public_id }}'"
                    class="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
                >
                    <i class="fas fa-info-circle mr-2"></i>
                    <span x-text="openCandidate === '{{ rec.public_id }}' ? 'Hide Profile' : 'View Profile'"></span>
                </button>
                
                <div class="flex space-x-2">
                    <button class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white font-medium rounded-lg hover:from-green-600 hover:to-green-700 transition-all duration-200">
                        <i class="fas fa-envelope mr-2"></i>
                        Contact
                    </button>
                    
                    <button class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white font-medium rounded-lg hover:from-purple-600 hover:to-purple-700 transition-all duration-200">
                        <i class="fas fa-bookmark mr-2"></i>
                        Shortlist
                    </button>
                </div>
            </div>
            
            <!-- Candidate Profile Expandable Section -->
            <div x-show="openCandidate === '{{ rec.public_id }}'" 
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0 transform scale-95"
                 x-transition:enter-end="opacity-100 transform scale-100"
                 x-transition:leave="transition ease-in duration-200"
                 x-transition:leave-start="opacity-100 transform scale-100"
                 x-transition:leave-end="opacity-0 transform scale-95"
                 class="mt-6 pt-6 border-t border-gray-200">
                
                {% if rec.profile %}
                <div class="space-y-4">
                    <div>
                        <h4 class="text-lg font-semibold text-gray-900 mb-4">
                            <i class="fas fa-user text-blue-500 mr-2"></i>
                            Candidate Profile
                        </h4>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {% for key, value in rec.profile.items() %}
                            {% if key not in ['public_id'] and value %}
                            <div class="bg-gray-50 rounded-lg p-3">
                                <div class="text-xs text-gray-500 uppercase tracking-wide">{{ key.replace('_', ' ') }}</div>
                                <div class="text-sm font-medium text-gray-900 mt-1">
                                    {% if value|length > 100 %}
                                        {{ value[:100] }}...
                                    {% else %}
                                        {{ value }}
                                    {% endif %}
                                </div>
                            </div>
                            {% endif %}
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% else %}
                <div class="text-center py-8">
                    <i class="fas fa-info-circle text-gray-400 text-2xl mb-2"></i>
                    <p class="text-gray-500">No additional profile information available for this candidate.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% if not recommendations %}
<div class="text-center py-12">
    <i class="fas fa-users text-6xl text-gray-300 mb-4"></i>
    <h3 class="text-xl font-medium text-gray-500 mb-2">No candidate recommendations found</h3>
    <p class="text-gray-400">This job doesn't have any candidate recommendations yet.</p>
</div>
{% endif %}
{% endblock %}'''

# Write template files
with open('templates/base.html', 'w') as f:
    f.write(base_template)

with open('templates/index.html', 'w') as f:
    f.write(index_template)

with open('templates/job_detail.html', 'w') as f:
    f.write(job_detail_template)

print("Flask application created successfully!")
print("\nTo run the application:")
print("1. Make sure you have Flask, pandas, and beautifulsoup4 installed:")
print("   pip install flask pandas beautifulsoup4")
print("2. Place your data files in the correct locations:")
print("   - job_candidate.json (in root directory)")
print("   - data/profile_info_filter.csv")
print("   - data/job_posting_filter.csv")
print("3. Run: python app.py")
print("4. Open http://localhost:5000 in your browser")
print("\nFeatures:")
print("- Dashboard showing all jobs with candidate recommendations")
print("- Detailed job view with candidate profiles and match scores")
print("- Expandable candidate profiles with full information")
print("- Interactive UI with hover effects and animations")
print("- Contact and shortlist buttons for candidate management")