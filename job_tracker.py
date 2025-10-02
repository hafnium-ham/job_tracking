import requests
import json
import os
from datetime import datetime
import re
import sys

class EnhancedJobTracker:
    def __init__(self):
        self.jobs_file = "jobs.json"
        self.jobs = self.load_jobs()
    
    def load_jobs(self):
        """Load existing jobs from file"""
        if os.path.exists(self.jobs_file):
            try:
                with open(self.jobs_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_jobs(self):
        """Save jobs to file"""
        with open(self.jobs_file, 'w') as f:
            json.dump(self.jobs, f, indent=2)
    
    def extract_from_pdf(self, pdf_path):
        """Extract text content from PDF file"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                return text_content.strip()
                
        except ImportError:
            print("PyPDF2 not installed. Installing...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
                import PyPDF2
                
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
                    
                    return text_content.strip()
            except Exception as e:
                print(f"Failed to install PyPDF2: {e}")
                return None
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None
    
    def extract_from_url(self, url):
        """Extract content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            # Clean up HTML content
            html_content = response.text
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Convert HTML to text
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return text_content
            
        except Exception as e:
            print(f"Error extracting from URL: {e}")
            return None
    
    def extract_job_info_from_content(self, content, source_type, source):
        """Extract job information from text content using Ollama"""
        try:
            # Limit content size for Ollama
            if len(content) > 8000:
                content = content[:8000]
            
            # Use Ollama to extract job information
            job_info = self.extract_with_ollama(content, source_type, source)
            
            if job_info:
                job_info.update({
                    'source': source,
                    'source_type': source_type,
                    'date_added': datetime.now().strftime('%m/%d/%Y'),
                    'status': 'Applied',
                    'last_update': datetime.now().strftime('%m/%d/%Y')
                })
                return job_info
            else:
                return None
        
        except Exception as e:
            print(f"Error extracting job info: {e}")
            return None
    
    def extract_with_ollama(self, content, source_type, source):
        """Use Ollama to extract job information with fallback"""
        # First try Ollama
        ollama_result = self.try_ollama_extraction(content)
        if ollama_result:
            return ollama_result
        
        # If Ollama fails, use fallback extraction
        print("Ollama failed, using fallback extraction...")
        return self.fallback_extraction(content, source)
    
    def try_ollama_extraction(self, content):
        """Try to extract using Ollama with retries"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting Ollama extraction (attempt {attempt + 1}/{max_retries})...")
                
                # Enhanced prompt for better extraction
                prompt = f"""Extract job information from this content. Return ONLY a valid JSON object:
{{
  "title": "job title here",
  "company": "company name here", 
  "description": "brief description (max 400 chars)",
  "location": "location if found",
  "salary": "salary if found",
  "requirements": "key requirements if found",
  "job_type": "full-time/part-time/contract if found"
}}

Content:
{content[:4000]}"""
                
                # Try different models in order of preference
                models = ['phi3:mini', 'llama3.2', 'llama3.1', 'llama3', 'llama2']
                
                for model in models:
                    try:
                        print(f"Trying model: {model}")
                        
                        ollama_response = requests.post(
                            'http://localhost:11434/api/generate',
                            json={
                                'model': model,
                                'prompt': prompt,
                                'stream': False,
                                'options': {
                                    'temperature': 0.1,
                                    'top_p': 0.9,
                                    'num_predict': 300
                                }
                            },
                            timeout=120  # 2 minutes timeout
                        )
                        
                        if ollama_response.status_code == 200:
                            result = ollama_response.json()
                            response_text = result.get('response', '').strip()
                            
                            # Try to parse JSON from response
                            job_data = self.parse_ollama_response(response_text)
                            if job_data:
                                print(f"Successfully extracted with {model}")
                                return job_data
                        
                    except requests.exceptions.ConnectionError:
                        print(f"Connection error with model {model}")
                        continue
                    except requests.exceptions.Timeout:
                        print(f"Timeout with model {model}")
                        continue
                    except Exception as e:
                        print(f"Error with model {model}: {e}")
                        continue
                
                # If all models failed, wait before retry
                if attempt < max_retries - 1:
                    print("Waiting 5 seconds before retry...")
                    import time
                    time.sleep(5)
                    
            except Exception as e:
                print(f"Ollama attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(3)
        
        return None
    
    def parse_ollama_response(self, response_text):
        """Parse JSON from Ollama response"""
        try:
            # Find JSON in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                job_data = json.loads(json_str)
                
                # Format the data
                formatted_data = {
                    'title': job_data.get('title', 'Unknown Title'),
                    'company': job_data.get('company', 'Unknown Company'),
                    'description': job_data.get('description', 'No description found')[:500],
                    'other_info': {}
                }
                
                # Add optional fields to other_info
                optional_fields = ['location', 'salary', 'requirements', 'job_type']
                for field in optional_fields:
                    if job_data.get(field):
                        formatted_data['other_info'][field] = job_data[field]
                
                return formatted_data
                
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
        except Exception as e:
            print(f"Response parse error: {e}")
        
        return None
    
    def fallback_extraction(self, content, source):
        """Fallback extraction using simple text parsing"""
        try:
            # Try to find title (look for common patterns)
            title = "Unknown Title"
            title_patterns = [
                r'(?:job\s+title|position|role)[\s:]+([^\n]{10,100})',
                r'(?:^|\n)([A-Z][^.\n]{10,80}(?:engineer|developer|manager|analyst|specialist|coordinator))',
                r'(?:^|\n)([A-Z][^.\n]{10,80}(?:intern|associate|director|lead))',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    potential_title = match.group(1).strip()
                    if len(potential_title) > 5 and len(potential_title) < 200:
                        title = potential_title
                        break
            
            # Try to find company
            company = "Unknown Company"
            company_patterns = [
                r'(?:company|employer|organization)[\s:]+([^\n]{2,50})',
                r'(?:at|@)\s+([A-Z][a-zA-Z\s&.,]{2,40})',
                r'([A-Z][a-zA-Z\s&.,]{2,40})(?:\s+is\s+(?:hiring|looking|seeking))',
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    potential_company = match.group(1).strip()
                    if len(potential_company) > 1 and len(potential_company) < 100:
                        company = potential_company
                        break
            
            # Use first part of content as description
            description = content[:500] + "..." if len(content) > 500 else content
            if not description.strip():
                description = "No description found"
            
            # Try to find additional info
            other_info = {}
            
            # Salary
            salary_patterns = [
                r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:year|hour|yr|hr|annum))?',
                r'[\d,]+k?(?:\s*-\s*[\d,]+k?)?\s*(?:per\s+year|annually|/year)',
            ]
            
            for pattern in salary_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    other_info['salary'] = match.group()
                    break
            
            # Location
            location_patterns = [
                r'(?:location|based in|located in)[\s:]+([^\n]{5,50})',
                r'([A-Z][a-z]+,\s*[A-Z]{2}(?:\s+\d{5})?)',
                r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    if len(location) > 2 and len(location) < 100:
                        other_info['location'] = location
                        break
            
            # Job type
            job_type_match = re.search(r'(full[_\s-]?time|part[_\s-]?time|contract|temporary|intern)', content, re.IGNORECASE)
            if job_type_match:
                other_info['job_type'] = job_type_match.group(1)
            
            return {
                'title': title,
                'company': company,
                'description': description,
                'other_info': other_info
            }
            
        except Exception as e:
            print(f"Fallback extraction error: {e}")
            return {
                'title': "Unknown Title",
                'company': "Unknown Company", 
                'description': "No description found",
                'other_info': {}
            }
    
    def add_job_from_input(self, user_input):
        """Add a job from various input types"""
        user_input = user_input.strip()
        
        # Check if it's a URL
        if user_input.startswith('http'):
            return self.add_job_from_url(user_input)
        
        # Check if it's a PDF file path
        elif user_input.endswith('.pdf') and os.path.exists(user_input):
            return self.add_job_from_pdf(user_input)
        
        # Check if it's a text file path
        elif user_input.endswith('.txt') and os.path.exists(user_input):
            return self.add_job_from_text_file(user_input)
        
        # Otherwise treat as direct text content
        else:
            return self.add_job_from_text(user_input)
    
    def add_job_from_url(self, url):
        """Add a job from URL"""
        print("Processing URL...")
        content = self.extract_from_url(url)
        if not content:
            return False
        
        job_info = self.extract_job_info_from_content(content, 'url', url)
        return self.save_job_info(job_info)
    
    def add_job_from_pdf(self, pdf_path):
        """Add a job from PDF file"""
        print("Processing PDF...")
        content = self.extract_from_pdf(pdf_path)
        if not content:
            return False
        
        job_info = self.extract_job_info_from_content(content, 'pdf', pdf_path)
        return self.save_job_info(job_info)
    
    def add_job_from_text_file(self, text_path):
        """Add a job from text file"""
        print("Processing text file...")
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            job_info = self.extract_job_info_from_content(content, 'text_file', text_path)
            return self.save_job_info(job_info)
        except Exception as e:
            print(f"Error reading text file: {e}")
            return False
    
    def add_job_from_text(self, text_content):
        """Add a job from direct text content"""
        print("Processing text content...")
        
        if len(text_content) < 50:
            print("Text content too short. Please provide more details.")
            return False
        
        job_info = self.extract_job_info_from_content(text_content, 'text', 'Direct Input')
        return self.save_job_info(job_info)
    
    def save_job_info(self, job_info):
        """Save job info and check for duplicates"""
        if not job_info:
            print("Failed to extract job information")
            return False
        
        # Check for duplicates based on title and company
        for existing_job in self.jobs:
            if (existing_job.get('title', '').lower() == job_info.get('title', '').lower() and 
                existing_job.get('company', '').lower() == job_info.get('company', '').lower()):
                print("Similar job already exists!")
                return False
        
        self.jobs.append(job_info)
        self.save_jobs()
        print(f"Added job: {job_info['title']} at {job_info['company']}")
        return True
    
    def display_jobs(self):
        """Display all jobs in easy to read format"""
        if not self.jobs:
            print("No jobs saved yet.")
            return
        
        print("\n" + "="*80)
        print("SAVED JOBS")
        print("="*80)
        
        for i, job in enumerate(self.jobs, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Date Added: {job['date_added']}")
            print(f"   Status: {job['status']}")
            print(f"   Source: {job.get('source_type', 'url')} - {job.get('source', 'N/A')}")
            
            if job.get('other_info'):
                for key, value in job['other_info'].items():
                    print(f"   {key.title()}: {value}")
            
            print(f"   Description: {job['description'][:100]}...")
            print("-" * 80)
    
    def run(self):
        """Main loop - wait for various inputs"""
        print("Enhanced Job Tracker Started!")
        print("Supported inputs:")
        print("  📄 PDF files: /path/to/job.pdf")
        print("  📝 Text files: /path/to/job.txt")
        print("  🌐 URLs: https://example.com/job")
        print("  ✏️  Direct text: paste job description directly")
        print("  📋 Commands: 'show' to display jobs, 'quit' to exit")
        print("-" * 70)
        
        while True:
            try:
                print("\nOptions:")
                print("1. Enter job URL")
                print("2. Enter PDF file path")
                print("3. Enter text file path") 
                print("4. Paste job description text")
                print("5. Show all jobs")
                print("6. Quit")
                
                choice = input("\nSelect option (1-6) or enter content directly: ").strip()
                
                if choice == '6' or choice.lower() == 'quit':
                    print("Goodbye!")
                    break
                elif choice == '5' or choice.lower() == 'show':
                    self.display_jobs()
                elif choice in ['1', '2', '3', '4']:
                    if choice == '1':
                        user_input = input("Enter job URL: ").strip()
                    elif choice == '2':
                        user_input = input("Enter PDF file path: ").strip()
                    elif choice == '3':
                        user_input = input("Enter text file path: ").strip()
                    elif choice == '4':
                        print("Paste job description (press Enter twice when done):")
                        lines = []
                        while True:
                            line = input()
                            if line == "" and len(lines) > 0 and lines[-1] == "":
                                break
                            lines.append(line)
                        user_input = "\n".join(lines).strip()
                    
                    if user_input:
                        self.add_job_from_input(user_input)
                else:
                    # Try to process as direct input
                    self.add_job_from_input(choice)
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    tracker = EnhancedJobTracker()
    tracker.run()