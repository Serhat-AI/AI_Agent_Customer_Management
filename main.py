import os
import sys
from datetime import datetime
from config import validate_config, SUMMARY_RECIPIENT_EMAIL, GMAIL_USER_EMAIL
from gmail_client import GmailClient
from rag_engine import RAGEngine
from analysis_engine import AnalysisEngine

class RSDAnalysisAgent:
    def __init__(self):
        validate_config()
        self.gmail_client = GmailClient()
        self.analysis_engine = AnalysisEngine()
    
    def run_once(self):
        """Run the agent once: fetch emails, analyze, send reports"""
        print(f"\n{'='*60}")
        print(f"RSD Analysis Agent - Run at {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
        
        # Step 1: Index documents (check if needed)
        self._ensure_documents_indexed()
        
        # Step 2: Fetch unread RSDs from Gmail
        print("Fetching unread RSD emails...")
        emails = self.gmail_client.get_unread_emails()
        
        if not emails:
            print("No new RSD emails found.\n")
            return
        
        print(f"Found {len(emails)} unread RSD email(s)\n")
        
        # Step 3: Process each email
        for email in emails:
            if email is None:
                continue
            
            self._process_email(email)
    
    def _ensure_documents_indexed(self):
        """Ensure documents are indexed in vector DB"""
        rag = RAGEngine()
        info = rag.get_collection_info()
        
        if info['status'] == 'ready':
            print(f"Vector DB ready: {info['total_chunks']} chunks indexed\n")
        else:
            print("Indexing project documents... (this may take a moment)")
            rag.index_documents()
            print()
    
    def _process_email(self, email: dict):
        """Process a single RSD email"""
        print(f"Processing email: {email['subject']}")
        print(f"From: {email['sender']}\n")
        
        # Combine subject and body for analysis
        rsd_text = f"{email['subject']}\n\n{email['body']}"
        
        # Download attachments if present
        attachment_texts = []
        if email['attachments']:
            print(f"Found {len(email['attachments'])} attachment(s)")
            for attachment in email['attachments']:
                filepath = self.gmail_client.download_attachment(
                    email['id'],
                    attachment['attachmentId'],
                    attachment['filename']
                )
                if filepath:
                    print(f"  - Downloaded: {attachment['filename']}")
        
        print()
        
        # Analyze RSD
        print("Analyzing RSD...")
        analysis = self.analysis_engine.analyze_rsd(
            rsd_content=rsd_text,
            rsd_subject=email['subject']
        )
        
        print(f"Analysis complete. Found {len(analysis['similar_solutions'])} similar solution(s)\n")
        
        # Generate report
        report_html = self.analysis_engine.generate_summary_report(
            analysis,
            rsd_sender=email['sender']
        )
        
        # Send email summary
        print(f"Sending report to {SUMMARY_RECIPIENT_EMAIL}...")
        self.gmail_client.send_email(
            recipient=SUMMARY_RECIPIENT_EMAIL,
            subject=f"RSD Analysis Report: {email['subject']}",
            body=report_html
        )
        
        # Mark original email as read
        self.gmail_client.mark_as_read(email['id'])
        print("Email marked as read.\n")
    
    def initialize_index(self, force_reindex=False):
        """Manually initialize or reindex the document database"""
        print("Initializing document index...")
        rag = RAGEngine()
        rag.index_documents(force_reindex=force_reindex)
        print("Index initialization complete!")

def main():
    try:
        agent = RSDAnalysisAgent()
        
        if len(sys.argv) > 1 and sys.argv[1] == '--init':
            force = '--force' in sys.argv
            agent.initialize_index(force_reindex=force)
        else:
            agent.run_once()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
