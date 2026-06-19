from typing import List, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from rag_engine import RAGEngine
from config import OPENAI_API_KEY, USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL

class AnalysisEngine:
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM (OpenAI or Ollama)"""
        if USE_OLLAMA:
            from langchain_community.llms import Ollama
            return Ollama(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_MODEL,
                temperature=0.3
            )
        else:
            return ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model='gpt-3.5-turbo',
                temperature=0.3
            )
    
    def analyze_rsd(self, rsd_content: str, rsd_subject: str = "") -> dict:
        """Analyze RSD and find similar solutions"""
        
        # Extract key requirements from RSD
        key_requirements = self._extract_requirements(rsd_content)
        
        # Search for similar solutions
        similar_solutions = self.rag_engine.search_similar_solutions(
            query=rsd_content,
            top_k=5
        )
        
        # Generate analysis
        analysis = {
            'rsd_subject': rsd_subject,
            'key_requirements': key_requirements,
            'similar_solutions_found': len(similar_solutions) > 0,
            'similar_solutions': similar_solutions,
            'recommendations': self._generate_recommendations(rsd_content, similar_solutions)
        }
        
        return analysis
    
    def _extract_requirements(self, rsd_content: str) -> List[str]:
        """Extract key requirements from RSD using LLM"""
        template = """Extract the top 5 key requirements from this RSD (Requirements/Specification Document). 
        Return them as a bullet list with brief descriptions.
        
        RSD Content:
        {rsd_content}
        
        Key Requirements:"""
        
        prompt = PromptTemplate(template=template, input_variables=["rsd_content"])
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({"rsd_content": rsd_content[:2000]})  # Limit to 2000 chars
            
            # Parse response into list
            lines = response.content.split('\n')
            requirements = [line.strip() for line in lines if line.strip() and line.strip().startswith('-')]
            return requirements[:5]
        
        except Exception as e:
            print(f"Error extracting requirements: {e}")
            return ["Unable to extract requirements"]
    
    def _generate_recommendations(self, rsd_content: str, similar_solutions: List[dict]) -> str:
        """Generate recommendations based on analysis"""
        
        if not similar_solutions:
            return "No similar solutions found in archive. This may be a unique project."
        
        solutions_summary = "\n".join([
            f"- {sol['filename']} (Similarity: {sol['similarity_score']})"
            for sol in similar_solutions[:3]
        ])
        
        template = """Based on the customer's RSD and our similar previous solutions, 
        provide 2-3 brief recommendations for reusing or adapting existing components.
        
        RSD Key Content:
        {rsd_content}
        
        Similar Solutions We've Built:
        {solutions_summary}
        
        Recommendations:"""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["rsd_content", "solutions_summary"]
        )
        
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "rsd_content": rsd_content[:1500],
                "solutions_summary": solutions_summary
            })
            return response.content
        
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return "Unable to generate recommendations"
    
    def generate_summary_report(self, analysis: dict, rsd_sender: str) -> str:
        """Generate HTML email summary report"""
        
        similar_solutions_html = ""
        if analysis['similar_solutions']:
            similar_solutions_html = "<h3>Similar Solutions Found:</h3><ul>"
            for sol in analysis['similar_solutions']:
                similar_solutions_html += f"""
                <li>
                    <strong>{sol['filename']}</strong> (Similarity: {sol['similarity_score']})
                    <br><small>Source: {sol['source_file']}</small>
                </li>
                """
            similar_solutions_html += "</ul>"
        else:
            similar_solutions_html = "<p><em>No similar solutions found in our archive.</em></p>"
        
        html_report = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>RSD Analysis Report</h2>
            
            <h3>Customer Request:</h3>
            <p><strong>Subject:</strong> {analysis['rsd_subject']}</p>
            <p><strong>From:</strong> {rsd_sender}</p>
            
            <h3>Key Requirements Identified:</h3>
            <ul>
                {''.join([f'<li>{req}</li>' for req in analysis['key_requirements']])}
            </ul>
            
            {similar_solutions_html}
            
            <h3>Recommendations:</h3>
            <p>{analysis['recommendations']}</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This report was automatically generated by the RSD Analysis Agent.
            </p>
        </body>
        </html>
        """
        
        return html_report
