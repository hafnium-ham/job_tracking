import json
import os
from datetime import datetime, timedelta

class JobManager:
    def __init__(self):
        self.jobs_file = "jobs.json"
        self.jobs = self.load_jobs()
    
    def load_jobs(self):
        """Load jobs from file"""
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
    
    def check_ghosted_jobs(self):
        """Mark jobs as ghosted if no update in 6 months"""
        today = datetime.now()
        updated_count = 0
        
        for job in self.jobs:
            try:
                last_update = datetime.strptime(job['last_update'], '%m/%d/%Y')
                days_since_update = (today - last_update).days
                
                if days_since_update >= 180 and job['status'] not in ['Ghosted', 'Rejected', 'Hired']:
                    job['status'] = 'Ghosted'
                    job['last_update'] = today.strftime('%m/%d/%Y')
                    updated_count += 1
            except:
                continue
        
        if updated_count > 0:
            self.save_jobs()
            print(f"Marked {updated_count} jobs as ghosted")
        else:
            print("No jobs to mark as ghosted")
    
    def display_jobs_numbered(self):
        """Display jobs with numbers for selection"""
        if not self.jobs:
            print("No jobs found.")
            return False
        
        print("\n" + "="*80)
        print("ALL JOBS")
        print("="*80)
        
        for i, job in enumerate(self.jobs, 1):
            status_indicator = "👻" if job['status'] == 'Ghosted' else "📝"
            print(f"{i:2d}. {status_indicator} {job['title']}")
            print(f"     Company: {job['company']}")
            print(f"     Status: {job['status']}")
            print(f"     Added: {job['date_added']} | Updated: {job['last_update']}")
            print("-" * 80)
        
        return True
    
    def update_job_status(self, job_index):
        """Update status of a specific job"""
        if job_index < 1 or job_index > len(self.jobs):
            print("Invalid job number")
            return
        
        job = self.jobs[job_index - 1]
        
        print(f"\nUpdating: {job['title']} at {job['company']}")
        print(f"Current status: {job['status']}")
        
        print("\nStatus options:")
        print("1. Applied")
        print("2. Interview Scheduled")
        print("3. Interviewed")
        print("4. Waiting for Response")
        print("5. Rejected")
        print("6. Hired")
        print("7. Ghosted")
        print("8. Withdrawn")
        
        try:
            choice = input("Select new status (1-8): ").strip()
            
            status_map = {
                '1': 'Applied',
                '2': 'Interview Scheduled',
                '3': 'Interviewed',
                '4': 'Waiting for Response',
                '5': 'Rejected',
                '6': 'Hired',
                '7': 'Ghosted',
                '8': 'Withdrawn'
            }
            
            if choice in status_map:
                job['status'] = status_map[choice]
                job['last_update'] = datetime.now().strftime('%m/%d/%Y')
                
                # Add notes if desired
                notes = input("Add notes (optional): ").strip()
                if notes:
                    if 'notes' not in job:
                        job['notes'] = []
                    job['notes'].append({
                        'date': datetime.now().strftime('%m/%d/%Y'),
                        'note': notes
                    })
                
                self.save_jobs()
                print(f"Updated job status to: {job['status']}")
            else:
                print("Invalid choice")
        
        except KeyboardInterrupt:
            print("\nUpdate cancelled")
    
    def show_job_details(self, job_index):
        """Show detailed information for a specific job"""
        if job_index < 1 or job_index > len(self.jobs):
            print("Invalid job number")
            return
        
        job = self.jobs[job_index - 1]
        
        print("\n" + "="*80)
        print("JOB DETAILS")
        print("="*80)
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Status: {job['status']}")
        print(f"Date Added: {job['date_added']}")
        print(f"Last Update: {job['last_update']}")
        
        if job.get('other_info'):
            print("\nAdditional Info:")
            for key, value in job['other_info'].items():
                print(f"  {key.title()}: {value}")
        
        print(f"\nDescription:\n{job['description']}")
        
        if job.get('notes'):
            print("\nNotes:")
            for note in job['notes']:
                print(f"  {note['date']}: {note['note']}")
        
        print(f"\nURL: {job['url']}")
        print("="*80)
    
    def show_statistics(self):
        """Show job application statistics"""
        if not self.jobs:
            print("No jobs to analyze")
            return
        
        status_counts = {}
        for job in self.jobs:
            status = job['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\n" + "="*50)
        print("JOB APPLICATION STATISTICS")
        print("="*50)
        print(f"Total Jobs: {len(self.jobs)}")
        print("\nStatus Breakdown:")
        for status, count in status_counts.items():
            percentage = (count / len(self.jobs)) * 100
            print(f"  {status}: {count} ({percentage:.1f}%)")
        print("="*50)
    
    def run(self):
        """Main menu loop"""
        print("Job Manager Started!")
        print("Commands:")
        print("  1. Show all jobs")
        print("  2. Update job status")
        print("  3. Show job details")
        print("  4. Check for ghosted jobs")
        print("  5. Show statistics")
        print("  6. Quit")
        print("-" * 50)
        
        while True:
            try:
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == '1':
                    self.display_jobs_numbered()
                
                elif choice == '2':
                    if self.display_jobs_numbered():
                        try:
                            job_num = int(input("Enter job number to update: "))
                            self.update_job_status(job_num)
                        except ValueError:
                            print("Invalid number")
                
                elif choice == '3':
                    if self.display_jobs_numbered():
                        try:
                            job_num = int(input("Enter job number for details: "))
                            self.show_job_details(job_num)
                        except ValueError:
                            print("Invalid number")
                
                elif choice == '4':
                    self.check_ghosted_jobs()
                
                elif choice == '5':
                    self.show_statistics()
                
                elif choice == '6':
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid choice. Enter 1-6")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    manager = JobManager()
    manager.run()