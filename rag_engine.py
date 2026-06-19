import os
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer
from config import VECTOR_DB_PATH, SIMILARITY_THRESHOLD
from document_processor import DocumentProcessor

class RAGEngine:
    def __init__(self):
        self.vector_db_path = VECTOR_DB_PATH
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        
        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        self.collection = None
    
    def index_documents(self, force_reindex=False):
        """Load and index all project documents"""
        collection_name = "project_solutions"
        
        # Remove existing collection if force reindex
        if force_reindex:
            try:
                self.client.delete_collection(name=collection_name)
                print(f"Deleted existing collection: {collection_name}")
            except:
                pass
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load and process documents
        processor = DocumentProcessor()
        documents = processor.load_all_documents()
        
        if not documents:
            print("No documents found to index")
            return
        
        chunks = processor.chunk_documents(documents)
        
        if not chunks:
            print("No chunks created")
            return
        
        # Embed and add to collection
        ids = []
        embeddings = []
        documents_list = []
        metadatas = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = f"chunk_{idx}"
            ids.append(chunk_id)
            documents_list.append(chunk['content'])
            embeddings.append(self.embedder.encode(chunk['content']).tolist())
            metadatas.append({
                'source': chunk['source'],
                'filename': chunk['filename']
            })
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents_list,
            metadatas=metadatas
        )
        
        print(f"Indexed {len(chunks)} chunks in vector database")
    
    def search_similar_solutions(self, query: str, top_k: int = 5) -> List[dict]:
        """Search for similar project solutions"""
        if self.collection is None:
            print("Collection not initialized. Call index_documents() first.")
            return []
        
        try:
            # Embed query
            query_embedding = self.embedder.encode(query).tolist()
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=None
            )
            
            # Format results
            similar_solutions = []
            
            if results['ids'] and len(results['ids']) > 0:
                for i, (doc_id, distance, document, metadata) in enumerate(zip(
                    results['ids'][0],
                    results['distances'][0],
                    results['documents'][0],
                    results['metadatas'][0]
                )):
                    # Convert distance to similarity score (cosine distance to similarity)
                    similarity = 1 - distance
                    
                    if similarity >= SIMILARITY_THRESHOLD:
                        similar_solutions.append({
                            'rank': i + 1,
                            'similarity_score': round(similarity, 3),
                            'source_file': metadata.get('source', ''),
                            'filename': metadata.get('filename', ''),
                            'preview': document[:500] + '...' if len(document) > 500 else document
                        })
            
            return similar_solutions
        
        except Exception as e:
            print(f"Error searching similar solutions: {e}")
            return []
    
    def get_collection_info(self) -> dict:
        """Get information about indexed collection"""
        if self.collection is None:
            return {'status': 'not_initialized'}
        
        try:
            count = self.collection.count()
            return {
                'status': 'ready',
                'total_chunks': count,
                'embedding_model': 'all-MiniLM-L6-v2'
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {'status': 'error', 'error': str(e)}
